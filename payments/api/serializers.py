from rest_framework import serializers
from apps.payments.models import Payment, BankTransferPayment, CashPayment


class BankTransferReadSerializer(serializers.ModelSerializer):
    class Meta:
        model  = BankTransferPayment
        fields = ['bank', 'reference_number', 'transfer_date']


class CashReadSerializer(serializers.ModelSerializer):
    class Meta:
        model  = CashPayment
        fields = ['amount_received', 'observations']


class PaymentReadSerializer(serializers.ModelSerializer):
    bank_transfer = BankTransferReadSerializer(read_only=True)
    cash_payment  = CashReadSerializer(read_only=True)
    method_label  = serializers.CharField(
        source='get_payment_method_display', read_only=True
    )
    status_label  = serializers.CharField(
        source='get_status_display', read_only=True
    )

    class Meta:
        model  = Payment
        fields = [
            'id', 'provider', 'status', 'status_label',
            'payment_method', 'method_label', 'amount',
            'bank_transfer', 'cash_payment', 'created',
        ]