from django.db import models
from django.conf import settings
from Products.models import Product


class Comment(models.Model):
    """
    A comment left by a user on a product. A product can have many comments
    (one-to-many). Ownership restrictions (can't comment on own product,
    edit/delete only own comment) are enforced at the serializer/view level,
    not here — the model just stores the data.
    """

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']  # newest comments first, like Facebook/LinkedIn feeds

    def __str__(self):
        return f"Comment by {self.author.username} on {self.product.title}"
