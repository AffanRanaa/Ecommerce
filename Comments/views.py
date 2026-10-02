from rest_framework import generics, permissions, serializers as drf_serializers
from django.shortcuts import get_object_or_404
from Products.models import Product
from .models import Comment
from .serializers import CommentSerializer
from Products.permissions import IsOwnerOrReadOnly


class CommentListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/products/{product_id}/comments/  -> list all comments on that product
    POST /api/products/{product_id}/comments/  -> add a new comment to it
    """
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        # only comments belonging to the product in the URL
        product_id = self.kwargs['product_id']
        return Comment.objects.filter(product_id=product_id)

    def perform_create(self, serializer):
        product = get_object_or_404(Product, id=self.kwargs['product_id'])

        # the actual "can't comment on your own product" rule
        if product.owner == self.request.user:
            raise drf_serializers.ValidationError(
                "You cannot comment on your own product."
            )

        serializer.save(product=product, author=self.request.user)


class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET/PUT/PATCH/DELETE /api/comments/{id}/
    IsOwnerOrReadOnly ensures only the comment's author can edit/delete it
    (it checks obj.author, since Comment has no 'owner' field — see the
    permission class's fallback logic).
    """
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]