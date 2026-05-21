from django.urls import path
from .views import SimulatePaymentView, PaymentStatusView

urlpatterns = [
    path('simulate/',              SimulatePaymentView.as_view(), name='payment-simulate'),
    path('<int:order_id>/status/', PaymentStatusView.as_view(),  name='payment-status'),
]