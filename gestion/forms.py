from django import forms
from .models import Produit, Client, Commande

class ProduitForm(forms.ModelForm):
    class Meta:
        model = Produit
        fields = [
            'nom', 'description', 'categorie', 'prix', 'stock', 
            'unite', 'image', 'actif'
        ]
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom du produit'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description du produit'}),
            'categorie': forms.Select(attrs={'class': 'form-select'}),
            'prix': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': 'Prix en DH'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'unite': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'L, kg, m³...'}),
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'actif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'nom': 'Nom du produit',
            'description': 'Description',
            'categorie': 'Catégorie',
            'prix': 'Prix (DH)',
            'stock': 'Stock',
            'unite': 'Unité',
            'image': 'Image',
            'actif': 'Produit actif',
        }
        help_texts = {
            'prix': 'Prix unitaire en dirhams marocains (DH)',
            'stock': 'Quantité disponible en stock',
            'unite': 'Unité de mesure (L, kg, m³, etc.)',
        }

class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = [
            'raison_sociale', 'siret', 'contact', 'email', 'telephone',
            'adresse', 'ville', 'code_postal', 'statut', 'notes'
        ]
        widgets = {
            'raison_sociale': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom de l\'entreprise'}),
            'siret': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '12345678901234'}),
            'contact': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom du contact'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'contact@entreprise.com'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+212 5 22 34 56 78'}),
            'adresse': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Adresse complète'}),
            'ville': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ville'}),
            'code_postal': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '20000'}),
            'statut': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Notes internes'}),
        }
        labels = {
            'raison_sociale': 'Raison sociale',
            'siret': 'SIRET',
            'contact': 'Personne de contact',
            'email': 'Email',
            'telephone': 'Téléphone',
            'adresse': 'Adresse',
            'ville': 'Ville',
            'code_postal': 'Code postal',
            'statut': 'Statut',
            'notes': 'Notes',
        }
        help_texts = {
            'telephone': 'Format: +212 5 22 34 56 78',
            'siret': 'Numéro d\'identification de l\'entreprise',
            'notes': 'Informations complémentaires sur le client',
        }

class CommandeForm(forms.ModelForm):
    class Meta:
        model = Commande
        fields = ['client', 'date_commande', 'statut', 'notes']  # RETIRÉ 'date_livraison'
        widgets = {
            'client': forms.Select(attrs={'class': 'form-select'}),
            'date_commande': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'statut': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Notes sur la commande'}),
        }
        labels = {
            'client': 'Client',
            'date_commande': 'Date de commande',
            'statut': 'Statut',
            'notes': 'Notes',
        }
        help_texts = {
            'notes': 'Informations complémentaires sur la commande',
        }

