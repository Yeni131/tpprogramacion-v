from rest_framework import generics, filters
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from apps.products.models import Category, Product, ProductVariant
from .serializers import (
    CategorySerializer,
    ProductSerializer,
    ProductListSerializer,
    ProductVariantSerializer,
)


class ProductListView(generics.ListCreateAPIView):
    """
    GET  /api/products/       → lista paginada con filtros y búsqueda
    POST /api/products/       → crear producto (solo admin)
    """
    queryset = (
        Product.objects
        .filter(available=True)
        .select_related('category')
        .prefetch_related('variants', 'reviews')
    )
    filter_backends  = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category__slug', 'available']
    search_fields    = ['name', 'description']
    ordering_fields  = ['price', 'created']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ProductSerializer
        return ProductListSerializer
    

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdminUser()]
        return [IsAuthenticatedOrReadOnly()]


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/products/<pk>/   → detalle completo
    PUT    /api/products/<pk>/   → actualizar (solo admin)
    PATCH  /api/products/<pk>/   → actualizar parcial (solo admin)
    DELETE /api/products/<pk>/   → eliminar (solo admin)
    """
    queryset = (
        Product.objects
        .select_related('category')
        .prefetch_related('variants', 'reviews')
    )
    serializer_class = ProductSerializer

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH', 'DELETE'):
            return [IsAdminUser()]
        return [IsAuthenticatedOrReadOnly()]


class ProductVariantListView(generics.ListCreateAPIView):
    """
    GET  /api/products/<pk>/variants/   → variantes del producto
    POST /api/products/<pk>/variants/   → crear variante (solo admin)
    """
    serializer_class   = ProductVariantSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return ProductVariant.objects.filter(product_id=self.kwargs['pk'])

    def perform_create(self, serializer):
        product = generics.get_object_or_404(Product, pk=self.kwargs['pk'])
        serializer.save(product=product)


class CategoryListView(generics.ListCreateAPIView):
    """
    GET  /api/products/categories/   → todas las categorías
    POST /api/products/categories/   → crear (solo admin)
    """
    queryset           = Category.objects.all()
    serializer_class   = CategorySerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdminUser()]
        return [IsAuthenticatedOrReadOnly()]


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/products/categories/<pk>/
    PUT    /api/products/categories/<pk>/
    DELETE /api/products/categories/<pk>/
    """
    queryset           = Category.objects.all()
    serializer_class   = CategorySerializer

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH', 'DELETE'):
            return [IsAdminUser()]
        return [IsAuthenticatedOrReadOnly()]