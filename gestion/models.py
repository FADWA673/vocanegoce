from django.db import models 
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator  # ← AJOUT MANQUANT
import uuid


class Produit(models.Model):
    CATEGORIES = [
        ('chimique', 'Produit Chimique'),
        ('equipement', 'Équipement'),
        ('consommable', 'Consommable'),
        ('autre', 'Autre'),
    ]
    
    nom = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    categorie = models.CharField(max_length=50, choices=CATEGORIES, default='autre')
    prix = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    unite = models.CharField(max_length=20, default='unité')
    formule_chimique = models.CharField(max_length=100, blank=True)
    image = models.ImageField(upload_to='produits/', blank=True, null=True)
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    seuil_minimum = models.IntegerField(
        default=10,
        help_text="Seuil minimum avant alerte stock faible"
    )
    
    @property
    def stock_faible(self):
        return self.stock < self.seuil_minimum
    
    class Meta:
        ordering = ['nom']
        verbose_name = 'Produit'
        verbose_name_plural = 'Produits'
    
    def __str__(self):
        return self.nom


class Client(models.Model):
    STATUTS = [
        ('actif', 'Actif'),
        ('inactif', 'Inactif'),
        ('suspendu', 'Suspendu'),
    ]
    
    raison_sociale = models.CharField(max_length=200)
    contact = models.CharField(max_length=100)
    email = models.EmailField()
    telephone = models.CharField(max_length=20, blank=True)
    adresse = models.TextField(blank=True)
    ville = models.CharField(max_length=100)
    code_postal = models.CharField(max_length=10, blank=True)
    siret = models.CharField(max_length=14, blank=True)
    statut = models.CharField(max_length=20, choices=STATUTS, default='actif')
    notes = models.TextField(blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['raison_sociale']
        verbose_name = 'Client'
        verbose_name_plural = 'Clients'
    
    def __str__(self):
        return self.raison_sociale


class DetailCommande(models.Model):
    """Détail d'une ligne de commande"""
    commande = models.ForeignKey(
        'Commande', 
        on_delete=models.CASCADE, 
        related_name='details',
        verbose_name="Commande"
    )
    produit = models.ForeignKey(
        'Produit', 
        on_delete=models.CASCADE, 
        verbose_name="Produit"
    )
    quantite = models.PositiveIntegerField(
        verbose_name="Quantité",
        validators=[MinValueValidator(1)]  # ← Maintenant ça marche
    )
    prix_unitaire = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name="Prix unitaire"
    )
    sous_total = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name="Sous-total",
        editable=False  # Calculé automatiquement
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Détail de commande"
        verbose_name_plural = "Détails de commande"
        unique_together = ['commande', 'produit']  # Évite les doublons
    
    def save(self, *args, **kwargs):
        """Calcul automatique du sous-total"""
        self.sous_total = self.quantite * self.prix_unitaire
        super().save(*args, **kwargs)
        
        # Mettre à jour le total de la commande
        if self.commande_id:  # S'assurer que la commande existe
            self.commande.calculer_total()
    
    def __str__(self):
        return f"{self.commande.numero_commande} - {self.produit.nom} x{self.quantite}"


class Commande(models.Model):
    STATUTS = [
        ('en_attente', 'En attente'),
        ('confirmee', 'Confirmée'),
        ('en_preparation', 'En préparation'),
        ('expediee', 'Expédiée'),
        ('livree', 'Livrée'),
        ('annulee', 'Annulée'),
    ]
    
    numero_commande = models.CharField(
        max_length=20, 
        unique=True, 
        editable=False,
        verbose_name="Numéro de commande"
    )
    client = models.ForeignKey(
        'Client', 
        on_delete=models.CASCADE,
        verbose_name="Client"
    )
    date_commande = models.DateField(
        default=timezone.now,
        verbose_name="Date de commande"
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(
        max_length=20, 
        choices=STATUTS, 
        default='en_attente',
        verbose_name="Statut"
    )
    notes = models.TextField(
        blank=True, 
        null=True,
        verbose_name="Notes"
    )
    total = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        verbose_name="Total"
    )
    
    class Meta:
        verbose_name = "Commande"
        verbose_name_plural = "Commandes"
        ordering = ['-date_creation']
    
    def save(self, *args, **kwargs):
        if not self.numero_commande:
            self.numero_commande = self.generer_numero_commande()
        super().save(*args, **kwargs)
    
    def generer_numero_commande(self):
        """Générer un numéro de commande unique"""
        from datetime import datetime
        now = datetime.now()
        prefix = f"CMD-{now.strftime('%Y%m%d')}"
        
        # Compter les commandes du jour
        count = Commande.objects.filter(
            numero_commande__startswith=prefix
        ).count() + 1
        
        return f"{prefix}-{count:04d}"
    
    def calculer_total(self):
        """Recalculer le total de la commande"""
        total = self.details.aggregate(
            total=models.Sum('sous_total')
        )['total'] or 0
        
        if self.total != total:
            self.total = total
            # Utiliser update pour éviter les boucles infinies
            Commande.objects.filter(pk=self.pk).update(total=total)
    
    def __str__(self):
        return f"{self.numero_commande} - {self.client.raison_sociale}"


class SearchLog(models.Model):
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE)
    terme_recherche = models.CharField(max_length=200)
    type_recherche = models.CharField(max_length=50)
    resultats_count = models.IntegerField(default=0)
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date_creation']
        verbose_name = 'Log de recherche'
        verbose_name_plural = 'Logs de recherche'
        
    def __str__(self):
        return f"{self.utilisateur.username} - {self.terme_recherche}"
    

