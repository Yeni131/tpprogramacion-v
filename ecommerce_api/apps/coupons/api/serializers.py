from rest_framework import serializers
from apps.coupons.models import Coupon


class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Coupon
        fields = ['id', 'code', 'discount', 'valid_from', 'valid_to']


class CouponApplySerializer(serializers.Serializer):
    code = serializers.CharField(max_length=50)