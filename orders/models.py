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
    coupon      = models.ForeignKey(Coupon, null=True, blank=True, on_delete=models.SET_NULL)
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount    = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    address     = models.TextField(blank=True, null=True)

    # ── Campos extendidos para Checkout ──────────────────────────────────────
    first_name    = models.CharField(max_length=100, blank=True)
    last_name     = models.CharField(max_length=100, blank=True)
    email         = models.EmailField(blank=True)
    phone         = models.CharField(max_length=20, blank=True)
    city          = models.CharField(max_length=100, blank=True)
    wants_invoice = models.BooleanField(default=False)
    # ─────────────────────────────────────────────────────────────────────────

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return f'Orden #{self.pk} — {self.user}'


class OrderItem(models.Model):
    order   = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT, null=True, blank=True)
    price   = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f'{self.quantity}x {self.product} (Orden #{self.order_id})'

    @property
    def subtotal(self):
        return self.price * self.quantity


class BillingData(models.Model):
    """Datos de facturación opcionales asociados a una orden."""
    order         = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='billing')
    business_name = models.CharField(max_length=200)
    ruc           = models.CharField(max_length=20)

    def __str__(self):
        return f'Factura {self.business_name} — Orden #{self.order_id}'