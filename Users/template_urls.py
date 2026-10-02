from django.urls import path
from .template_views import signup_view, profile_page

urlpatterns = [
    path('signup/', signup_view, name='signup'),
    path('profile/', profile_page, name='profile-page'),
]