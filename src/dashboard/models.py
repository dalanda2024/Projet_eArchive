from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.models import BaseUserManager
from django.utils.translation import gettext_lazy as _

class UtilisateurManager(BaseUserManager):
    def create_user(self, username, matricule, password=None, **extra_fields):
        if not username:
            raise ValueError('Le nom d\'utilisateur est obligatoire')
        if not matricule:
            raise ValueError('Le matricule est obligatoire')
        
        user = self.model(
            username=username,
            matricule=matricule,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, matricule, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, matricule, password, **extra_fields)

class Utilisateur(AbstractUser):
    matricule = models.IntegerField(unique=True, null=False, blank=False)
    ROLE_CHOICES = (
        ('etudiant', 'Étudiant'),
        ('enseignant', 'Enseignant'),
        ('personnel', 'Personnel Administratif')
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    department = models.CharField(max_length=100, blank=True)

    objects = UtilisateurManager()
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['matricule']

    telechargements = models.ManyToManyField(
        'ProjetEtudiant', 
        related_name='telecharge_par',
        blank=True,
        verbose_name='Projets téléchargés'
    )

    groups = models.ManyToManyField(
        Group,
        related_name="utilisateurs",
        blank=True,
        help_text='Les groupes auxquels appartient cet utilisateur.',
        verbose_name='groupes',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="utilisateurs",
        blank=True,
        help_text='Permissions spécifiques pour cet utilisateur.',
        verbose_name='permissions utilisateur',
    )

class ProjetEtudiant(models.Model):
    TYPE_PROJET_CHOICES = (
        ('pfe', 'Projet de Fin d\'Études'),
        ('memoire', 'Mémoire'),
        ('these', 'Thèse'),
        ('rapport', 'Rapport de Stage'),
        ('autre', 'Autre'),
    )
    
    titre = models.CharField(max_length=255)
    description = models.TextField()
    fichier = models.FileField(upload_to='projets/')
    date_ajout = models.DateTimeField(auto_now_add=True)
    auteur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, limit_choices_to={'role': 'etudiant'})
    type_projet = models.CharField(max_length=20, choices=TYPE_PROJET_CHOICES, default='pfe')
    mots_cles = models.CharField(max_length=255, blank=True)
    annee_academique = models.CharField(max_length=20)
    scan_provenance = models.ForeignKey('ScanDocument', null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.titre

class CoursEnseignant(models.Model):
    TYPE_COURS_CHOICES = (
        ('cours', 'Cours Magistral'),
        ('td', 'Travaux Dirigés'),
        ('tp', 'Travaux Pratiques'),
        ('support', 'Support de Cours'),
        ('examen', 'Examen'),
    )
    
    titre = models.CharField(max_length=255)
    description = models.TextField()
    fichier = models.FileField(upload_to='cours/')
    date_ajout = models.DateTimeField(auto_now_add=True)
    auteur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, limit_choices_to={'role': 'enseignant'})
    code_cours = models.CharField(max_length=20)
    type_cours = models.CharField(max_length=20, choices=TYPE_COURS_CHOICES, default='cours')
    semestre = models.PositiveSmallIntegerField()
    annee_academique = models.CharField(max_length=20)
    scan_provenance = models.ForeignKey('ScanDocument', null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.titre

class DocumentAdministratif(models.Model):
    TYPE_DOC_CHOICES = (
        ('circulaire', 'Circulaire'),
        ('note', 'Note de Service'),
        ('pv', 'Procès-Verbal'),
        ('decision', 'Décision'),
        ('rapport', 'Rapport'),
        ('autre', 'Autre'),
    )
    
    titre = models.CharField(max_length=255)
    fichier = models.FileField(upload_to='documents_admin/')
    description = models.TextField()
    date_ajout = models.DateTimeField(auto_now_add=True)
    auteur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, limit_choices_to={'role': 'personnel'})
    type_document = models.CharField(max_length=20, choices=TYPE_DOC_CHOICES, default='circulaire')
    reference = models.CharField(max_length=50)
    est_public = models.BooleanField(default=False)
    scan_provenance = models.ForeignKey('ScanDocument', null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.titre

class ScanDocument(models.Model):
    TYPE_DOC_CHOICES = (
        ('projet', 'Projet Étudiant'),
        ('cours', 'Cours Enseignant'),
        ('document', 'Document Administratif'),
    )
    
    STATUS_CHOICES = (
        ('en_attente', 'En attente'),
        ('traite', 'Traité'),
        ('erreur', 'Erreur'),
    )
    
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE)
    type_document = models.CharField(max_length=20, choices=TYPE_DOC_CHOICES)
    fichier_scan = models.FileField(upload_to='scans/')
    date_scan = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='en_attente')
    resultat_projet = models.OneToOneField('ProjetEtudiant', null=True, blank=True, on_delete=models.SET_NULL)
    resultat_cours = models.OneToOneField('CoursEnseignant', null=True, blank=True, on_delete=models.SET_NULL)
    resultat_document = models.OneToOneField('DocumentAdministratif', null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"Scan {self.id} - {self.get_type_document_display()}"