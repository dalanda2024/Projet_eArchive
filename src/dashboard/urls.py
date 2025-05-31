from django.urls import path
from . import views
from django.urls import reverse

urlpatterns = [
    # Authentification
    path('signin/', views.signin, name='signin'),
    path('signup/', views.signup, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('redirect/', views.redirect_after_login, name='redirect_after_login'),

    # Téléchargements
    path('projet/<int:projet_id>/telecharger/', views.telecharger_projet, name='telecharger_projet'),
    path('cours/<int:cours_id>/telecharger/', views.telecharger_cours, name='telecharger_cours'),
    path('document/<int:doc_id>/telecharger/', views.telecharger_document, name='telecharger_document'),

    # Tableaux de bord
    path('etudiant/', views.indexetudiant, name='indexetudiant'),
    path('enseignant/', views.indexenseignant, name='indexenseignant'),
    path('personnel/', views.indexpersonnel, name='indexpersonnel'),

    # Scanner
    path('scanner/', views.scanner_document, name='scanner_document'),
    path('scanner/projet/<int:scan_id>/', views.traiter_scan_projet, name='traiter_scan_projet'),
    path('scanner/cours/<int:scan_id>/', views.traiter_scan_cours, name='traiter_scan_cours'),
    path('scanner/document/<int:scan_id>/', views.traiter_scan_document, name='traiter_scan_document'),
    path('api/upload_scan/', views.upload_scan_api, name='upload_scan_api'),

    # Projets étudiants
    path('projet/modifier_projet/<int:projet_id>/', views.modifier_projet, name='modifier_projet'),
    path('projet/supprimer_projet/<int:projet_id>/', views.supprimer_projet, name='supprimer_projet'),

    # Cours enseignants
    path('cours/modifier_cours/<int:cours_id>/', views.modifier_cours, name='modifier_cours'),
    path('cours/supprimer_cours/<int:cours_id>/', views.supprimer_cours, name='supprimer_cours'),

    # Documents administratifs
    path('document/modifier/<int:document_id>/', views.modifier_document, name='modifier_document'),
    path('document/supprimer/<int:document_id>/', views.supprimer_document, name='supprimer_document'),
]