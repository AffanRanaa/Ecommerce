class SessionCart:
    """
    Wraps request.session to manage a guest (not-logged-in) user's cart.
    Stored as a plain dict: {"<product_id>": quantity, ...}. This is
    completely separate from the Cart/CartItem database models used for
    logged-in users — nothing here touches the database.
    """

    SESSION_KEY = 'cart'

    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(self.SESSION_KEY)
        if cart is None:
            cart = self.session[self.SESSION_KEY] = {}
        self.cart = cart

    def add(self, product_id, quantity=1):
        product_id = str(product_id)  # session/JSON keys must be strings
        if product_id in self.cart:
            self.cart[product_id] += quantity
        else:
            self.cart[product_id] = quantity
        self._save()

    def update_quantity(self, product_id, quantity):
        product_id = str(product_id)
        if product_id in self.cart:
            self.cart[product_id] = quantity
            self._save()

    def remove(self, product_id):
        product_id = str(product_id)
        if product_id in self.cart:
            del self.cart[product_id]
            self._save()

    def clear(self):
        self.session[self.SESSION_KEY] = {}
        self._save()

    def items(self):
        """Returns {product_id: quantity} — used to look up Product objects in the view."""
        return self.cart

    def _save(self):
        self.session.modified = True  # tells Django the session data changed, so it gets saved