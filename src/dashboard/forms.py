from django import forms 
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import *
from django.contrib.auth import authenticate 

class InscriptionForm(UserCreationForm):
    role = forms.ChoiceField(choices=Utilisateur.ROLE_CHOICES)
    profile_picture = forms.ImageField(required=False)
    phone = forms.CharField(max_length=20, required=False)
    department = forms.CharField(max_length=100, required=False)

    class Meta:
        model = Utilisateur
        fields = ('matricule', 'username', 'email', 'first_name', 'last_name', 
                 'role', 'password1', 'password2', 'profile_picture', 'phone', 'department')

class ConnexionForm(forms.Form):
    matricule = forms.IntegerField(label="Matricule")
    username = forms.CharField(label="Nom d'utilisateur")
    password = forms.CharField(label="Mot de passe", widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        matricule = cleaned_data.get('matricule')

        if username and password and matricule:
            user = authenticate(username=username, password=password)
            if user is None:
                raise forms.ValidationError("Nom d'utilisateur ou mot de passe incorrect")
            if user.matricule != matricule:
                raise forms.ValidationError("Matricule incorrect")
        return cleaned_data

class ProjetEtudiantForm(forms.ModelForm):
    class Meta:
        model = ProjetEtudiant
        fields = ['titre', 'type_projet', 'fichier', 'description', 'mots_cles']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class CoursEnseignantForm(forms.ModelForm):
    class Meta:
        model = CoursEnseignant
        fields = ['titre',  'type_cours', 'fichier', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class DocumentAdministratifForm(forms.ModelForm):
    class Meta:
        model = DocumentAdministratif
        fields = ['titre', 'type_document', 'fichier', 'description', 'est_public']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class ScanDocumentForm(forms.ModelForm):
    class Meta:
        model = ScanDocument
        fields = ['type_document', 'fichier_scan']


class ScanTypeForm(forms.Form):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user.role == 'etudiant':
            self.fields['type_projet'] = forms.ChoiceField(
                choices=ProjetEtudiant.TYPE_PROJET_CHOICES,
                label="Type de projet"
            )
        elif user.role == 'enseignant':
            self.fields['type_cours'] = forms.ChoiceField(
                choices=CoursEnseignant.TYPE_COURS_CHOICES,
                label="Type de cours"
            )
        elif user.role == 'personnel':
            self.fields['type_document_admin'] = forms.ChoiceField(
                choices=DocumentAdministratif.TYPE_DOC_CHOICES,
                label="Type de document"
            )
        
        # Limiter les choix selon le rôle
        if user.role == 'etudiant':
            self.fields['type_document'] = forms.ChoiceField(
                choices=[('projet', 'Projet Étudiant')],
                initial='projet',
                widget=forms.HiddenInput()
            )
        elif user.role == 'enseignant':
            self.fields['type_document'] = forms.ChoiceField(
                choices=[('cours', 'Cours Enseignant')],
                initial='cours',
                widget=forms.HiddenInput()
            )
        elif user.role == 'personnel':
            self.fields['type_document'] = forms.ChoiceField(
                choices=[('document', 'Document Administratif')],
                initial='document',
                widget=forms.HiddenInput()
            )
