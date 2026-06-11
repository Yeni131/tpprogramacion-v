from django.urls import path

from apps.payments.api.views import PaymentDetailAPIView


urlpatterns = [
     path('order/<int:order_pk>/', PaymentDetailAPIView.as_view(), name='api-payment-detail'),
]