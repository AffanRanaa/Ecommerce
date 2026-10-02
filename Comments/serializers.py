from rest_framework import serializers
from .models import Comment


class CommentSerializer(serializers.ModelSerializer):
    """
    product and author are read_only — neither is sent by the client.
    product comes from the URL (which product's comments this is),
    author comes from request.user. Both get set in the view's
    perform_create(), not here.
    """

    author = serializers.ReadOnlyField(source='author.username')

    class Meta:
        model = Comment
        fields = ['id', 'product', 'author', 'body', 'created_at', 'updated_at']
        read_only_fields = ['id', 'product', 'author', 'created_at', 'updated_at']