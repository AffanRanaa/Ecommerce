from rest_framework import serializers, viewsets, permissions, parsers, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.postgres.search import TrigramSimilarity
from django.shortcuts import get_object_or_404
from .models import Product, ProductImage
from .serializers import ProductSerializer, ProductImageSerializer
from .permissions import IsOwnerOrReadOnly


class ProductViewSet(viewsets.ModelViewSet):
    """
    Handles list, retrieve, create, update, delete for products.
    IsAuthenticatedOrReadOnly: anyone can GET (browse products),
    but you must be logged in to POST a new one.
    IsOwnerOrReadOnly: once a product exists, only its owner can
    edit/delete it (checked automatically by DRF on write actions).
    """

    queryset = Product.objects.all().order_by('-created_at')
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        # owner is never sent by the client — it's always the logged-in user
        serializer.save(owner=self.request.user)

    def perform_destroy(self, instance):
        # A product with reserved stock must not be deleted because
        # unpaid orders still depend on that reservation.
        if instance.reserved_quantity > 0:
            raise serializers.ValidationError(
                'This product cannot be deleted while stock is reserved '
                'by an unpaid order.'
            )

        instance.delete()

    @action(
        detail=True,
        methods=['post'],
        parser_classes=[parsers.MultiPartParser, parsers.FormParser],
        permission_classes=[permissions.IsAuthenticated]
    )
    def upload_image(self, request, pk=None):
        """
        POST /api/products/{id}/upload_image/
        Accepts MULTIPLE files in one request under the key 'images'
        (not 'image') — each call can add several ProductImage rows at
        once, and calling it again later just adds MORE, never replaces
        existing ones (there's no unique constraint stopping that).
        """
        product = self.get_object()
        if product.owner != request.user:
            return Response({'detail': 'Not your product.'}, status=status.HTTP_403_FORBIDDEN)

        files = request.FILES.getlist('images')
        if not files:
            return Response({'images': 'No files provided.'}, status=status.HTTP_400_BAD_REQUEST)

        created_images = []
        for file in files:
            image = ProductImage.objects.create(product=product, image=file)
            created_images.append(image)

        serializer = ProductImageSerializer(created_images, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=True,
        methods=['delete'],
        url_path=r'images/(?P<image_id>\d+)',
        permission_classes=[permissions.IsAuthenticated]
    )
    def delete_image(self, request, pk=None, image_id=None):
        """
        DELETE /api/products/{id}/images/{image_id}/
        Deletes ONE specific image, not the whole product. Only the
        product's owner can do this — checked explicitly since this is
        a custom action, not one of DRF's automatic object-level checks.
        """
        product = self.get_object()
        if product.owner != request.user:
            return Response({'detail': 'Not your product.'}, status=status.HTTP_403_FORBIDDEN)

        image = get_object_or_404(ProductImage, id=image_id, product=product)
        image.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductSearchView(generics.ListAPIView):
    """
    GET /api/search/?q=shirt
    Uses PostgreSQL trigram similarity (via the pg_trgm extension + GIN
    index on Product.title/description) instead of icontains. This
    tolerates typos and partial matches, and stays fast at scale because
    the GIN index avoids a full table scan.
    """
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        query = self.request.query_params.get('q', '')
        if not query:
            return Product.objects.none()

        return Product.objects.annotate(
            similarity=TrigramSimilarity('title', query) + TrigramSimilarity('description', query)
        ).filter(similarity__gt=0.1).order_by('-similarity')[:10]
