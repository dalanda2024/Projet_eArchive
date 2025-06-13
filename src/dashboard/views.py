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
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .forms import ScanDocumentForm
import base64
from django.core.files.base import ContentFile
import uuid
import json
from tempfile import NamedTemporaryFile
import img2pdf
from django.core.files import File



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
        matricule = request.POST.get('matricule')
        
        # Vérifie si le matricule existe déjà
        if Utilisateur.objects.filter(matricule=matricule).exists():
            messages.error(request, "Ce matricule est déjà enregistré")
        else:
            # Crée l'utilisateur avec username et matricule
            user = Utilisateur(
                username=request.POST.get('username'),
                matricule=matricule,
                email=request.POST.get('email'),
                role=request.POST.get('role'),
                first_name=request.POST.get('first_name', ''),
                last_name=request.POST.get('last_name', '')
            )
            user.set_password(request.POST.get('password1'))
            user.save()
            
            messages.success(request, "Inscription réussie! Vous pouvez maintenant vous connecter")
            return redirect('signin')
    
    return render(request, 'dashboard/signup.html')


def signin(request):
    if request.user.is_authenticated:
        return redirect_after_login(request)

    if request.method == 'POST':
        matricule = request.POST.get('matricule')
        password = request.POST.get('password')
        
        try:
            # Trouver l'utilisateur par matricule
            user = Utilisateur.objects.get(matricule=matricule)
            
            # Authentifier avec le username (comme dans votre modèle actuel)
            auth_user = authenticate(
                request, 
                username=user.username,  # Utilise le username pour l'authentification
                password=password
            )
            
            if auth_user is not None:
                login(request, auth_user)
                return redirect_after_login(request)
            else:
                messages.error(request, "Mot de passe incorrect")
        except Utilisateur.DoesNotExist:
            messages.error(request, "Matricule non reconnu")
    
    return render(request, 'dashboard/signin.html')




def logout_view(request):
    logout(request)
    return redirect('signin')

# === Scanner ===
@login_required
def scanner_document(request):
    if request.method == 'POST':
        form = ScanTypeForm(request.POST, user=request.user)
        if form.is_valid():
            type_document = form.cleaned_data['type_document']
            
            # Stockage des types selon le rôle
            if request.user.role == 'etudiant':
                type_projet = form.cleaned_data.get('type_projet')
                request.session['scan_type_projet'] = type_projet
            
            elif request.user.role == 'enseignant':
                type_cours = form.cleaned_data.get('type_cours')
                request.session['scan_type_cours'] = type_cours
            
            elif request.user.role == 'personnel':
                type_doc_admin = form.cleaned_data.get('type_document_admin')
                request.session['scan_type_doc_admin'] = type_doc_admin
            
            request.session['scan_type_document'] = type_document
            return render(request, 'dashboard/scanner.html', {
                'type_document': type_document,
                'user_role': request.user.role
            })
    else:
        form = ScanTypeForm(user=request.user)
    
    return render(request, 'dashboard/choisir_type_scan.html', {'form': form})


@login_required
def traiter_scan(request):
    if request.method == 'POST' and request.session.get('scan_type_document'):
        try:
            scan_data = json.loads(request.POST.get('scan_data', '{}'))
            pages = scan_data.get('pages', [])
        except json.JSONDecodeError:
            messages.error(request, "Données de scan invalides.")
            return redirect('scanner_document')
        
        if not pages:
            messages.error(request, "Aucune page scannée n'a été trouvée")
            return redirect('scanner_document')
        
        scan = ScanDocument(
            utilisateur=request.user,
            type_document=request.session.get('scan_type_document')
        )
        scan.save()
        
        for i, page_data in enumerate(pages):
            try:
                format_part, imgstr = page_data.split(';base64,') 
                ext = format_part.split('/')[-1]
            except ValueError:
                messages.error(request, "Format de page scannée incorrect.")
                scan.delete()
                return redirect('scanner_document')

            filename = f"scan_{scan.id}_page_{i+1}.{ext}"
            file_content = ContentFile(base64.b64decode(imgstr), name=filename)
            
            page = ScanPage(
                scan=scan,
                numero_page=i+1,
                fichier_page=file_content
            )
            page.save()
        
        # Redirection selon rôle
        if request.user.role == 'etudiant':
            return redirect('completer_scan_projet', scan_id=scan.id)
        elif request.user.role == 'enseignant':
            return redirect('completer_scan_cours', scan_id=scan.id)
        else:
            return redirect('completer_scan_document', scan_id=scan.id)
    
    return redirect('scanner_document')


@login_required
def completer_scan_projet(request, scan_id):
    scan = get_object_or_404(ScanDocument, id=scan_id, utilisateur=request.user)
    type_projet = request.session.get('scan_type_projet', 'pfe')
    
    if request.method == 'POST':
        form = ProjetEtudiantForm(request.POST)
        if form.is_valid():
            projet = form.save(commit=False)
            projet.auteur = request.user
            projet.type_projet = type_projet
            projet.scan_provenance = scan
            
            # Fusionner les pages en PDF
            fichier_pdf = combine_scan_pages(scan)
            if fichier_pdf is None:
                messages.error(request, "Erreur lors de la génération du fichier PDF.")
                return redirect('completer_scan_projet', scan_id=scan.id)
            
            projet.fichier = fichier_pdf
            projet.save()
            
            scan.status = 'traite'
            scan.resultat_projet = projet
            scan.save()
            
            request.session.pop('scan_type_document', None)
            request.session.pop('scan_type_projet', None)
            
            messages.success(request, "Projet créé à partir du scan avec succès!")
            return redirect('indexetudiant')
    else:
        form = ProjetEtudiantForm(initial={
            'titre': f"Projet scanné {scan.date_scan.strftime('%d/%m/%Y')}",
            'type_projet': type_projet,
            'description': "Document scanné et converti en format numérique"
        })
    
    return render(request, 'dashboard/completer_scan.html', {
        'form': form,
        'scan': scan,
        'type_doc': 'projet étudiant',
        'pages': scan.pages.all().order_by('numero_page')
    })


@login_required
def completer_scan_cours(request, scan_id):
    scan = get_object_or_404(ScanDocument, id=scan_id, utilisateur=request.user)
    type_cours = request.session.get('scan_type_cours', 'cours')
    
    if request.method == 'POST':
        form = CoursEnseignantForm(request.POST)
        if form.is_valid():
            cours = form.save(commit=False)
            cours.auteur = request.user
            cours.type_cours = type_cours
            cours.scan_provenance = scan
            
            fichier_pdf = combine_scan_pages(scan)
            if fichier_pdf is None:
                messages.error(request, "Erreur lors de la génération du fichier PDF.")
                return redirect('completer_scan_cours', scan_id=scan.id)
            
            cours.fichier = fichier_pdf
            cours.save()
            
            scan.status = 'traite'
            scan.resultat_cours = cours
            scan.save()
            
            request.session.pop('scan_type_document', None)
            request.session.pop('scan_type_cours', None)
            
            messages.success(request, "Cours créé à partir du scan avec succès!")
            return redirect('indexenseignant')
    else:
        form = CoursEnseignantForm(initial={
            'titre': f"Cours scanné {scan.date_scan.strftime('%d/%m/%Y')}",
            'type_cours': type_cours,
            'description': "Document scanné et converti en format numérique"
        })
    
    return render(request, 'dashboard/completer_scan.html', {
        'form': form,
        'scan': scan,
        'type_doc': 'cours enseignant',
        'pages': scan.pages.all().order_by('numero_page')
    })


@login_required
def completer_scan_document(request, scan_id):
    scan = get_object_or_404(ScanDocument, id=scan_id, utilisateur=request.user)
    type_doc_admin = request.session.get('scan_type_doc_admin', 'circulaire')
    
    if request.method == 'POST':
        form = DocumentAdministratifForm(request.POST)
        if form.is_valid():
            document = form.save(commit=False)
            document.auteur = request.user
            document.type_document = type_doc_admin
            document.scan_provenance = scan
            
            fichier_pdf = combine_scan_pages(scan)
            if fichier_pdf is None:
                messages.error(request, "Erreur lors de la génération du fichier PDF.")
                return redirect('completer_scan_document', scan_id=scan.id)
            
            document.fichier = fichier_pdf
            document.save()
            
            scan.status = 'traite'
            scan.resultat_document = document
            scan.save()
            
            request.session.pop('scan_type_document', None)
            request.session.pop('scan_type_doc_admin', None)
            
            messages.success(request, "Document administratif créé à partir du scan avec succès!")
            return redirect('indexpersonnel')
    else:
        form = DocumentAdministratifForm(initial={
            'titre': f"Document scanné {scan.date_scan.strftime('%d/%m/%Y')}",
            'type_document': type_doc_admin,
            'description': "Document scanné et converti en format numérique"
        })
    
    return render(request, 'dashboard/completer_scan.html', {
        'form': form,
        'scan': scan,
        'type_doc': 'document administratif',
        'pages': scan.pages.all().order_by('numero_page')
    })


def combine_scan_pages(scan):
    pages = scan.pages.all().order_by('numero_page')
    
    if not pages.exists():
        return None
    
    if pages.count() == 1:
        # Si une seule page, on retourne directement le fichier image.
        # ATTENTION : Vérifier que le champ accepte une image et non un pdf.
        return pages.first().fichier_page
    
    try:
        with NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_pdf:
            pdf_bytes = img2pdf.convert([page.fichier_page.path for page in pages])
            tmp_pdf.write(pdf_bytes)
            tmp_pdf.flush()
            pdf_name = f"scan_complet_{scan.id}.pdf"
            
            with open(tmp_pdf.name, 'rb') as pdf_file:
                django_file = File(pdf_file, name=pdf_name)
                return django_file
    except Exception as e:
        print(f"Erreur lors de la fusion des pages : {e}")
        return None



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