from django.urls import path
from .views import (
    ProductListView,
    ProductDetailView,
    CategoryListView,
    CategoryDetailView,
    ProductVariantListView,
)

urlpatterns = [
    # Productos
    path('',          ProductListView.as_view(),   name='product-list'),
    path('<int:pk>/', ProductDetailView.as_view(), name='product-detail'),

    # Variantes anidadas al producto
    path('<int:pk>/variants/', ProductVariantListView.as_view(), name='product-variants'),

    # Categorías
    path('categories/',          CategoryListView.as_view(),   name='category-list'),
    path('categories/<int:pk>/', CategoryDetailView.as_view(), name='category-detail'),
]