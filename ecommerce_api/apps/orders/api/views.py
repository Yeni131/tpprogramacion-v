from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.orders.models import Order
from .serializers import OrderSerializer, OrderCreateSerializer


class OrderListView(generics.ListAPIView):
    """GET /api/orders/ — historial de órdenes del usuario"""
    serializer_class   = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(
            user=self.request.user
        ).prefetch_related('items__product', 'items__variant')


class OrderCreateView(generics.CreateAPIView):
    """POST /api/orders/create/ — crear orden desde carrito"""
    serializer_class   = OrderCreateSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        return Response(
            OrderSerializer(order, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )


class OrderDetailView(generics.RetrieveAPIView):
    """GET /api/orders/<id>/ — detalle de una orden"""
    serializer_class   = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)


class OrderCancelView(generics.UpdateAPIView):
    """PATCH /api/orders/<id>/cancel/ — cancelar orden"""
    serializer_class   = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def patch(self, request, *args, **kwargs):
        order = self.get_object()

        if order.status not in ['pending']:
            return Response(
                {'error': 'Solo podés cancelar órdenes pendientes'},
                status=status.HTTP_400_BAD_REQUEST
            )

        order.status = 'cancelled'
        order.save()
        return Response(OrderSerializer(order).data)