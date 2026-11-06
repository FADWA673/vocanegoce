from django.urls import path
from django.shortcuts import render
from . import views

urlpatterns = [
    # Page d'accueil / Dashboard
    path('', views.dashboard, name='dashboard'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Authentication
    path('register/', views.register, name='register'),
    path('login/', views.custom_login, name='login'),
    
    # Produits
    path('produits/', views.produit_list, name='produit_list'),
    path('produits/nouveau/', views.produit_create, name='produit_create'),
    path('produits/<int:pk>/', views.produit_detail, name='produit_detail'),
    path('produits/<int:pk>/modifier/', views.produit_update, name='produit_update'),
    path('produits/<int:pk>/supprimer/', views.produit_delete, name='produit_delete'),
    
    # Clients
    path('clients/', views.client_list, name='client_list'),
    path('clients/nouveau/', views.client_create, name='client_create'),
    path('clients/<int:pk>/', views.client_detail, name='client_detail'),
    path('clients/<int:pk>/modifier/', views.client_update, name='client_update'),
    path('clients/<int:pk>/supprimer/', views.client_delete, name='client_delete'),
    
    # Commandes
    path('commandes/', views.commande_list, name='commande_list'),
    path('commandes/nouvelle/', views.commande_create, name='commande_create'),
    path('commandes/<int:pk>/', views.commande_detail, name='commande_detail'),
    path('commandes/<int:pk>/modifier/', views.commande_update, name='commande_update'),
    path('commandes/<int:pk>/supprimer/', views.commande_delete, name='commande_delete'),
    
    # NOUVELLES API RECHERCHE INTELLIGENTE
    path('api/search/', views.search_api, name='search_api'),
    path('api/autocomplete/', views.autocomplete_api, name='autocomplete_api'),
   
    path('commandes/<int:pk>/facture_pdf/', views.generer_facture_pdf, name='generer_facture_pdf'),
    path("chiffre-affaire/", views.chiffre_affaire, name="chiffre_affaire"),
     
  

]
