from rest_framework import serializers

from .models import CategoryNutrition, Product


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"


class CategoryNutritionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryNutrition
        fields = "__all__"
