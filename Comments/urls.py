from django.urls import path
from .views import CommentListCreateView, CommentDetailView

urlpatterns = [
    path('products/<int:product_id>/comments/', CommentListCreateView.as_view(), name='product-comments'),
    path('comments/<int:pk>/', CommentDetailView.as_view(), name='comment-detail'),
]