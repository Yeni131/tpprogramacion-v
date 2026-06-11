from rest_framework import serializers
from apps.orders.models import Order, OrderItem, BillingData


class ShippingSerializer(serializers.Serializer):
    email      = serializers.EmailField()
    first_name = serializers.CharField(max_length=100)
    last_name  = serializers.CharField(max_length=100)
    phone      = serializers.CharField(max_length=20)
    address    = serializers.CharField()
    city       = serializers.CharField(max_length=100)
    reference  = serializers.CharField(required=False, allow_blank=True)
    postal_code = serializers.CharField(required=False, allow_blank=True)


class BillingSerializer(serializers.Serializer):
    wants_invoice = serializers.BooleanField(default=False)
    business_name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    ruc           = serializers.CharField(max_length=20,  required=False, allow_blank=True)

    def validate(self, data):
        if data.get('wants_invoice'):
            errors = {}
            if not data.get('business_name'):
                errors['business_name'] = 'Requerido al solicitar factura.'
            if not data.get('ruc'):
                errors['ruc'] = 'Requerido al solicitar factura.'
            if errors:
                raise serializers.ValidationError(errors)
        return data


class PaymentSerializer(serializers.Serializer):
    # ── FIX: Métodos alineados con el frontend ───────────────────────────────
    # Frontend envía: 'efectivo' | 'transferencia' | 'credito' | 'debito'
    METHOD_CHOICES = ['efectivo', 'transferencia', 'credito', 'debito']

    method           = serializers.ChoiceField(choices=METHOD_CHOICES)
    # Campos opcionales para transferencia
    bank             = serializers.CharField(max_length=100, required=False, allow_blank=True)
    reference_number = serializers.CharField(max_length=100, required=False, allow_blank=True)
    transfer_date    = serializers.DateField(required=False, allow_null=True)
    # Campos opcionales para efectivo
    amount_received  = serializers.DecimalField(
                           max_digits=10, decimal_places=2,
                           required=False, allow_null=True
                       )
    observations     = serializers.CharField(required=False, allow_blank=True)


class CheckoutSerializer(serializers.Serializer):
    shipping = ShippingSerializer()
    billing  = BillingSerializer(required=False)
    payment  = PaymentSerializer()


# ── Serializers de lectura ────────────────────────────────────────────────────

class OrderItemReadSerializer(serializers.ModelSerializer):
    product_name  = serializers.CharField(source='product.name', read_only=True)
    product_image = serializers.SerializerMethodField()
    variant_name  = serializers.SerializerMethodField()
    subtotal      = serializers.SerializerMethodField()

    class Meta:
        model  = OrderItem
        fields = [
            'id', 'product_name', 'product_image',
            'variant_name', 'price', 'quantity', 'subtotal',
        ]

    def get_product_image(self, obj):
        request = self.context.get('request')
        image   = obj.product.image
        if not image:
            return None
        if request:
            return request.build_absolute_uri(image.url)
        return image.url

    def get_variant_name(self, obj):
        return str(obj.variant) if obj.variant else None

    def get_subtotal(self, obj):
        return float(obj.price * obj.quantity)


class OrderReadSerializer(serializers.ModelSerializer):
    items       = OrderItemReadSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model  = Order
        fields = [
            'id', 'status', 'total_price', 'discount',
            'first_name', 'last_name', 'email', 'phone',
            'address', 'city', 'wants_invoice', 'created', 'items',
        ]

    def get_total_price(self, obj):
        return float(obj.total_price)