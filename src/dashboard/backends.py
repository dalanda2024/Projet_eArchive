from django.contrib.auth.backends import ModelBackend
from .models import Utilisateur

class MatriculeBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = Utilisateur.objects.get(username=username)
            if user.check_password(password):
                return user
        except Utilisateur.DoesNotExist:
            return None