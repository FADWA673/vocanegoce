"""URL configuration for vocanegoce_project project."""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect
from django.views.generic import TemplateView

def redirect_to_register(request):
    return redirect('register')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('', redirect_to_register),  # Redirection vers inscription
    path('', include('gestion.urls')),
    

    
    # Pages spéciales pour les nouvelles fonctionnalités
    path('search/', TemplateView.as_view(template_name='gestion/search_interface.html'), name='search_interface'),
    path('chatbot/', TemplateView.as_view(template_name='gestion/chatbot_interface.html'), name='chatbot_interface'),
]

# Servir les fichiers media et static en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Admin site customization
admin.site.site_header = "VocaNégoce Administration"
admin.site.site_title = "VocaNégoce Admin"
admin.site.index_title = "Panneau d'administration avec IA"
