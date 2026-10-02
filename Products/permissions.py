from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Anyone (even not logged in) can read (GET/HEAD/OPTIONS).
    Only the object's owner can update/delete it.

    Works for any model whose owning field is named 'owner' (Product)
    or 'author' (Comment) — checked below.
    """

    def has_object_permission(self, request, view, obj):
        # SAFE_METHODS = GET, HEAD, OPTIONS — always allowed, no ownership check
        if request.method in permissions.SAFE_METHODS:
            return True

        # For write methods (PUT, PATCH, DELETE), check ownership
        owner_field = getattr(obj, 'owner', None) or getattr(obj, 'author', None)
        return owner_field == request.user