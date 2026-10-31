from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .api import (
    ActivityPlanViewSet,
    ActivityTypeViewSet,
    CalculatorView,
    ProfileView,
    SupplementIntakeViewSet,
    SupplementViewSet,
    TodayView,
)

router = DefaultRouter()
router.register(r"activity-types", ActivityTypeViewSet)
router.register(r"activities", ActivityPlanViewSet, basename="plan-activity")
router.register(r"supplements", SupplementViewSet, basename="plan-supplement")
router.register(
    r"supplement-intakes", SupplementIntakeViewSet, basename="plan-supplement-intake"
)

urlpatterns = [
    path("profile/", ProfileView.as_view(), name="plan-profile"),
    path("calculator/", CalculatorView.as_view(), name="plan-calculator"),
    path("today/", TodayView.as_view(), name="plan-today"),
    path("", include(router.urls)),
]
