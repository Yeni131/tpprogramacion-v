from django.urls import path
from apps.orders.api.views import (
    CheckoutAPIView,
    OrderDetailAPIView,
    OrderListAPIView,
    InvoiceDownloadAPIView,
)

urlpatterns = [
    path('checkout/',        CheckoutAPIView.as_view(),       name='api-checkout'),
    path('',          OrderListAPIView.as_view(), name='api-order-list'),
    path('<int:pk>/',        OrderDetailAPIView.as_view(),    name='api-order-detail'),
    path('<int:pk>/invoice/', InvoiceDownloadAPIView.as_view(), name='api-order-invoice'),
]