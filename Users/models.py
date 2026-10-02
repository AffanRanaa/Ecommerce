from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """
    Custom User model, extending Django's built-in AbstractUser.
    Inherits: username, email, password, first_name, last_name,
    is_staff, is_active, is_superuser, date_joined, last_login.
    We add the extra fields the project requires.
    """

    email = models.EmailField(unique=True)  # enforce unique email for signup/signin
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    display_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username