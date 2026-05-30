from django.db import models
from django.utils.text import slugify
from apps.users.models import User


class Category(models.Model):
    name  = models.CharField(max_length=200)
    slug  = models.SlugField(unique=True, blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    category    = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    name        = models.CharField(max_length=200)
    slug        = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    price       = models.DecimalField(max_digits=10, decimal_places=2)
    stock       = models.PositiveIntegerField(default=0)
    image       = models.ImageField(upload_to='products/', blank=True, null=True)
    available   = models.BooleanField(default=True)
    created     = models.DateTimeField(auto_now_add=True)
    updated     = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['-created']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_average_rating(self):
        reviews = self.reviews.all()
        if reviews.exists():
            return round(sum(r.rating for r in reviews) / reviews.count(), 1)
        return 0

    def __str__(self):
        return self.name


class ProductVariant(models.Model):
    SIZE_CHOICES = [('XS','XS'),('S','S'),('M','M'),('L','L'),('XL','XL'),('XXL','XXL')]

    product     = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    size        = models.CharField(max_length=10, choices=SIZE_CHOICES, blank=True)
    color       = models.CharField(max_length=50, blank=True)
    stock       = models.PositiveIntegerField(default=0)
    extra_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    class Meta:
        verbose_name = 'Variante'
        verbose_name_plural = 'Variantes'
        unique_together = ('product', 'size', 'color')

    def get_final_price(self):
        return self.product.price + self.extra_price

    def __str__(self):
        return f"{self.product.name} — {self.size} / {self.color}"