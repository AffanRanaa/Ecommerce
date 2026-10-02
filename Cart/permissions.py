from rest_framework import permissions


class IsCartItemOwner(permissions.BasePermission):
    """
    CartItem has no 'owner' or 'author' field directly — ownership is
    one hop away, through item.cart.user. So this permission checks
    that relationship instead of reusing IsOwnerOrReadOnly.
    """

    def has_object_permission(self, request, view, obj):
        return obj.cart.user == request.user