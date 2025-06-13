from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission, BaseUserManager
from django.utils.translation import gettext_lazy as _
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile

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

class ScanPage(models.Model):
    scan = models.ForeignKey('ScanDocument', related_name='pages', on_delete=models.CASCADE)
    numero_page = models.PositiveIntegerField()
    fichier_page = models.ImageField(upload_to='scan_pages/')
    
    class Meta:
        ordering = ['numero_page']
    
    def __str__(self):
        return f"Page {self.numero_page} du scan {self.scan.id}"

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
    type_cours = models.CharField(max_length=20, choices=TYPE_COURS_CHOICES, default='cours')
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
    fichier_scan = models.ImageField(upload_to='scans/', null=True, blank=True)
    date_scan = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='en_attente')
    resultat_projet = models.OneToOneField('ProjetEtudiant', null=True, blank=True, on_delete=models.SET_NULL)
    resultat_cours = models.OneToOneField('CoursEnseignant', null=True, blank=True, on_delete=models.SET_NULL)
    resultat_document = models.OneToOneField('DocumentAdministratif', null=True, blank=True, on_delete=models.SET_NULL)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)  # Sauvegarde initiale (crée le PK)

        # Ne rien faire si fichier déjà existant
        if self.fichier_scan or not hasattr(self, 'pages') or not self.pages.exists():
            return

        try:
            images = []
            for page in self.pages.all():
                img = Image.open(page.fichier_page.path).convert('RGB')
                images.append(img)

            if images:
                pdf_buffer = BytesIO()
                images[0].save(pdf_buffer, format='PDF', save_all=True, append_images=images[1:])
                pdf_buffer.seek(0)

                nom_pdf = f'scan_{self.id}.pdf'
                self.fichier_scan.save(nom_pdf, ContentFile(pdf_buffer.read()), save=False)
                self.status = 'traite'
                super().save(update_fields=['fichier_scan', 'status'])

        except Exception as e:
            self.status = 'erreur'
            super().save(update_fields=['status'])
            print(f"Erreur lors de la génération du PDF : {e}")