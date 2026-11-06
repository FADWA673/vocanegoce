from django.contrib import admin
from .models import Produit, Client, Commande, DetailCommande

@admin.register(Produit)
class ProduitAdmin(admin.ModelAdmin):
    list_display = ['nom', 'categorie', 'prix', 'stock', 'actif', 'date_creation']
    list_filter = ['categorie', 'actif', 'date_creation']
    search_fields = ['nom', 'description']
    list_editable = ['prix', 'stock', 'actif']
    ordering = ['-date_creation']

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['raison_sociale', 'contact', 'email', 'ville', 'statut', 'date_creation']
    list_filter = ['statut', 'ville', 'date_creation']
    search_fields = ['raison_sociale', 'contact', 'email']
    list_editable = ['statut']
    ordering = ['raison_sociale']

class DetailCommandeInline(admin.TabularInline):
    model = DetailCommande
    extra = 1

@admin.register(Commande)
class CommandeAdmin(admin.ModelAdmin):
    list_display = ['numero_commande', 'client', 'date_commande', 'statut', 'total', 'date_creation']
    list_filter = ['statut', 'date_commande', 'date_creation']
    search_fields = ['numero_commande', 'client__raison_sociale']
    list_editable = ['statut']
    ordering = ['-date_creation']
    inlines = [DetailCommandeInline]


