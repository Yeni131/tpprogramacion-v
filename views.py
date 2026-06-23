from decimal import Decimal

from django.db import transaction
from django.http import HttpResponse, Http404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.cart.models import Cart
from apps.products.models import Product, ProductVariant
from apps.orders.models import Order, OrderItem, BillingData
from apps.orders.api.serializers import (CheckoutSerializer, OrderReadSerializer,OrderListItemSerializer)
from apps.orders.utils import generate_invoice
from apps.payments.models import Payment
from apps.coupons.models import Coupon

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

        try:
            with transaction.atomic():
                cart_items = list(
                    cart.items.select_related('product', 'variant').all()
                )

                # ── PASO 1: validar stock ANTES de crear nada ────────────
                locked_products = {}
                locked_variants = {}

                for item in cart_items:
                    if item.variant_id:
                        variant = (
                            ProductVariant.objects
                            .select_for_update()
                            .get(pk=item.variant_id)
                        )
                        if variant.stock < item.quantity:
                            return Response(
                                {
                                    'success': False,
                                    'errors': {
                                        'stock': (
                                            f'Stock insuficiente para '
                                            f'"{item.product.name}" '
                                            f'({variant.size or ""} {variant.color or ""}). '
                                            f'Disponible: {variant.stock}, solicitado: {item.quantity}.'
                                        )
                                    },
                                },
                                status=status.HTTP_400_BAD_REQUEST,
                            )
                        locked_variants[item.variant_id] = variant
                    else:
                        product = (
                            Product.objects
                            .select_for_update()
                            .get(pk=item.product_id)
                        )
                        if product.stock < item.quantity:
                            return Response(
                                {
                                    'success': False,
                                    'errors': {
                                        'stock': (
                                            f'Stock insuficiente para '
                                            f'"{product.name}". '
                                            f'Disponible: {product.stock}, solicitado: {item.quantity}.'
                                        )
                                    },
                                },
                                status=status.HTTP_400_BAD_REQUEST,
                            )
                        locked_products[item.product_id] = product

                # ── PASO 2: calcular total ────────────────────────────────
                subtotal = Decimal('0')
                for item in cart_items:
                    subtotal += item.get_subtotal()

                # ── Aplicar cupón guardado en sesión (si existe y sigue válido) ──
                coupon = None
                discount_amount = Decimal('0')
                coupon_id = request.session.get('coupon_id')
                if coupon_id:
                    coupon = Coupon.objects.filter(pk=coupon_id).first()
                    if coupon and coupon.is_valid():
                        discount_amount = (subtotal * coupon.discount / Decimal('100')).quantize(Decimal('0.01'))
                    else:
                        # Cupón vencido/agotado entre que se aplicó y se confirmó la compra
                        coupon = None
                        del request.session['coupon_id']

                total = subtotal - discount_amount

                shipping = data['shipping']
                billing  = data.get('billing') or {}

                # ── PASO 3: crear la orden ─────────────────────────────────
                order = Order.objects.create(
                    user          = request.user,
                    first_name    = shipping['first_name'],
                    last_name     = shipping['last_name'],
                    email         = shipping['email'],
                    phone         = shipping['phone'],
                    address       = shipping['address'],
                    city          = shipping['city'],
                    wants_invoice = billing.get('wants_invoice', False),
                    status        = 'pending',
                    total_price   = total,
                    discount      = discount_amount,
                    coupon        = coupon,
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

                # ── PASO 4: descontar stock ────────────────────────────────
                for item in cart_items:
                    if item.variant_id:
                        variant = locked_variants[item.variant_id]
                        variant.stock -= item.quantity
                        variant.save(update_fields=['stock'])
                    else:
                        product = locked_products[item.product_id]
                        product.stock -= item.quantity
                        product.save(update_fields=['stock'])

                # ── Registrar el uso del cupón (si se aplicó uno) ─────────────
                if coupon:
                    coupon.used_count += 1
                    coupon.save(update_fields=['used_count'])
                    del request.session['coupon_id']

                # ── PASO 5: datos de facturación ────────────────────────────
                if billing.get('wants_invoice'):
                    BillingData.objects.create(
                        order          = order,
                        business_name  = billing.get('business_name', ''),
                        ruc            = billing.get('ruc', ''),
                        fiscal_address = billing.get('fiscal_address', ''),
                    )

                # ── PASO 6: pago ─────────────────────────────────────────────
                payment_data = data['payment']
                METHOD_MAP = {
                    'efectivo':      'cash',
                    'transferencia': 'bank_transfer',
                    'credito':       'credit_card' if 'credit_card' in dict(Payment.METHOD_CHOICES) else 'stripe',
                    'debito':        'debit_card' if 'debit_card' in dict(Payment.METHOD_CHOICES) else 'stripe',
                }
                internal_method = METHOD_MAP.get(payment_data['method'], 'cash')

                Payment.objects.create(
                    order          = order,
                    provider       = 'manual',
                    status         = 'pending',
                    amount         = total,
                    payment_method = internal_method,
                )

                cart.items.all().delete()

        except (Product.DoesNotExist, ProductVariant.DoesNotExist):
            return Response(
                {'success': False, 'errors': {'cart': 'Uno de los productos ya no existe.'}},
                status=status.HTTP_400_BAD_REQUEST,
            )

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

class OrderListAPIView(APIView):
    """
    GET /api/orders/
    Devuelve el historial completo de compras del usuario autenticado,
    ordenado del más reciente al más antiguo (ya viene ordenado así
    por el Meta.ordering del modelo Order).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = (
            Order.objects
            .filter(user=request.user)
            .prefetch_related('items__product', 'items__variant')
        )
        serializer = OrderListItemSerializer(
            orders, many=True, context={'request': request}
        )
        return Response(serializer.data)

class InvoiceDownloadAPIView(APIView):
    """
    GET /api/orders/<pk>/invoice/
    Genera y devuelve el PDF de la factura/comprobante de la orden.
    Solo accesible por el dueño de la orden.

    FIX: esta clase tenía un segundo método get() duplicado pegado por
    error debajo (copiado de OrderDetailAPIView). En Python, cuando dos
    métodos con el mismo nombre quedan definidos en la misma clase, el
    segundo sobrescribe al primero — por eso esta vista terminaba
    devolviendo el JSON de la orden en vez del PDF. Se eliminó el bloque
    duplicado; ahora la clase tiene un solo método get().
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            order = (
                Order.objects
                .select_related('user', 'coupon')
                .prefetch_related('items__product', 'items__variant')
                .get(pk=pk, user=request.user)
            )
        except Order.DoesNotExist:
            raise Http404('Orden no encontrada.')

        pdf_bytes = generate_invoice(order)

        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="factura_orden_{order.pk}.pdf"'
        return response