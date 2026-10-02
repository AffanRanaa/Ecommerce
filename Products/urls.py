from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, ProductSearchView

router = DefaultRouter()
router.register('products', ProductViewSet, basename='product')

urlpatterns = [
    path('search/', ProductSearchView.as_view(), name='product-search'),
] + router.urls