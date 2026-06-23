from rest_framework import serializers
from apps.cart.models import Cart, CartItem
from apps.products.api.serializers import ProductListSerializer, ProductVariantSerializer


class CartItemSerializer(serializers.ModelSerializer):
    product    = ProductListSerializer(read_only=True)
    variant    = ProductVariantSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    variant_id = serializers.IntegerField(write_only=True, required=False)
    # BUG 8 FIX: float() convierte Decimal → evita NaN potencial en JS
    subtotal   = serializers.SerializerMethodField()

    class Meta:
        model  = CartItem
        fields = [
            'id', 'product', 'product_id',
            'variant', 'variant_id',
            'quantity', 'subtotal',
        ]

    def get_subtotal(self, obj):
        return float(obj.get_subtotal())


class CartSerializer(serializers.ModelSerializer):
    items      = CartItemSerializer(many=True, read_only=True)
    # BUG 8 FIX: float() en total también
    total      = serializers.SerializerMethodField()
    item_count = serializers.SerializerMethodField()

    class Meta:
        model  = Cart
        # BUG 9 FIX: 'created' eliminado — no lo usa el frontend
        fields = ['id', 'items', 'total', 'item_count']

    def get_total(self, obj):
        return float(obj.get_total())

    def get_item_count(self, obj):
        return obj.get_item_count()