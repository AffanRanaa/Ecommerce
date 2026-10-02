from django.apps import AppConfig


class CartConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Cart'

    def ready(self):
        import Cart.signals  # noqa — this import is what actually registers the signal