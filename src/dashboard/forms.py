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
        fields = ['titre', 'type_projet', 'fichier', 'description', 'mots_cles', 'annee_academique']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class CoursEnseignantForm(forms.ModelForm):
    class Meta:
        model = CoursEnseignant
        fields = ['titre', 'code_cours', 'type_cours', 'fichier', 'description', 'semestre', 'annee_academique']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class DocumentAdministratifForm(forms.ModelForm):
    class Meta:
        model = DocumentAdministratif
        fields = ['titre', 'type_document', 'reference', 'fichier', 'description', 'est_public']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class ScanDocumentForm(forms.ModelForm):
    class Meta:
        model = ScanDocument
        fields = ['type_document', 'fichier_scan']