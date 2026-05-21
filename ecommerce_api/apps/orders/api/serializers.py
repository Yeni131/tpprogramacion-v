from rest_framework import serializers
from apps.orders.models import Order, OrderItem
from apps.products.api.serializers import ProductListSerializer, ProductVariantSerializer


class OrderItemSerializer(serializers.ModelSerializer):
    product  = ProductListSerializer(read_only=True)
    variant  = ProductVariantSerializer(read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model  = OrderItem
        fields = ['id', 'product', 'variant', 'price', 'quantity', 'subtotal']

    def get_subtotal(self, obj):
        return obj.get_subtotal()


class OrderSerializer(serializers.ModelSerializer):
    items       = OrderItemSerializer(many=True, read_only=True)
    final_total = serializers.SerializerMethodField()
    user        = serializers.StringRelatedField(read_only=True)
    coupon_code = serializers.CharField(source='coupon.code', read_only=True)

    class Meta:
        model  = Order
        fields = [
            'id', 'user', 'status',
            'total_price', 'discount', 'final_total',
            'coupon_code', 'address',
            'items', 'created', 'updated'
        ]

    def get_final_total(self, obj):
        return obj.get_final_total()


class OrderCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear una orden desde el carrito"""

    class Meta:
        model  = Order
        fields = ['address']

    def create(self, validated_data):
        request = self.context['request']
        user    = request.user

        # Obtener carrito del usuario
        from apps.cart.models import Cart
        try:
            cart = Cart.objects.get(user=user)
        except Cart.DoesNotExist:
            raise serializers.ValidationError('No tenés un carrito activo')

        if not cart.items.exists():
            raise serializers.ValidationError('El carrito está vacío')

        # Calcular total
        total = cart.get_total()

        # Aplicar cupón si existe en sesión
        discount   = 0
        coupon     = None
        coupon_id  = request.session.get('coupon_id')
        if coupon_id:
            from apps.coupons.models import Coupon
            try:
                coupon   = Coupon.objects.get(id=coupon_id, active=True)
                discount = round(total * coupon.discount / 100, 2)
                coupon.used_count += 1
                coupon.save()
            except Coupon.DoesNotExist:
                pass

        # Crear la orden
        order = Order.objects.create(
            user        = user,
            address     = validated_data['address'],
            total_price = total,
            discount    = discount,
            coupon      = coupon,
            status      = 'pending'
        )

        # Crear los items de la orden desde el carrito
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order    = order,
                product  = cart_item.product,
                variant  = cart_item.variant,
                price    = cart_item.get_unit_price(),
                quantity = cart_item.quantity
            )

        # Vaciar carrito y sesión de cupón
        cart.items.all().delete()
        if 'coupon_id' in request.session:
            del request.session['coupon_id']

        return order