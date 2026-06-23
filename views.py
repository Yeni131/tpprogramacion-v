
from django.db import models
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from apps.coupons.models import Coupon
from .serializers import CouponApplySerializer, CouponSerializer


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

class CouponListView(APIView):
    """
    GET /api/coupons/active/
    Devuelve los cupones actualmente vigentes y con cupos disponibles,
    para mostrarlos públicamente en la página de Ofertas.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        now = timezone.now()
        coupons = Coupon.objects.filter(
            active=True,
            valid_from__lte=now,
            valid_to__gte=now,
            used_count__lt=models.F('max_uses'),
        ).order_by('valid_to')

        serializer = CouponSerializer(coupons, many=True)
        return Response(serializer.data)