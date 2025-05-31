from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.http import FileResponse
import os
from django.contrib.auth import login
from .forms import *
from .models import *
import base64
from django.utils.text import slugify
import uuid



# === Vérificateurs de rôle ===
def est_etudiant(user):
    return user.role == 'etudiant'

def est_enseignant(user):
    return user.role == 'enseignant'

def est_personnel(user):
    return user.role == 'personnel'

# === Redirection après connexion selon le rôle ===
def redirect_after_login(request):
    if request.user.role == 'etudiant':
        return redirect('indexetudiant')
    elif request.user.role == 'enseignant':
        return redirect('indexenseignant')
    elif request.user.role == 'personnel':
        return redirect('indexpersonnel')
    return redirect('index')

# === AUTH ===
def signup(request):
    if request.method == 'POST':
        form = InscriptionForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Inscription réussie!")
            return redirect_after_login(request)
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = InscriptionForm()
    
    return render(request, 'dashboard/signup.html', {'form': form})

def signin(request):
    if request.user.is_authenticated:
        return redirect_after_login(request)

    if request.method == 'POST':
        form = ConnexionForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect_after_login(request)
            else:
                messages.error(request, "Identifiants incorrects")
    else:
        form = ConnexionForm()
    
    return render(request, 'dashboard/signin.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('signin')

# === Scanner ===
@login_required
def scanner_document(request):
    if request.method == 'POST':
        form = ScanDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            scan = form.save(commit=False)
            scan.utilisateur = request.user
            scan.save()
            
            # Traitement selon le type de document
            if scan.type_document == 'projet' and est_etudiant(request.user):
                return redirect('traiter_scan_projet', scan_id=scan.id)
            elif scan.type_document == 'cours' and est_enseignant(request.user):
                return redirect('traiter_scan_cours', scan_id=scan.id)
            elif scan.type_document == 'document' and est_personnel(request.user):
                return redirect('traiter_scan_document', scan_id=scan.id)
            else:
                messages.error(request, "Type de document incompatible avec votre profil")
                return redirect('dashboard')
    else:
        form = ScanDocumentForm()
    
    return render(request, 'dashboard/scanner.html', {'form': form})

@login_required
def traiter_scan_projet(request, scan_id):
    scan = get_object_or_404(ScanDocument, id=scan_id, utilisateur=request.user, type_document='projet')
    
    if request.method == 'POST':
        form = ProjetEtudiantForm(request.POST, request.FILES)
        if form.is_valid():
            projet = form.save(commit=False)
            projet.auteur = request.user
            projet.scan_provenance = scan
            projet.save()
            
            scan.status = 'traite'
            scan.resultat_projet = projet
            scan.save()
            
            messages.success(request, "Projet créé à partir du scan avec succès!")
            return redirect('indexetudiant')
    else:
        initial_data = {
            'fichier': scan.fichier_scan,
        }
        form = ProjetEtudiantForm(initial=initial_data)
    
    return render(request, 'dashboard/traiter_scan.html', {
        'form': form,
        'scan': scan,
        'type_doc': 'projet étudiant'
    })

@login_required
def traiter_scan_cours(request, scan_id):
    scan = get_object_or_404(ScanDocument, id=scan_id, utilisateur=request.user, type_document='cours')
    
    if request.method == 'POST':
        form = CoursEnseignantForm(request.POST, request.FILES)
        if form.is_valid():
            cours = form.save(commit=False)
            cours.auteur = request.user
            cours.scan_provenance = scan
            cours.save()
            
            scan.status = 'traite'
            scan.resultat_cours = cours
            scan.save()
            
            messages.success(request, "Cours créé à partir du scan avec succès!")
            return redirect('indexenseignant')
    else:
        initial_data = {
            'fichier': scan.fichier_scan,
        }
        form = CoursEnseignantForm(initial=initial_data)
    
    return render(request, 'dashboard/traiter_scan.html', {
        'form': form,
        'scan': scan,
        'type_doc': 'cours enseignant'
    })

@login_required
def traiter_scan_document(request, scan_id):
    scan = get_object_or_404(ScanDocument, id=scan_id, utilisateur=request.user, type_document='document')
    
    if request.method == 'POST':
        form = DocumentAdministratifForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.auteur = request.user
            doc.scan_provenance = scan
            doc.save()
            
            scan.status = 'traite'
            scan.resultat_document = doc
            scan.save()
            
            messages.success(request, "Document créé à partir du scan avec succès!")
            return redirect('indexpersonnel')
    else:
        initial_data = {
            'fichier': scan.fichier_scan,
        }
        form = DocumentAdministratifForm(initial=initial_data)
    
    return render(request, 'dashboard/traiter_scan.html', {
        'form': form,
        'scan': scan,
        'type_doc': 'document administratif'
    })


# === ÉTUDIANT ===
@login_required
@user_passes_test(est_etudiant)
def indexetudiant(request):
    projets = ProjetEtudiant.objects.filter(auteur=request.user)
    projets_autres = ProjetEtudiant.objects.exclude(auteur=request.user)
    cours_enseignants = CoursEnseignant.objects.all()
    scans = ScanDocument.objects.filter(utilisateur=request.user, type_document='projet')
    
    stats = {
        'nb_projets': projets.count(),
        'nb_telechargements': request.user.telechargements.count(),
        'nb_scans': scans.count(),
    }
    
    if request.method == 'POST':
        form = ProjetEtudiantForm(request.POST, request.FILES)
        if form.is_valid():
            projet = form.save(commit=False)
            projet.auteur = request.user
            projet.save()
            messages.success(request, "Projet ajouté avec succès!")
            return redirect('indexetudiant')
    else:
        form = ProjetEtudiantForm()
        
    return render(request, 'dashboard/indexetudiant.html', {
        'form': form,
        'projets': projets,
        'projets_autres': projets_autres,
        'cours_enseignants': cours_enseignants,
        'scans': scans,
        'stats': stats,
        'user': request.user
    })

@login_required
@user_passes_test(est_etudiant)
def modifier_projet(request, projet_id):
    projet = get_object_or_404(ProjetEtudiant, id=projet_id)
    if request.method == 'POST':
        form = ProjetEtudiantForm(request.POST, request.FILES, instance=projet)
        if form.is_valid():
            form.save()
            return redirect('indexetudiant')
    else:
        form = ProjetEtudiantForm(instance=projet)
    return render(request, 'dashboard/modifier_projet.html', {'form': form})

@login_required
def supprimer_projet(request, projet_id):
    projet = get_object_or_404(ProjetEtudiant, id=projet_id)
    if not (projet.auteur == request.user or est_personnel(request.user)):
        return HttpResponseForbidden()
        return render(request, 'dashboard/erreur.html', {
            'message': "Ce projet n'existe pas ou vous n'y avez pas accès."
        })
    
    if request.method == 'POST':
        projet.delete()
        return redirect('indexetudiant')
    return render(request, 'dashboard/supprimer_projet.html', {'projet': projet})

# === ENSEIGNANT ===
@login_required
@user_passes_test(est_enseignant)
def indexenseignant(request):
    cours = CoursEnseignant.objects.filter(auteur=request.user)
    projets = ProjetEtudiant.objects.all()
    scans = ScanDocument.objects.filter(utilisateur=request.user, type_document='cours')
    
    stats = {
        'nb_cours': cours.count(),
        'nb_projets': projets.count(),
        'nb_scans': scans.count(),
    }
    
    if request.method == 'POST':
        form = CoursEnseignantForm(request.POST, request.FILES)
        if form.is_valid():
            cours = form.save(commit=False)
            cours.auteur = request.user
            cours.save()
            messages.success(request, "Cours ajouté avec succès!")
            return redirect('indexenseignant')
    else:
        form = CoursEnseignantForm()
        
    return render(request, 'dashboard/indexenseignant.html', {
        'form': form,
        'cours': cours,
        'projets_etudiants': projets,
        'scans': scans,
        'stats': stats,
        'user': request.user
    })


@login_required
@user_passes_test(est_enseignant)
def modifier_cours(request, cours_id):
    cours = get_object_or_404(CoursEnseignant, id=cours_id)
    if request.method == 'POST':
        form = CoursEnseignantForm(request.POST, request.FILES, instance=cours)
        if form.is_valid():
            form.save()
            return redirect('indexenseignant')
    else:
        form = CoursEnseignantForm(instance=cours)
    return render(request, 'dashboard/modifier_cours.html', {'form': form})

@login_required
def supprimer_cours(request, cours_id):
    cours = get_object_or_404(CoursEnseignant, id=cours_id)
    if not (cours.auteur == request.user or est_personnel(request.user)):
        return HttpResponseForbidden()
    
    if request.method == 'POST':
        cours.delete()
        return redirect('indexenseignant')
    return render(request, 'dashboard/supprimer_cours.html', {'cours': cours})

# === PERSONNEL ===
@login_required
@user_passes_test(est_personnel)
def indexpersonnel(request):
    documents = DocumentAdministratif.objects.filter(auteur=request.user)
    all_cours_enseignants = CoursEnseignant.objects.all()
    projets_etudiants = ProjetEtudiant.objects.all()
    scans = ScanDocument.objects.filter(utilisateur=request.user, type_document='document')
    
    stats = {
        'nb_documents': documents.count(),
        'nb_cours': all_cours_enseignants.count(),
        'nb_projets': projets_etudiants.count(),
        'nb_scans': scans.count(),
    }
    
    if request.method == 'POST':
        form = DocumentAdministratifForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.auteur = request.user
            doc.save()
            messages.success(request, "Document ajouté avec succès!")
            return redirect('indexpersonnel')
    else:
        form = DocumentAdministratifForm()
        
    return render(request, 'dashboard/indexpersonnel.html', {
        'form': form,
        'documents': documents,
        'all_cours_enseignants': all_cours_enseignants,
        'projets_etudiants': projets_etudiants,
        'scans': scans,
        'stats': stats,
        'user': request.user
    })



@login_required
@user_passes_test(est_personnel)
def modifier_document(request, document_id):
    document = get_object_or_404(DocumentAdministratif, id=document_id)
    if request.method == 'POST':
        form = DocumentAdministratifForm(request.POST, request.FILES, instance=document)
        if form.is_valid():
            form.save()
            return redirect('indexpersonnel')
    else:
        form = DocumentAdministratifForm(instance=document)
    return render(request, 'dashboard/modifier_document.html', {'form': form})

@login_required
@user_passes_test(est_personnel)
def supprimer_document(request, document_id):
    document = get_object_or_404(DocumentAdministratif, id=document_id)
    if request.method == 'POST':
        document.delete()
        return redirect('indexpersonnel')
    return render(request, 'dashboard/supprimer_document.html', {'document': document})


# === Téléchargements ===
@login_required
def telecharger_projet(request, projet_id):
    projet = get_object_or_404(ProjetEtudiant, id=projet_id)
    request.user.telechargements.add(projet)
    return FileResponse(projet.fichier.open(), as_attachment=True, filename=projet.fichier.name)

@login_required
def telecharger_cours(request, cours_id):
    cours = get_object_or_404(CoursEnseignant, id=cours_id)
    return FileResponse(cours.fichier.open(), as_attachment=True, filename=cours.fichier.name)

@login_required
def telecharger_document(request, doc_id):
    document = get_object_or_404(DocumentAdministratif, id=doc_id)
    return FileResponse(document.fichier.open(), as_attachment=True, filename=document.fichier.name)

# API pour le scanner (utilisée par JavaScript)
@login_required
def upload_scan_api(request):
    if request.method == 'POST' and request.FILES.get('scan'):
        scan_file = request.FILES['scan']
        doc_type = request.POST.get('type_document', 'projet')
        
        scan = ScanDocument(
            utilisateur=request.user,
            type_document=doc_type,
            fichier_scan=scan_file
        )
        scan.save()
        
        return JsonResponse({
            'status': 'success',
            'scan_id': scan.id,
            'redirect_url': reverse('traiter_scan', kwargs={'scan_id': scan.id})
        })
    
    return JsonResponse({'status': 'error'}, status=400)
    document = get_object_or_404(DocumentAdministratif, id=doc_id)
    return FileResponse(document.fichier.open(), as_attachment=True,filename=doc.fichier.name)