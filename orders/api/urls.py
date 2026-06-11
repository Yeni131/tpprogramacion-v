from django.urls import path
from apps.orders.api.views import CheckoutAPIView, OrderDetailAPIView

urlpatterns = [
    path('checkout/',    CheckoutAPIView.as_view(),     name='api-checkout'),
    path('<int:pk>/',    OrderDetailAPIView.as_view(),  name='api-order-detail'),
]