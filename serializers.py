from rest_framework import serializers
from apps.reviews.models import Review


class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()

    class Meta:
        model  = Review
        fields = ['id', 'user_name', 'rating', 'comment', 'created']
        read_only_fields = ['user_name', 'created']

    def get_user_name(self, obj):
        full_name = f'{obj.user.first_name} {obj.user.last_name}'.strip()
        return full_name or obj.user.email

    def validate_rating(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError('El rating debe ser entre 1 y 5.')
        return value

    def validate(self, data):
        request = self.context['request']
        product = self.context['product']
        if Review.objects.filter(user=request.user, product=product).exists():
            raise serializers.ValidationError('Ya dejaste una reseña para este producto.')
        return data