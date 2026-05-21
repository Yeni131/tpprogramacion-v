from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from apps.products.models import Category, Product, ProductVariant
from .serializers import (
    CategorySerializer, ProductSerializer,
    ProductListSerializer, ProductVariantSerializer
)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset           = Category.objects.all()
    serializer_class   = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field       = 'slug'


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.filter(available=True).select_related('category').prefetch_related('variants', 'reviews')
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields   = ['category__slug', 'available']
    search_fields      = ['name', 'description']
    ordering_fields    = ['price', 'created']
    lookup_field       = 'slug'

    def get_serializer_class(self):
        if self.action == 'list':
            return ProductListSerializer
        return ProductSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticatedOrReadOnly()]

    @action(detail=True, methods=['get'], url_path='variantes')
    def variantes(self, request, slug=None):
        """GET /api/products/<slug>/variantes/"""
        product  = self.get_object()
        variants = product.variants.all()
        serializer = ProductVariantSerializer(variants, many=True)
        return Response(serializer.data)


class ProductVariantViewSet(viewsets.ModelViewSet):
    queryset           = ProductVariant.objects.select_related('product')
    serializer_class   = ProductVariantSerializer
    permission_classes = [IsAdminUser]