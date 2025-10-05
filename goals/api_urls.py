from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .api import BodyMeasurementViewSet, GoalViewSet

router = DefaultRouter()
router.register(r"goals", GoalViewSet)
router.register(r"measurements", BodyMeasurementViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
