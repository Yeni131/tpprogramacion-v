from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.coupons.models import Coupon
from .serializers import CouponApplySerializer


class CouponApplyView(APIView):
    """POST /api/coupons/apply/ — validar y aplicar cupón"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CouponApplySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        code = serializer.validated_data['code']

        try:
            coupon = Coupon.objects.get(code=code)
        except Coupon.DoesNotExist:
            return Response({'error': 'Cupón no encontrado'}, status=404)

        if not coupon.is_valid():
            return Response({'error': 'Cupón inválido o expirado'}, status=400)

        # Guardar en sesión para usarlo al crear la orden
        request.session['coupon_id'] = coupon.id

        return Response({
            'message'  : f'Cupón aplicado: {coupon.discount}% de descuento',
            'code'     : coupon.code,
            'discount' : coupon.discount,
        })


class CouponRemoveView(APIView):
    """DELETE /api/coupons/remove/ — quitar cupón de la sesión"""
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        if 'coupon_id' in request.session:
            del request.session['coupon_id']
        return Response({'message': 'Cupón removido'})