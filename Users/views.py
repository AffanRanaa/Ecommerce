from rest_framework import generics, permissions
from .serializers import UserSerializer
from django.contrib.auth import get_user_model

User = get_user_model()


class ProfileView(generics.RetrieveUpdateAPIView):
    """
    GET returns the logged-in user's own profile, PUT/PATCH updates it.
    get_object() returns request.user directly instead of looking up
    a pk from the URL — this endpoint always means "my own profile".
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user