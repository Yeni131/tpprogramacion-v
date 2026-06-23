from django.db import models
from apps.orders.models import Order


class Payment(models.Model):
    PROVIDER_CHOICES = [
        ('stripe',      'Stripe'),
        ('mercadopago', 'MercadoPago'),
        ('manual',      'Manual'),           # transferencia / efectivo
    ]
    STATUS_CHOICES = [
        ('pending',   'Pendiente'),
        ('completed', 'Completado'),
        ('failed',    'Fallido'),
        ('refunded',  'Reembolsado'),
    ]
    METHOD_CHOICES = [
        ('bank_transfer', 'Transferencia Bancaria'),
        ('cash',          'Efectivo'),
        ('stripe',        'Stripe'),
        ('mercadopago',   'MercadoPago'),
    ]

    order  = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, default='manual')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    # Campos heredados (Stripe / MP)
    stripe_id = models.CharField(max_length=200, blank=True)
    mp_id     = models.CharField(max_length=200, blank=True)

    # ── Campos extendidos ─────────────────────────────────────────────────────
    payment_method     = models.CharField(max_length=20, choices=METHOD_CHOICES, default='cash')
    gateway            = models.CharField(max_length=50, blank=True)   # ej. 'stripe_checkout'
    external_payment_id = models.CharField(max_length=200, blank=True) # ID unificado futuro
    payment_status     = models.CharField(max_length=50, blank=True)   # estado raw del gateway
    # ─────────────────────────────────────────────────────────────────────────

    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Pago #{self.pk} — {self.get_payment_method_display()} — {self.get_status_display()}'


class BankTransferPayment(models.Model):
    """Detalle de pago por transferencia bancaria."""
    payment          = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='bank_transfer')
    bank             = models.CharField(max_length=100)
    reference_number = models.CharField(max_length=100)
    transfer_date    = models.DateField()

    def __str__(self):
        return f'Transferencia {self.bank} — Ref {self.reference_number}'


class CashPayment(models.Model):
    """Detalle de pago en efectivo."""
    payment         = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='cash_payment')
    amount_received = models.DecimalField(max_digits=10, decimal_places=2)
    observations    = models.TextField(blank=True)

    def __str__(self):
        return f'Efectivo recibido: {self.amount_received}'