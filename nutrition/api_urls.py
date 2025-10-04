from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import (
    DietViewSet, MealViewSet, IngredientViewSet, CategoryViewSet,
    MealRecordViewSet, MealPreferenceViewSet, MealIngredientViewSet
)

router = DefaultRouter()
router.register(r'diets', DietViewSet)
router.register(r'meals', MealViewSet)
router.register(r'ingredients', IngredientViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'records', MealRecordViewSet)
router.register(r'preferences', MealPreferenceViewSet)
router.register(r'meal-ingredients', MealIngredientViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
