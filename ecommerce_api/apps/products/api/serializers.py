from rest_framework import serializers
from apps.products.models import Category, Product, ProductVariant


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model  = Category
        fields = ['id', 'name', 'slug', 'image']


class ProductVariantSerializer(serializers.ModelSerializer):
    final_price = serializers.SerializerMethodField()

    class Meta:
        model  = ProductVariant
        fields = ['id', 'size', 'color', 'stock', 'extra_price', 'final_price']

    def get_final_price(self, obj):
        return obj.get_final_price()


class ProductSerializer(serializers.ModelSerializer):
    category        = CategorySerializer(read_only=True)
    category_id     = serializers.PrimaryKeyRelatedField(
                          queryset=Category.objects.all(),
                          source='category',
                          write_only=True
                      )
    variants        = ProductVariantSerializer(many=True, read_only=True)
    average_rating  = serializers.SerializerMethodField()

    class Meta:
        model  = Product
        fields = [
            'id', 'name', 'slug', 'description',
            'price', 'stock', 'image', 'available',
            'category', 'category_id',
            'variants', 'average_rating',
            'created', 'updated',
        ]

    def get_average_rating(self, obj):
        return obj.get_average_rating()


class ProductListSerializer(serializers.ModelSerializer):
    """Serializer liviano para listas — sin variantes ni reviews"""
    category_name  = serializers.CharField(source='category.name', read_only=True)
    average_rating = serializers.SerializerMethodField()

    class Meta:
        model  = Product
        fields = ['id', 'name', 'slug', 'price', 'image',
                  'available', 'stock', 'category_name', 'average_rating']

    def get_average_rating(self, obj):
        return obj.get_average_rating()