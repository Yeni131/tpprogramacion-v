from django.db import transaction
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from apps.cart.models import Cart, CartItem
from apps.products.models import Product, ProductVariant
from .serializers import CartSerializer


# ── helper de prefetch ─────────────────────────────────────────────────────
def _cart_qs(pk):
    """Devuelve el carrito con todos los items prefetcheados (evita N+1)."""
    return (
        Cart.objects
        .prefetch_related('items__product', 'items__variant')
        .get(pk=pk)
    )


def get_or_create_cart(request):
    """
    Obtiene o crea el carrito.
    - Usuario autenticado → carrito por user.
    - Anónimo            → carrito por session_key.
    - Login              → fusiona carrito de sesión en carrito de usuario
                           dentro de una transacción atómica para evitar
                           duplicados si la operación se interrumpe.
    """
    if request.user.is_authenticated:
        # BUG 5 FIX: filter().first() evita MultipleObjectsReturned
        user_cart = Cart.objects.filter(user=request.user).first()
        if not user_cart:
            user_cart = Cart.objects.create(user=request.user)

        # BUG 2 FIX: fusión dentro de atomic() + select_for_update()
        session_key = request.session.session_key
        if session_key:
            try:
                session_cart = Cart.objects.get(session_key=session_key, user=None)
                with transaction.atomic():
                    for item in session_cart.items.select_for_update().all():
                        existing = user_cart.items.filter(
                            product=item.product,
                            variant=item.variant
                        ).first()
                        if existing:
                            existing.quantity += item.quantity
                            existing.save()
                        else:
                            item.cart = user_cart
                            item.save()
                    session_cart.delete()
            except Cart.DoesNotExist:
                pass

        return user_cart

    else:
        if not request.session.session_key:
            request.session.create()
        cart, _ = Cart.objects.get_or_create(
            session_key=request.session.session_key,
            user=None
        )
        return cart


class CartDetailView(APIView):
    """GET /api/cart/"""
    permission_classes = [AllowAny]

    def get(self, request):
        cart = get_or_create_cart(request)
        serializer = CartSerializer(_cart_qs(cart.pk))
        return Response(serializer.data)


class CartAddView(APIView):
    """POST /api/cart/add/"""
    permission_classes = [AllowAny]

    def post(self, request):
        # BUG 4 FIX: validar product_id antes de hacer .get()
        product_id = request.data.get('product_id')
        if not product_id:
            return Response({'error': 'product_id requerido'}, status=400)

        variant_id = request.data.get('variant_id')

        try:
            quantity = int(request.data.get('quantity', 1))
            if quantity < 1:
                return Response({'error': 'quantity debe ser >= 1'}, status=400)
        except (ValueError, TypeError):
            return Response({'error': 'quantity inválido'}, status=400)

        try:
            product = Product.objects.get(id=product_id, available=True)
        except Product.DoesNotExist:
            return Response({'error': 'Producto no encontrado'}, status=404)

        variant = None
        if variant_id:
            try:
                variant = ProductVariant.objects.get(id=variant_id, product=product)
            except ProductVariant.DoesNotExist:
                return Response({'error': 'Variante no encontrada'}, status=404)

        cart = get_or_create_cart(request)

        item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            variant=variant,
            defaults={'quantity': quantity}
        )
        if not created:
            item.quantity += quantity
            item.save()

        serializer = CartSerializer(_cart_qs(cart.pk))
        return Response(serializer.data, status=status.HTTP_200_OK)


class CartUpdateView(APIView):
    """PATCH /api/cart/update/<item_id>/"""
    permission_classes = [AllowAny]

    def patch(self, request, item_id):
        try:
            quantity = int(request.data.get('quantity', 1))
        except (ValueError, TypeError):
            return Response({'error': 'quantity inválido'}, status=400)

        cart = get_or_create_cart(request)

        try:
            # BUG 6 FIX: select_for_update evita race condition en clicks rápidos
            item = CartItem.objects.select_for_update().get(id=item_id, cart=cart)
        except CartItem.DoesNotExist:
            return Response({'error': 'Item no encontrado'}, status=404)

        # BUG 1 FIX: siempre devolver CartSerializer completo
        if quantity <= 0:
            item.delete()
        else:
            item.quantity = quantity
            item.save()

        serializer = CartSerializer(_cart_qs(cart.pk))
        return Response(serializer.data)


class CartRemoveView(APIView):
    """DELETE /api/cart/remove/<item_id>/"""
    permission_classes = [AllowAny]

    def delete(self, request, item_id):
        cart = get_or_create_cart(request)
        try:
            item = CartItem.objects.get(id=item_id, cart=cart)
            item.delete()
            serializer = CartSerializer(_cart_qs(cart.pk))
            return Response(serializer.data)
        except CartItem.DoesNotExist:
            return Response({'error': 'Item no encontrado'}, status=404)


class CartClearView(APIView):
    """DELETE /api/cart/clear/"""
    permission_classes = [AllowAny]

    def delete(self, request):
        cart = get_or_create_cart(request)
        cart.items.all().delete()
        serializer = CartSerializer(_cart_qs(cart.pk))
        return Response(serializer.data)