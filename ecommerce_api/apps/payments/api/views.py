from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.orders.models import Order
from apps.payments.models import Payment
from .serializers import PaymentSerializer


class SimulatePaymentView(APIView):
    """POST /api/payments/simulate/ — simula un pago aprobado"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        order_id = request.data.get('order_id')
        provider = request.data.get('provider', 'stripe')  # stripe o mercadopago

        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response({'error': 'Orden no encontrada'}, status=404)

        if order.status != 'pending':
            return Response({'error': 'La orden no está pendiente'}, status=400)

        # Simular pago aprobado
        payment = Payment.objects.create(
            order     = order,
            provider  = provider,
            amount    = order.get_final_total(),
            status    = 'completed',
            stripe_id = f'sim_stripe_{order.id}' if provider == 'stripe' else None,
            mp_id     = f'sim_mp_{order.id}' if provider == 'mercadopago' else None,
        )

        order.status = 'paid'
        order.save()

        return Response({
            'message' : 'Pago simulado exitosamente',
            'payment' : PaymentSerializer(payment).data
        })


class PaymentStatusView(APIView):
    """GET /api/payments/<order_id>/status/"""
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        try:
            order   = Order.objects.get(id=order_id, user=request.user)
            payment = Payment.objects.get(order=order)
            return Response(PaymentSerializer(payment).data)
        except Order.DoesNotExist:
            return Response({'error': 'Orden no encontrada'}, status=404)
        except Payment.DoesNotExist:
            return Response({'error': 'Pago no encontrado'}, status=404)