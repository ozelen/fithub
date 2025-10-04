from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import GoalViewSet, BodyMeasurementViewSet

router = DefaultRouter()
router.register(r'goals', GoalViewSet)
router.register(r'measurements', BodyMeasurementViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
