from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from apps.reviews.models import Review
from apps.products.models import Product
from .serializers import ReviewSerializer


class ReviewListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/reviews/<product_slug>/  — ver reseñas del producto
    POST /api/reviews/<product_slug>/  — crear reseña
    """
    serializer_class   = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_product(self):
        return Product.objects.get(slug=self.kwargs['product_slug'])

    def get_queryset(self):
        return Review.objects.filter(
            product__slug=self.kwargs['product_slug']
        ).select_related('user')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['product'] = self.get_product()
        return context

    def perform_create(self, serializer):
        serializer.save(
            user    = self.request.user,
            product = self.get_product()
        )

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        product = self.get_product()
        return Response({
            'product'        : product.name,
            'average_rating' : product.get_average_rating(),
            'total_reviews'  : queryset.count(),
            'reviews'        : serializer.data
        })


class ReviewDeleteView(generics.DestroyAPIView):
    """DELETE /api/reviews/<product_slug>/<review_id>/ — borrar reseña propia"""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Review.objects.filter(user=self.request.user)