from django.contrib import admin

from django.contrib.auth.admin import UserAdmin
from .models import Utilisateur, ProjetEtudiant, CoursEnseignant, DocumentAdministratif

# Utilisation du UserAdmin pour le modèle personnalisé
class UtilisateurAdmin(UserAdmin):
    model = Utilisateur
    list_display = ['username', 'email', 'matricule', 'role', 'is_staff']
    fieldsets = UserAdmin.fieldsets + (
        ('Informations supplémentaires', {'fields': ('matricule', 'role')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informations supplémentaires', {'fields': ('matricule', 'role')}),
    )

admin.site.register(Utilisateur, UtilisateurAdmin)
admin.site.register(ProjetEtudiant)
admin.site.register(CoursEnseignant)
admin.site.register(DocumentAdministratif)
