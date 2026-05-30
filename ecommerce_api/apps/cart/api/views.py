from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from apps.cart.models import Cart, CartItem
from apps.products.models import Product, ProductVariant
from .serializers import CartSerializer, CartItemSerializer


def get_or_create_cart(request):
    """Obtiene o crea el carrito — por usuario o por sesión"""
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
    else:
        if not request.session.session_key:
            request.session.create()
        cart, _ = Cart.objects.get_or_create(
            session_key=request.session.session_key,
            user=None
        )
    return cart


class CartDetailView(APIView):
    """GET /api/cart/ — ver carrito actual"""
    permission_classes = [AllowAny]

    def get(self, request):
        cart = get_or_create_cart(request)
        serializer = CartSerializer(cart)
        return Response(serializer.data)


class CartAddView(APIView):
    """POST /api/cart/add/ — agregar producto"""
    permission_classes = [AllowAny]

    def post(self, request):
        cart       = get_or_create_cart(request)
        product_id = request.data.get('product_id')
        variant_id = request.data.get('variant_id')
        quantity   = int(request.data.get('quantity', 1))

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

        # Si ya existe el item, suma la cantidad
        item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            variant=variant,
            defaults={'quantity': quantity}
        )
        if not created:
            item.quantity += quantity
            item.save()

        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CartRemoveView(APIView):
    """DELETE /api/cart/remove/<item_id>/ — quitar item"""
    permission_classes = [AllowAny]

    def delete(self, request, item_id):
        cart = get_or_create_cart(request)
        try:
            item = CartItem.objects.get(id=item_id, cart=cart)
            item.delete()
            serializer = CartSerializer(cart)
            return Response(serializer.data)
        except CartItem.DoesNotExist:
            return Response({'error': 'Item no encontrado'}, status=404)


class CartUpdateView(APIView):
    """PATCH /api/cart/update/<item_id>/ — cambiar cantidad"""
    permission_classes = [AllowAny]

    def patch(self, request, item_id):
        cart     = get_or_create_cart(request)
        quantity = int(request.data.get('quantity', 1))

        try:
            item = CartItem.objects.get(id=item_id, cart=cart)
        except CartItem.DoesNotExist:
            return Response({'error': 'Item no encontrado'}, status=404)

        if quantity <= 0:
            item.delete()
            return Response({'message': 'Item eliminado'})

        item.quantity = quantity
        item.save()
        serializer = CartSerializer(cart)
        return Response(serializer.data)


class CartClearView(APIView):
    """DELETE /api/cart/clear/ — vaciar carrito"""
    permission_classes = [AllowAny]

    def delete(self, request):
        cart = get_or_create_cart(request)
        cart.items.all().delete()
        serializer = CartSerializer(cart)
        return Response(serializer.data)