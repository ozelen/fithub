from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from goals.models import BodyMeasurement
from nutrition.models import Diet, MealRecord

from .calculator import ACTIVITY_FIELDS, calculate
from .models import ActivityPlan, ActivityType, Profile, Supplement, SupplementIntake
from .serializers import (
    ActivityPlanSerializer,
    ActivityTypeSerializer,
    ProfileSerializer,
    SupplementIntakeSerializer,
    SupplementSerializer,
)


def latest_measurement(user, metric):
    m = (
        BodyMeasurement.objects.filter(user=user, metric=metric)
        .exclude(measurement_type="target")
        .order_by("-timestamp")
        .first()
    )
    return m.value if m else None


def age_on(birth_date, today):
    return (
        today.year
        - birth_date.year
        - ((today.month, today.day) < (birth_date.month, birth_date.day))
    )


def run_calculator(profile, weight_kg=None, body_fat_pct=None):
    user = profile.user
    weight_kg = weight_kg or latest_measurement(user, "weight_kg")
    body_fat_pct = body_fat_pct or latest_measurement(user, "body_fat_percentage")
    if weight_kg is None:
        return None, "No weight: log a weight_kg measurement first"
    acts = [
        (
            a.activity_type.met,
            a.activity_type.protein_g_per_kg,
            a.activity_type.fat_g_per_kg,
            a.hours_per_session,
            a.times_per_week,
        )
        for a in profile.activities.select_related("activity_type")
    ]
    result = calculate(
        sex=profile.sex,
        age=age_on(profile.birth_date, timezone.localdate()),
        weight_kg=weight_kg,
        height_cm=profile.height_cm,
        body_fat_pct=body_fat_pct,
        target_body_fat_pct=profile.target_body_fat_pct,
        target_weight_kg=profile.target_weight_kg,
        deficit_pct=profile.deficit_pct,
        steps_per_day=profile.steps_per_day,
        activities=acts,
    )
    result["inputs"] = {
        "weight_kg": weight_kg,
        "body_fat_pct": body_fat_pct,
        "activities": [dict(zip(ACTIVITY_FIELDS, a)) for a in acts],
    }
    return result, None


@extend_schema(tags=["Plan"])
class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            ProfileSerializer(get_object_or_404(Profile, user=request.user)).data
        )

    def put(self, request):
        s = ProfileSerializer(
            Profile.objects.filter(user=request.user).first(), data=request.data
        )
        s.is_valid(raise_exception=True)
        s.save(user=request.user)
        return Response(s.data)


@extend_schema(tags=["Plan"])
class CalculatorView(APIView):
    """Spreadsheet calculator over the profile and latest measurements. `?weight=&bf=` override."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = get_object_or_404(Profile, user=request.user)
        p = request.query_params
        result, err = run_calculator(
            profile,
            p.get("weight") and float(p["weight"]),
            p.get("bf") and float(p["bf"]),
        )
        return Response(result or {"error": err}, status=200 if result else 400)


def today_template(diet, today):
    """ponytail: templates rotate by day index since the diet started; weekday rules if ever needed."""
    days = sorted({d for d in diet.meal_set.values_list("plan_day", flat=True) if d})
    if not days:
        return None
    return days[(today - diet.start_date).days % len(days)]


@extend_schema(tags=["Plan"])
class TodayView(APIView):
    """Planned meals vs eaten vs targets, supplements with intake state, activities for today."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        today = timezone.localdate()
        diet = Diet.objects.filter(user=user, is_active=True).first()
        plan_day = today_template(diet, today) if diet else None
        meals = (
            diet.meal_set.filter(plan_day=plan_day).order_by("order")
            if plan_day
            else []
        )
        records = MealRecord.objects.filter(user=user, timestamp__date=today)
        eaten = {
            "calories": round(sum(r.get_total_calories() for r in records), 1),
            "proteins": round(sum(r.get_total_proteins() for r in records), 1),
            "fats": round(sum(r.get_total_fats() for r in records), 1),
            "carbs": round(sum(r.get_total_carbs() for r in records), 1),
        }
        recorded_meal_ids = set(records.values_list("meal_id", flat=True))
        intakes = SupplementIntake.objects.filter(
            supplement__user=user, taken_at__date=today
        )
        taken = {}
        for i in intakes:
            taken[i.supplement_id] = taken.get(i.supplement_id, 0) + i.qty
        profile = Profile.objects.filter(user=user).first()
        # Targets follow the user's own profile and latest weight; the diet's stored numbers are the fallback.
        calc = run_calculator(profile)[0] if profile else None
        targets = (
            {
                "calories": calc["calories_in_kcal"],
                "proteins": calc["protein_g"],
                "fats": calc["fat_g"],
                "carbs": calc["carbs_g"],
                "warning": calc["warning"],
            }
            if calc
            else diet
            and {
                "calories": diet.day_calories_kcal,
                "proteins": diet.day_proteins_g,
                "fats": diet.day_fats_g,
                "carbs": diet.day_carbohydrates_g,
                "warning": None,
            }
        )
        return Response(
            {
                "date": today,
                "diet": diet
                and {"id": diet.id, "name": diet.name, "plan_day": plan_day},
                "targets": targets,
                "meals": [
                    {
                        "id": m.id,
                        "order": m.order,
                        "name": m.name,
                        "start_time": m.start_time,
                        "eaten": m.id in recorded_meal_ids,
                        "items": [
                            {"ingredient": mi.ingredient.name, "grams": mi.quantity}
                            for mi in m.mealingredient_set.select_related("ingredient")
                        ],
                        **m.macros(),
                    }
                    for m in meals
                ],
                "eaten": eaten,
                "supplements": [
                    {
                        "id": s.id,
                        "name": s.name,
                        "dose": s.dose,
                        "schedule": s.schedule,
                        "taken_qty": taken.get(s.id, 0),
                    }
                    for s in Supplement.objects.filter(user=user, is_active=True)
                ],
                "activities": ActivityPlanSerializer(
                    profile.activities.select_related("activity_type"), many=True
                ).data
                if profile
                else [],
            }
        )


@extend_schema(tags=["Plan"])
class ActivityTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ActivityType.objects.all()
    serializer_class = ActivityTypeSerializer
    permission_classes = [IsAuthenticated]


@extend_schema(tags=["Plan"])
class ActivityPlanViewSet(viewsets.ModelViewSet):
    serializer_class = ActivityPlanSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ActivityPlan.objects.filter(
            profile__user=self.request.user
        ).select_related("activity_type")

    def perform_create(self, serializer):
        serializer.save(profile=get_object_or_404(Profile, user=self.request.user))


@extend_schema(tags=["Plan"])
class SupplementViewSet(viewsets.ModelViewSet):
    serializer_class = SupplementSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Supplement.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@extend_schema(tags=["Plan"])
class SupplementIntakeViewSet(viewsets.ModelViewSet):
    serializer_class = SupplementIntakeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SupplementIntake.objects.filter(supplement__user=self.request.user)
