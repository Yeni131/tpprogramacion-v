from decimal import Decimal

from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.cart.models import Cart
from apps.orders.models import Order, OrderItem, BillingData
from apps.orders.api.serializers import CheckoutSerializer, OrderReadSerializer
from apps.payments.models import Payment


def _get_user_cart(user):
    return (
        Cart.objects
        .prefetch_related('items__product', 'items__variant')
        .filter(user=user)
        .first()
    )


class CheckoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        cart = _get_user_cart(request.user)
        if not cart or not cart.items.exists():
            return Response(
                {'success': False, 'errors': {'cart': 'El carrito está vacío.'}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = CheckoutSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'success': False, 'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data

        with transaction.atomic():
            cart_items = list(
                cart.items.select_related('product', 'variant').all()
            )

            total = Decimal('0')
            for item in cart_items:
                total += item.get_subtotal()

            shipping = data['shipping']
            billing  = data.get('billing') or {}

            order = Order.objects.create(
                user          = request.user,
                # ── FIX: campos del serializer → campos del modelo ──────────
                first_name    = shipping['first_name'],
                last_name     = shipping['last_name'],
                email         = shipping['email'],
                phone         = shipping['phone'],
                address       = shipping['address'],
                city          = shipping['city'],
                # ────────────────────────────────────────────────────────────
                wants_invoice = billing.get('wants_invoice', False),
                status        = 'pending',
                total_price   = total,
                discount      = Decimal('0'),
            )

            OrderItem.objects.bulk_create([
                OrderItem(
                    order    = order,
                    product  = item.product,
                    variant  = item.variant,
                    price    = item.get_unit_price(),
                    quantity = item.quantity,
                )
                for item in cart_items
            ])

            if billing.get('wants_invoice'):
                BillingData.objects.create(
                    order         = order,
                    business_name = billing.get('business_name', ''),
                    ruc           = billing.get('ruc', ''),
                )

            payment_data = data['payment']

            # ── FIX: mapear métodos del frontend → campo interno ─────────────
            METHOD_MAP = {
                'efectivo':      'cash',
                'transferencia': 'bank_transfer',
                'credito':       'credit_card',
                'debito':        'debit_card',
            }
            internal_method = METHOD_MAP.get(payment_data['method'], payment_data['method'])

            Payment.objects.create(
                order          = order,
                provider       = 'manual',
                status         = 'pending',
                amount         = total,
                payment_method = internal_method,
            )

            # Solo vaciar items, nunca borrar el Cart
            cart.items.all().delete()

        return Response(
            {'success': True, 'order_id': order.pk},
            status=status.HTTP_201_CREATED,
        )


class OrderDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            order = (
                Order.objects
                .prefetch_related('items__product', 'items__variant')
                .get(pk=pk, user=request.user)
            )
        except Order.DoesNotExist:
            return Response(
                {'detail': 'Orden no encontrada.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(OrderReadSerializer(order, context={'request': request}).data)  