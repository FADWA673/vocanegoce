from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count, Case, When, IntegerField, Value
from datetime import date, datetime
import json
import re
from .models import Produit, Client, Commande, DetailCommande, SearchLog
from .forms import ProduitForm, ClientForm, CommandeForm
from django.utils import timezone
from django.db import models

def register(request):
    """Vue d'inscription pour créer un nouveau compte"""
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Compte créé avec succès pour {username}! Bienvenue dans VocaNégoce.')
            login(request, user)
            return redirect('dashboard')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = UserCreationForm()
        
    return render(request, 'registration/register.html', {'form': form})

def custom_login(request):
    """Vue de connexion personnalisée"""
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
                
        if user is not None:
            login(request, user)
            messages.success(request, f'Bienvenue {user.username}! Connexion réussie.')
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Nom d\'utilisateur ou mot de passe incorrect. Veuillez réessayer.')
        
    return render(request, 'registration/login.html')



@login_required
def dashboard(request):
    total_produits = Produit.objects.count()
    total_clients = Client.objects.count()
    total_commandes = Commande.objects.count()

    dernieres_commandes = Commande.objects.all().order_by('-date_creation')[:5]

    # ✅ Utiliser seuil_minimum au lieu de stock < 10
    produits_stock_faible = Produit.objects.filter(stock__lt=models.F('seuil_minimum'))

    stats = {
        'total_produits': total_produits,
        'total_clients': total_clients,
        'total_commandes': total_commandes,
        'produits_stock_faible': produits_stock_faible.count(),
        'commandes_en_attente': Commande.objects.filter(statut='en_attente').count(),
        'clients_actifs': Client.objects.filter(statut='actif').count(),
        'ca_total': Commande.objects.filter(statut='livree').aggregate(total=Sum('total'))['total'] or 0,
    }

    context = {
        'stats': stats,
        'dernieres_commandes': dernieres_commandes,
        'produits_stock_faible': produits_stock_faible,
    }
    return render(request, 'dashboard.html', context)


# ============ VUES PRODUITS AVEC RECHERCHE INTELLIGENTE CORRIGÉE ============
@login_required
def produit_list(request):
    """Liste des produits avec recherche intelligente corrigée"""
    produits = Produit.objects.all()
    search = request.GET.get('search')
        
    if search:
        # Recherche intelligente corrigée sans union()
        produits = smart_search_produits_fixed(search, produits)
                
        # Log de recherche
        SearchLog.objects.create(
            utilisateur=request.user,
            terme_recherche=search,
            type_recherche='produit',
            resultats_count=produits.count()
        )
        
    categorie = request.GET.get('categorie')
    if categorie:
        produits = produits.filter(categorie=categorie)
        
    stock_faible = request.GET.get('stock_faible')
    if stock_faible:
        produits = produits.filter(stock__lt=10)
        
    # Appliquer l'ordre après tous les filtres
    produits = produits.order_by('-date_creation')
        
    paginator = Paginator(produits, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
        
    context = {
        'page_obj': page_obj,
        'search': search,
        'categorie': categorie,
        'categories': Produit.CATEGORIES,
    }
        
    return render(request, 'gestion/produit_list.html', context)

def smart_search_produits_fixed(search_term, queryset):
    """Recherche sémantique intelligente corrigée pour les produits"""
    # Utiliser des annotations pour créer un score de pertinence
    search_query = queryset.annotate(
        # Score de pertinence basé sur le type de correspondance
        relevance_score=Case(
            # Correspondance exacte du nom (score le plus élevé)
            When(nom__iexact=search_term, then=Value(100)),
            # Correspondance exacte de la formule chimique
            When(formule_chimique__iexact=search_term, then=Value(95)),
            # Correspondance partielle du nom (début)
            When(nom__istartswith=search_term, then=Value(90)),
            # Correspondance partielle du nom (contient)
            When(nom__icontains=search_term, then=Value(80)),
            # Correspondance dans la description
            When(description__icontains=search_term, then=Value(70)),
            # Correspondance dans la catégorie
            When(categorie__icontains=search_term, then=Value(60)),
            # Correspondance partielle dans la formule chimique
            When(formule_chimique__icontains=search_term, then=Value(50)),
            default=Value(0),
            output_field=IntegerField()
        )
    ).filter(
        # Filtrer pour ne garder que les résultats pertinents
        Q(nom__icontains=search_term) |
        Q(description__icontains=search_term) |
        Q(categorie__icontains=search_term) |
        Q(formule_chimique__icontains=search_term)
    )
    
    # Ajouter la recherche floue pour les synonymes
    fuzzy_results = fuzzy_search_produits_fixed(search_term, queryset)
    
    # Combiner les résultats en utilisant distinct() au lieu de union()
    combined_ids = list(search_query.values_list('id', flat=True)) + list(fuzzy_results.values_list('id', flat=True))
    
    # Retourner les résultats ordonnés par pertinence
    return queryset.filter(id__in=combined_ids).annotate(
        relevance_score=Case(
            When(nom__iexact=search_term, then=Value(100)),
            When(formule_chimique__iexact=search_term, then=Value(95)),
            When(nom__istartswith=search_term, then=Value(90)),
            When(nom__icontains=search_term, then=Value(80)),
            When(description__icontains=search_term, then=Value(70)),
            When(categorie__icontains=search_term, then=Value(60)),
            When(formule_chimique__icontains=search_term, then=Value(50)),
            default=Value(30),
            output_field=IntegerField()
        )
    ).order_by('-relevance_score', 'nom')

def fuzzy_search_produits_fixed(search_term, queryset):
    """Recherche floue corrigée avec gestion des fautes de frappe et synonymes"""
    synonymes = {
        'acide': ['acid', 'acidique'],
        'base': ['basique', 'alcalin'],
        'solvant': ['solvent', 'dissolvant'],
        'eau': ['h2o', 'water'],
        'alcool': ['ethanol', 'alcohol'],
    }
        
    # Recherche avec synonymes
    terms_to_search = [search_term.lower()]
    for key, values in synonymes.items():
        if search_term.lower() in values or search_term.lower() == key:
            terms_to_search.extend([key] + values)
        
    q_objects = Q()
    for term in terms_to_search:
        q_objects |= (
            Q(nom__icontains=term) |
            Q(description__icontains=term) |
            Q(formule_chimique__icontains=term)
        )
        
    return queryset.filter(q_objects)

@login_required
def produit_create(request):
    if request.method == 'POST':
        form = ProduitForm(request.POST, request.FILES)
        if form.is_valid():
            produit = form.save()
            messages.success(request, f'Produit "{produit.nom}" créé avec succès!')
            return redirect('produit_list')
        else:
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
    else:
        form = ProduitForm()
        
    return render(request, 'gestion/produit_create.html', {'form': form})

@login_required
def produit_detail(request, pk):
    """Détail d'un produit"""
    produit = get_object_or_404(Produit, pk=pk)
    
    # Commandes contenant ce produit (utiliser DetailCommande au lieu de LigneCommande)
    details_commande = DetailCommande.objects.filter(produit=produit).select_related('commande__client').order_by('-commande__date_creation')
    
    context = {
        'produit': produit,
        'details_commande': details_commande,
    }
    return render(request, 'gestion/produit_detail.html', context)

@login_required
def produit_update(request, pk):
    """Modifier un produit"""
    produit = get_object_or_404(Produit, pk=pk)
    if request.method == 'POST':
        form = ProduitForm(request.POST, request.FILES, instance=produit)
        if form.is_valid():
            form.save()
            messages.success(request, f'Produit "{produit.nom}" modifié avec succès!')
            return redirect('produit_list')
    else:
        form = ProduitForm(instance=produit)
        
    return render(request, 'gestion/produit_update.html', {
        'form': form,
        'produit': produit
    })

@login_required
def produit_delete(request, pk):
    """Supprimer un produit"""
    produit = get_object_or_404(Produit, pk=pk)
    if request.method == 'POST':
        nom = produit.nom
        produit.delete()
        messages.success(request, f'Produit "{nom}" supprimé avec succès!')
        return redirect('produit_list')
        
    return render(request, 'gestion/produit_confirm_delete.html', {'produit': produit})

# ============ VUES CLIENTS AVEC RECHERCHE INTELLIGENTE ============
@login_required
def client_list(request):
    """Liste des clients avec recherche intelligente"""
    clients = Client.objects.all()
    search = request.GET.get('search')
        
    if search:
        clients = smart_search_clients(search, clients)
                
        # Log de recherche
        SearchLog.objects.create(
            utilisateur=request.user,
            terme_recherche=search,
            type_recherche='client',
            resultats_count=clients.count()
        )
        
    statut = request.GET.get('statut')
    if statut:
        clients = clients.filter(statut=statut)
        
    paginator = Paginator(clients, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
        
    context = {
        'page_obj': page_obj,
        'search': search,
        'statut': statut,
    }
        
    return render(request, 'gestion/client_list.html', context)

def smart_search_clients(search_term, queryset):
    """Recherche sémantique intelligente pour les clients"""
    return queryset.filter(
        Q(raison_sociale__icontains=search_term) |
        Q(contact__icontains=search_term) |
        Q(email__icontains=search_term) |
        Q(ville__icontains=search_term) |
        Q(siret__icontains=search_term)
    )

@login_required
def client_create(request):
    """Créer un nouveau client"""
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save()
            messages.success(request, f'Client "{client.raison_sociale}" créé avec succès!')
            return redirect('client_list')
    else:
        form = ClientForm()
        
    return render(request, 'gestion/client_form.html', {
        'form': form,
        'title': 'Nouveau Client'
    })

@login_required
def client_detail(request, pk):
    """Détail d'un client"""
    client = get_object_or_404(Client, pk=pk)
    commandes = client.commande_set.all().order_by('-date_creation')
        
    # Calcul des statistiques
    total_commandes = commandes.count()
    ca_total = commandes.filter(statut='livree').aggregate(total=Sum('total'))['total'] or 0
    ca_moyen = ca_total / total_commandes if total_commandes > 0 else 0
        
    context = {
        'client': client,
        'commandes': commandes,
        'total_commandes': total_commandes,
        'ca_total': ca_total,
        'ca_moyen': ca_moyen,
    }
        
    return render(request, 'gestion/client_detail.html', context)

@login_required
def client_update(request, pk):
    """Modifier un client"""
    client = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, f'Client "{client.raison_sociale}" modifié avec succès!')
            return redirect('client_list')
    else:
        form = ClientForm(instance=client)
        
    return render(request, 'gestion/client_form.html', {
        'form': form,
        'title': 'Modifier Client',
        'client': client
    })

@login_required
def client_delete(request, pk):
    """Supprimer un client"""
    client = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        nom = client.raison_sociale
        client.delete()
        messages.success(request, f'Client "{nom}" supprimé avec succès!')
        return redirect('client_list')
        
    return render(request, 'gestion/client_confirm_delete.html', {'client': client})

# ============ VUES COMMANDES ============
@login_required
def commande_list(request):
    """Liste des commandes avec recherche intelligente"""
    commandes = Commande.objects.select_related('client').all()
    search = request.GET.get('search')
        
    if search:
        commandes = commandes.filter(
            Q(numero_commande__icontains=search) |
            Q(client__raison_sociale__icontains=search)
        )
        
    statut = request.GET.get('statut')
    if statut:
        commandes = commandes.filter(statut=statut)
        
    paginator = Paginator(commandes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
        
    context = {
        'page_obj': page_obj,
        'search': search,
        'statut': statut,
        'statuts': Commande.STATUTS,
    }
        
    return render(request, 'gestion/commande_list.html', context)

from django.shortcuts import render, redirect, get_object_or_404
from django.utils.timezone import now
from .models import Commande, Client, Produit, DetailCommande

@login_required
def commande_create(request):
    """Créer une nouvelle commande avec calcul automatique des prix et gestion des stocks"""
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Validation des données requises
                client_id = request.POST.get('client')
                date_commande = request.POST.get('date_commande')
                statut = request.POST.get('statut', 'en_attente')
                notes = request.POST.get('notes', '')
                
                if not client_id:
                    raise ValueError("Veuillez sélectionner un client")
                if not date_commande:
                    raise ValueError("Veuillez saisir une date de commande")
                
                # Vérifier que le client existe
                try:
                    client = Client.objects.get(id=client_id)
                except Client.DoesNotExist:
                    raise ValueError("Client sélectionné invalide")
                
                # ✅ ÉTAPE 1: Créer d'abord la commande et la sauvegarder
                commande = Commande(
                    client=client,
                    date_commande=date_commande,
                    statut=statut,
                    notes=notes,
                    total=0  # On mettra à jour après
                )
                commande.save()  # ✅ CRUCIAL: Sauvegarder pour obtenir l'ID primaire
                
                print(f"✅ Commande créée avec ID: {commande.pk}")
                
                # ✅ ÉTAPE 2: Traiter les lignes de produits
                total = 0
                produits_traites = []
                lignes_traitees = 0
                
                # Collecter tous les produits du formulaire
                produits_data = []
                index = 0
                
                while True:
                    produit_key = f'produit_{index}'
                    quantite_key = f'quantite_{index}'
                    
                    produit_id = request.POST.get(produit_key)
                    quantite_str = request.POST.get(quantite_key)
                    
                    if not produit_id:
                        index += 1
                        if index > 50:  # Limite de sécurité
                            break
                        continue
                    
                    # Validation de la quantité
                    try:
                        quantite = int(quantite_str) if quantite_str else 0
                    except (ValueError, TypeError):
                        quantite = 0
                    
                    if quantite <= 0:
                        messages.warning(request, f"Quantité invalide pour la ligne {index + 1}, ligne ignorée")
                        index += 1
                        continue
                    
                    produits_data.append({
                        'produit_id': produit_id,
                        'quantite': quantite,
                        'ligne': index + 1
                    })
                    
                    index += 1
                
                # Vérifier qu'on a au moins un produit
                if not produits_data:
                    raise ValueError("Veuillez ajouter au moins un produit à la commande")
                
                # ✅ ÉTAPE 3: Traiter chaque produit
                for data in produits_data:
                    try:
                        produit = Produit.objects.get(id=data['produit_id'], actif=True)
                    except Produit.DoesNotExist:
                        messages.warning(request, f"Produit invalide à la ligne {data['ligne']}, ligne ignorée")
                        continue
                    
                    quantite = data['quantite']
                    
                    # Vérifier le stock disponible
                    if produit.stock < quantite:
                        raise ValueError(
                            f"Stock insuffisant pour {produit.nom}. "
                            f"Stock disponible: {produit.stock}, quantité demandée: {quantite}"
                        )
                    
                    # Utiliser le prix actuel du produit
                    prix_unitaire = produit.prix
                    sous_total = quantite * prix_unitaire
                    
                    # ✅ Maintenant on peut créer le DetailCommande car commande.pk existe
                    detail = DetailCommande.objects.create(
                        commande=commande,  # commande a maintenant un pk
                        produit=produit,
                        quantite=quantite,
                        prix_unitaire=prix_unitaire,
                        sous_total=sous_total
                    )
                    
                    print(f"✅ Détail créé: {detail.pk} - {produit.nom} x{quantite}")
                    
                    # Diminuer le stock seulement si nécessaire
                    if statut not in ['en_attente']:
                        produit.stock -= quantite
                        produit.save()
                        print(f"✅ Stock mis à jour pour {produit.nom}: {produit.stock}")
                    
                    total += sous_total
                    lignes_traitees += 1
                    produits_traites.append(f"{produit.nom} (x{quantite})")
                
                # ✅ ÉTAPE 4: Mettre à jour le total de la commande
                commande.total = total
                commande.save()
                
                print(f"✅ Commande finalisée - Total: {total}")
                
                if lignes_traitees > 0:
                    messages.success(
                        request,
                        f'Commande {commande.numero_commande} créée avec succès! '
                        f'Produits: {", ".join(produits_traites)}. Total: {total:.2f} DH'
                    )
                    return redirect('commande_list')
                else:
                    # Si aucune ligne traitée, supprimer la commande
                    commande.delete()
                    raise ValueError("Aucun produit valide n'a pu être ajouté à la commande")

        except ValueError as e:
            messages.error(request, str(e))
            print(f"❌ Erreur ValueError: {str(e)}")
        except Exception as e:
            messages.error(request, f'Erreur lors de la création: {str(e)}')
            print(f"❌ Erreur Exception: {str(e)}")
            import traceback
            print(traceback.format_exc())

    # GET request - afficher le formulaire
    clients = Client.objects.filter(statut='actif').order_by('raison_sociale')
    produits = Produit.objects.filter(stock__gt=0, actif=True).order_by('nom')

    context = {
        'title': 'Nouvelle Commande',
        'clients': clients,
        'produits': produits,
        'today': date.today().isoformat(),
        'commande': None,
    }

    return render(request, 'gestion/commande_form.html', context)


@login_required
def commande_update(request, pk):
    """Modifier une commande existante"""
    commande = get_object_or_404(Commande, pk=pk)
    clients = Client.objects.filter(statut='actif').order_by('raison_sociale')
    produits = Produit.objects.filter(actif=True).order_by('nom')

    if request.method == "POST":
        try:
            with transaction.atomic():
                # Validation des données
                client_id = request.POST.get("client")
                date_commande = request.POST.get("date_commande")
                statut = request.POST.get("statut")
                notes = request.POST.get("notes", "")

                if not client_id or not date_commande or not statut:
                    raise ValueError("Tous les champs obligatoires doivent être remplis")

                # Restaurer les stocks des anciens détails si nécessaire
                anciens_details = list(commande.details.all())
                for detail in anciens_details:
                    if commande.statut not in ['en_attente']:
                        detail.produit.stock += detail.quantite
                        detail.produit.save()

                # Supprimer les anciens détails
                commande.details.all().delete()

                # Mettre à jour les informations de la commande
                try:
                    client = Client.objects.get(id=client_id)
                except Client.DoesNotExist:
                    raise ValueError("Client sélectionné invalide")

                commande.client = client
                commande.date_commande = date_commande
                commande.statut = statut
                commande.notes = notes
                commande.save()

                # Traiter les nouveaux détails
                total_commande = 0
                lignes_traitees = 0
                
                index = 0
                while True:
                    produit_id = request.POST.get(f"produit_{index}")
                    quantite_str = request.POST.get(f"quantite_{index}")
                    
                    if not produit_id:
                        index += 1
                        if index > 50:
                            break
                        continue
                    
                    try:
                        quantite = int(quantite_str) if quantite_str else 0
                    except (ValueError, TypeError):
                        quantite = 0
                    
                    if quantite <= 0:
                        index += 1
                        continue

                    try:
                        produit = Produit.objects.get(id=produit_id, actif=True)
                    except Produit.DoesNotExist:
                        index += 1
                        continue

                    # Vérifier le stock
                    if produit.stock < quantite:
                        raise ValueError(f"Stock insuffisant pour {produit.nom}")

                    prix_unitaire = produit.prix
                    sous_total = prix_unitaire * quantite

                    # Créer le nouveau détail
                    DetailCommande.objects.create(
                        commande=commande,
                        produit=produit,
                        quantite=quantite,
                        prix_unitaire=prix_unitaire,
                        sous_total=sous_total
                    )

                    # Diminuer le stock si nécessaire
                    if statut not in ['en_attente']:
                        produit.stock -= quantite
                        produit.save()

                    total_commande += sous_total
                    lignes_traitees += 1
                    index += 1

                if lignes_traitees == 0:
                    raise ValueError("Au moins un produit doit être ajouté")

                # Mettre à jour le total
                commande.total = total_commande
                commande.save()

                messages.success(request, f"Commande {commande.numero_commande} modifiée avec succès!")
                return redirect("commande_list")

        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Erreur lors de la modification: {str(e)}')

    context = {
        "title": "Modifier commande",
        "commande": commande,
        "clients": clients,
        "produits": produits,
        "today": date.today().isoformat()
    }
    return render(request, "gestion/commande_form.html", context)


@login_required
def commande_detail(request, pk):
    """Détail d'une commande"""
    commande = get_object_or_404(Commande, pk=pk)
    # Utiliser DetailCommande au lieu de LigneCommande
    details = commande.details.select_related('produit').all()
        
    context = {
        'commande': commande,
        'details': details,
    }
        
    return render(request, 'gestion/commande_detail.html', context)


@login_required
def commande_delete(request, pk):
    """Supprimer une commande"""
    commande = get_object_or_404(Commande, pk=pk)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Restaurer les stocks avant suppression
                for detail in commande.details.all():
                    produit = detail.produit
                    # Restaurer le stock seulement si la commande n'était pas en attente
                    if commande.statut not in ['en_attente']:
                        produit.stock += detail.quantite
                        produit.save()
                        print(f"✅ Stock restauré pour {produit.nom}: +{detail.quantite} = {produit.stock}")
                
                numero = commande.numero_commande
                client_pk = commande.client.pk  # Sauvegarder l'ID du client pour la redirection
                commande.delete()
                
                messages.success(request, f'Commande {numero} supprimée avec succès!')
                return redirect('commande_list')
                
        except Exception as e:
            messages.error(request, f'Erreur lors de la suppression: {str(e)}')
            return redirect('commande_list')
    
    # Passer à la fois la commande ET le client dans le contexte
    context = {
        'commande': commande,
        'client': commande.client,  # ✅ AJOUT CRUCIAL
    }
    
    return render(request, 'gestion/commande_confirm_delete.html', context)

# ============ NOUVELLES API RECHERCHE INTELLIGENTE ============
@login_required
def search_api(request):
    """API de recherche intelligente unifiée"""
    query = request.GET.get('q', '')
    search_type = request.GET.get('type', 'all')
    limit = int(request.GET.get('limit', 10))
        
    if not query:
        return JsonResponse({'results': []})
        
    results = []
        
    if search_type in ['all', 'produits']:
        produits = smart_search_produits_fixed(query, Produit.objects.filter(actif=True))[:limit]
        for produit in produits:
            results.append({
                'type': 'produit',
                'id': produit.id,
                'title': produit.nom,
                'subtitle': f"{produit.get_categorie_display()} - {produit.prix} DH",
                'description': produit.description[:100] if produit.description else '',
                'url': f'/produits/{produit.id}/',
                'stock': produit.stock,
                'prix': float(produit.prix)
            })
        
    if search_type in ['all', 'clients']:
        clients = smart_search_clients(query, Client.objects.filter(statut='actif'))[:limit]
        for client in clients:
            results.append({
                'type': 'client',
                'id': client.id,
                'title': client.raison_sociale,
                'subtitle': f"{client.contact} - {client.ville}",
                'description': client.email,
                'url': f'/clients/{client.id}/',
                'statut': client.statut
            })
        
    if search_type in ['all', 'commandes']:
        commandes = Commande.objects.filter(
            Q(numero_commande__icontains=query) |
            Q(client__raison_sociale__icontains=query)
        )[:limit]
        for commande in commandes:
            results.append({
                'type': 'commande',
                'id': commande.id,
                'title': commande.numero_commande,
                'subtitle': f"{commande.client.raison_sociale} - {commande.get_statut_display()}",
                'description': f"Total: {commande.total} DH",
                'url': f'/commandes/{commande.id}/',
                'statut': commande.statut,
                'total': float(commande.total)
            })
        
    # Log de recherche
    SearchLog.objects.create(
        utilisateur=request.user,
        terme_recherche=query,
        type_recherche=search_type,
        resultats_count=len(results)
    )
        
    return JsonResponse({
        'results': results,
        'query': query,
        'total': len(results)
    })

@login_required
def autocomplete_api(request):
    """API d'auto-complétion"""
    query = request.GET.get('q', '')
    search_type = request.GET.get('type', 'all')
        
    if len(query) < 2:
        return JsonResponse({'suggestions': []})
        
    suggestions = []
        
    if search_type in ['all', 'produits']:
        produits = Produit.objects.filter(
            Q(nom__icontains=query) | Q(formule_chimique__icontains=query),
            actif=True
        )[:5]
        for produit in produits:
            suggestions.append({
                'text': produit.nom,
                'type': 'produit',
                'category': 'Produits'
            })
        
    if search_type in ['all', 'clients']:
        clients = Client.objects.filter(
            Q(raison_sociale__icontains=query) | Q(contact__icontains=query),
            statut='actif'
        )[:5]
        for client in clients:
            suggestions.append({
                'text': client.raison_sociale,
                'type': 'client',
                'category': 'Clients'
            })
        
    return JsonResponse({'suggestions': suggestions})

# ============ AGENT AI ELEVENLABS (CONSERVÉ) ============
def elevenlabs_assistant(request):
    """Vue pour l'assistant ElevenLabs dédié"""
    # Vous pouvez ajouter ici des données contextuelles pour l'assistant
    context = {
        'user_stats': {
            'total_produits': Produit.objects.count(),
            'total_clients': Client.objects.count(),
            'total_commandes': Commande.objects.count(),
            'ca_total': Commande.objects.filter(statut='livree').aggregate(
                total=Sum('total'))['total'] or 0,
        },
        'recent_activity': {
            'derniers_produits': Produit.objects.filter(actif=True).order_by('-date_creation')[:5],
            'derniers_clients': Client.objects.filter(statut='actif').order_by('-date_creation')[:5],
            'dernieres_commandes': Commande.objects.order_by('-date_creation')[:5],
        }
    }
    
    return render(request, 'gestion/elevenlabs_assistant.html', context)

# Ajoutez aussi cette API pour fournir des données contextuelles à ElevenLabs
@login_required
def elevenlabs_context_api(request):
    """API pour fournir le contexte de l'application à ElevenLabs"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    try:
        # Statistiques générales
        stats = {
            'total_produits': Produit.objects.count(),
            'total_clients': Client.objects.count(),
            'total_commandes': Commande.objects.count(),
            'ca_total': float(Commande.objects.filter(statut='livree').aggregate(
                total=Sum('total'))['total'] or 0),
        }
        
        # Activité récente
        recent_activity = {
            'derniers_produits': [
                {
                    'nom': p.nom,
                    'stock': p.stock,
                    'prix': float(p.prix),
                    'date_creation': p.date_creation.isoformat()
                } for p in Produit.objects.filter(actif=True).order_by('-date_creation')[:5]
            ],
            'derniers_clients': [
                {
                    'raison_sociale': c.raison_sociale,
                    'contact': c.contact,
                    'ville': c.ville,
                    'date_creation': c.date_creation.isoformat()
                } for c in Client.objects.filter(statut='actif').order_by('-date_creation')[:5]
            ],
            'dernieres_commandes': [
                {
                    'numero': c.numero_commande,
                    'client': c.client.raison_sociale,
                    'total': float(c.total),
                    'statut': c.statut,
                    'date_creation': c.date_creation.isoformat()
                } for c in Commande.objects.order_by('-date_creation')[:5]
            ]
        }
        
        return JsonResponse({
            'success': True,
            'stats': stats,
            'recent_activity': recent_activity,
            'user': {
                'username': request.user.username,
                'email': request.user.email
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors de la récupération du contexte: {str(e)}'
        }, status=500)

import os
from django.conf import settings
from django.template.loader import get_template
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from xhtml2pdf import pisa
from django.contrib.staticfiles import finders
from .models import Commande

def link_callback(uri, rel):
    """
    Convertit les URI (static, media) en chemins absolus
    pour que xhtml2pdf puisse charger les fichiers (ex: logo).
    """
    # 🔹 Cherche dans les fichiers statiques collectés
    result = finders.find(uri.replace(settings.STATIC_URL, ""))
    if result:
        if not isinstance(result, (list, tuple)):
            result = [result]
        path = result[0]
    else:
        # 🔹 Vérifie si le fichier est dans media
        sUrl = settings.STATIC_URL   # /static/
        sRoot = settings.STATIC_ROOT # chemin absolu
        mUrl = settings.MEDIA_URL    # /media/
        mRoot = settings.MEDIA_ROOT  # chemin absolu

        if uri.startswith(mUrl):
            path = os.path.join(mRoot, uri.replace(mUrl, ""))
        elif uri.startswith(sUrl):
            path = os.path.join(sRoot, uri.replace(sUrl, ""))
        else:
            return uri  # URL absolue (http://...) → laisser tel quel

    if not os.path.isfile(path):
        raise Exception(f"Fichier introuvable : {path}")
    return path


@login_required
def generer_facture_pdf(request, pk):
    """
    Génération du PDF de la facture avec logo
    """
    commande = get_object_or_404(Commande, pk=pk)
    details = commande.details.all()

    template_path = 'gestion/facture_template.html'
    context = {'commande': commande, 'details': details, 'request': request}
    template = get_template(template_path)
    html = template.render(context)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="facture_{commande.numero_commande}.pdf"'

    # 🔹 Ici on utilise link_callback
    pisa_status = pisa.CreatePDF(
        html, dest=response, link_callback=link_callback
    )

    if pisa_status.err:
        return HttpResponse('Erreur lors de la génération du PDF', status=500)
    return response



# ============ VUE CHIFFRE D’AFFAIRE ============

@login_required
def chiffre_affaire(request):
    """Vue pour afficher le chiffre d’affaire par mois et par année"""

    # Chiffre d’affaire total sur toutes les commandes livrées
    ca_total = Commande.objects.filter(statut="livree").aggregate(
        total=Sum("total")
    )["total"] or 0

    # CA par mois (année en cours)
    current_year = timezone.now().year
    ca_mensuel = (
        Commande.objects.filter(statut="livree", date_commande__year=current_year)
        .annotate(mois=models.functions.ExtractMonth("date_commande"))
        .values("mois")
        .annotate(total=Sum("total"))
        .order_by("mois")
    )

    # CA par année
    ca_annuel = (
        Commande.objects.filter(statut="livree")
        .annotate(annee=models.functions.ExtractYear("date_commande"))
        .values("annee")
        .annotate(total=Sum("total"))
        .order_by("annee")
    )

    context = {
        "ca_total": ca_total,
        "ca_mensuel": ca_mensuel,
        "ca_annuel": ca_annuel,
        "current_year": current_year,
    }
    return render(request, "gestion/chiffre_affaire.html", context)


