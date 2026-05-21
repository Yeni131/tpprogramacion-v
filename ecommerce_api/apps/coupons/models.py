from django.db import models
from django.utils import timezone


class Coupon(models.Model):
    code       = models.CharField(max_length=50, unique=True)
    discount   = models.DecimalField(max_digits=5, decimal_places=2,
                     help_text='Porcentaje: 10.00 = 10%')
    active     = models.BooleanField(default=True)
    valid_from = models.DateTimeField()
    valid_to   = models.DateTimeField()
    max_uses   = models.PositiveIntegerField(default=100)
    used_count = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Cupón'
        verbose_name_plural = 'Cupones'

    def is_valid(self):
        now = timezone.now()
        return (
            self.active
            and self.valid_from <= now <= self.valid_to
            and self.used_count < self.max_uses
        )

    def __str__(self):
        return f"{self.code} ({self.discount}%)"