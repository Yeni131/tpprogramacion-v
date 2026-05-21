from rest_framework import serializers
from apps.payments.models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    order_id = serializers.IntegerField(source='order.id', read_only=True)

    class Meta:
        model  = Payment
        fields = [
            'id', 'order_id', 'provider',
            'status', 'amount',
            'stripe_id', 'mp_id',
            'created'
        ]