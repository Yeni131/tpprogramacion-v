from django.db import models
from apps.users.models import User
from apps.products.models import Product, ProductVariant
from apps.coupons.models import Coupon


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending',   'Pendiente'),
        ('paid',      'Pagado'),
        ('shipped',   'Enviado'),
        ('delivered', 'Entregado'),
        ('cancelled', 'Cancelado'),
    ]

    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    coupon      = models.ForeignKey(Coupon, on_delete=models.SET_NULL,
                      null=True, blank=True)
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount    = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    address     = models.TextField()
    created     = models.DateTimeField(auto_now_add=True)
    updated     = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Orden'
        verbose_name_plural = 'Órdenes'
        ordering = ['-created']

    def get_final_total(self):
        return self.total_price - self.discount

    def __str__(self):
        return f"Orden #{self.id} — {self.user.username} — {self.status}"


class OrderItem(models.Model):
    order    = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product  = models.ForeignKey(Product, on_delete=models.PROTECT)
    variant  = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL,
                   null=True, blank=True)
    price    = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()

    class Meta:
        verbose_name = 'Item de orden'
        verbose_name_plural = 'Items de orden'

    def get_subtotal(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"