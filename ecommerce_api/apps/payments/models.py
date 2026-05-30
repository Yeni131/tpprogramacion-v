from django.db import models
from apps.orders.models import Order


class Payment(models.Model):
    PROVIDER_CHOICES = [
        ('stripe',      'Stripe'),
        ('mercadopago', 'MercadoPago'),
    ]
    STATUS_CHOICES = [
        ('pending',   'Pendiente'),
        ('completed', 'Completado'),
        ('failed',    'Fallido'),
        ('refunded',  'Reembolsado'),
    ]

    order     = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    provider  = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    status    = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    amount    = models.DecimalField(max_digits=10, decimal_places=2)
    stripe_id = models.CharField(max_length=200, blank=True, null=True)  # payment_intent_id
    mp_id     = models.CharField(max_length=200, blank=True, null=True)  # preference_id
    created   = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'

    def __str__(self):
        return f"Pago #{self.id} — {self.provider} — {self.status}"