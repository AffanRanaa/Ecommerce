from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """
    Used to display/update a logged-in user's own profile. No password
    field here — profile view is not where passwords get changed.
    """

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone_number', 'address', 'display_picture']
        read_only_fields = ['id', 'username']  # username shouldn't change after signup