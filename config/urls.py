"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # API URLs
    path('api/', include('Users.urls')),
    path('api/', include('Products.urls')),
    path('api/', include('Comments.urls')),
    path('api/', include('Orders.urls')),
    path('api/', include('Cart.urls')),
    
    # Template URLs
    path('', include('Cart.cart_template_urls')),
    path('', include('Orders.urls_template')),
    path('', include('Products.template_urls')),
    path('', include('Users.template_urls')),

    # Authentication pages
    path('login/', auth_views.LoginView.as_view(template_name='Users/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='product-list-page'), name='logout'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
