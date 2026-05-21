from rest_framework import serializers
from apps.reviews.models import Review


class ReviewSerializer(serializers.ModelSerializer):
    user     = serializers.StringRelatedField(read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model  = Review
        fields = ['id', 'user', 'username', 'rating', 'comment', 'created']
        read_only_fields = ['user', 'created']

    def validate_rating(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError('El rating debe ser entre 1 y 5')
        return value

    def validate(self, data):
        request    = self.context['request']
        product    = self.context['product']
        if Review.objects.filter(user=request.user, product=product).exists():
            raise serializers.ValidationError('Ya dejaste una reseña para este producto')
        return data