from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from apps.payments.models import Payment
from apps.payments.api.serializers import PaymentReadSerializer


class PaymentDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, order_pk):
        try:
            payment = Payment.objects.select_related(
                'bank_transfer', 'cash_payment'
            ).get(order__pk=order_pk, order__user=request.user)
        except Payment.DoesNotExist:
            return Response(
                {'detail': 'Pago no encontrado.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(PaymentReadSerializer(payment).data)