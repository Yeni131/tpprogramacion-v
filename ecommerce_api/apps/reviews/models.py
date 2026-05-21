from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.users.models import User
from apps.products.models import Product


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user    = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating  = models.IntegerField(
                  validators=[MinValueValidator(1), MaxValueValidator(5)]
              )
    comment = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Reseña'
        verbose_name_plural = 'Reseñas'
        unique_together = ('product', 'user')  # 1 reseña por usuario/producto
        ordering = ['-created']

    def __str__(self):
        return f"{self.user.username} → {self.product.name} ({self.rating}★)"