from django.contrib import admin

from django.contrib.auth.admin import UserAdmin
from .models import Utilisateur, ProjetEtudiant, CoursEnseignant, DocumentAdministratif
from django.utils.html import format_html
from .models import ScanDocument, ScanPage

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


class ScanPageAdmin(admin.ModelAdmin):
    list_display = ['scan', 'numero_page', 'aperçu_image']
    readonly_fields = ['aperçu_image']

    def aperçu_image(self, obj):
        if obj.fichier_page:
            return format_html(f"<img src='{obj.fichier_page.url}' width='100' />")
        return "Aucune image"
    
    aperçu_image.short_description = "Aperçu"

admin.site.register(ScanPage, ScanPageAdmin)