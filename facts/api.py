from django.contrib.postgres.search import TrigramSimilarity
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Category, CategoryNutrition, Product
from .serializers import CategoryNutritionSerializer, ProductSerializer


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """Open Food Facts products. `?q=` fuzzy name, `?category=en:basmati-rices`, `?country=en:spain`; `/{barcode}/` by code."""

    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        p = self.request.query_params
        qs = Product.objects.filter(obsolete=False)
        if p.get("category"):
            qs = qs.filter(categories_tags__contains=[p["category"]])
        if p.get("country"):
            qs = qs.filter(countries_tags__contains=[p["country"]])
        if p.get("q"):
            qs = qs.filter(name__trigram_similar=p["q"]).annotate(sim=TrigramSimilarity("name", p["q"]))
            return qs.order_by("-sim", "-completeness")
        return qs.order_by("-completeness", "code")


class CategoryView(APIView):
    """A generic product: taxonomy names and parents, median nutrients, and the most complete examples."""

    permission_classes = [IsAuthenticated]

    def get(self, request, tag):
        cat = Category.objects.filter(tag=tag).first()
        median = CategoryNutrition.objects.filter(tag=tag).first()
        examples = Product.objects.filter(categories_tags__contains=[tag], obsolete=False).order_by("-completeness")[:5]
        return Response(
            {
                "tag": tag,
                "names": cat.names if cat else {},
                "parents": cat.parents if cat else [],
                "median": CategoryNutritionSerializer(median).data if median else None,
                "examples": ProductSerializer(examples, many=True).data,
            }
        )
