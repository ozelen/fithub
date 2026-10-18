from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .api import CategoryView, ProductViewSet

router = DefaultRouter()
router.register(r"products", ProductViewSet, basename="facts-product")

urlpatterns = [
    path("categories/<str:tag>/", CategoryView.as_view(), name="facts-category"),
    path("", include(router.urls)),
]
