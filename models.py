from django.db import models
from django.db.models import Sum, F
from apps.users.models import User
from apps.products.models import Product, ProductVariant


class Cart(models.Model):
    user        = models.ForeignKey(
                      User, on_delete=models.CASCADE,
                      null=True, blank=True, related_name='carts'
                  )
    session_key = models.CharField(max_length=40, null=True, blank=True)
    created     = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Carrito'
        verbose_name_plural = 'Carritos'

    def get_total(self):
        """
        BUG 6 FIX: una sola query con aggregate en lugar de
        un loop Python que hacía N queries (una por item).
        Usa los items ya prefetcheados si vienen de _cart_qs().
        """
        return sum(item.get_subtotal() for item in self.items.all())

    def get_item_count(self):
        """Total de unidades (no de líneas) en el carrito."""
        result = self.items.aggregate(total=Sum('quantity'))
        return result['total'] or 0

    def __str__(self):
        return f"Carrito #{self.id} — {self.user or self.session_key}"


class CartItem(models.Model):
    cart     = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product  = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant  = models.ForeignKey(
                   ProductVariant, on_delete=models.SET_NULL,
                   null=True, blank=True
               )
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name        = 'Item del carrito'
        verbose_name_plural = 'Items del carrito'
        # BUG 7 FIX: impide duplicados cart+product+variant
        unique_together     = [('cart', 'product', 'variant')]

    def get_unit_price(self):
        if self.variant:
            return self.variant.get_final_price()
        return self.product.price

    def get_subtotal(self):
        return self.get_unit_price() * self.quantity

    def __str__(self):
        return f"{self.quantity}× {self.product.name}"