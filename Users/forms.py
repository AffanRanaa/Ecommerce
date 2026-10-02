from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

User = get_user_model()


class SignupForm(UserCreationForm):
    """
    UserCreationForm already handles password hashing + the
    'passwords must match' validation for us. We just extend it to
    include our extra fields (email, phone_number, display_picture).
    """

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ['username', 'email', 'phone_number', 'address', 'display_picture']