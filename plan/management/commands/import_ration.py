"""Seed the 'Раціон' spreadsheet (plan/fixtures/ration.json) for one user. Re-runnable."""

import json
from datetime import timedelta
from pathlib import Path

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from goals.models import BodyMeasurement
from nutrition.models import (
    Category,
    Diet,
    Ingredient,
    Meal,
    MealIngredient,
    MealPreference,
)
from plan.api import run_calculator
from plan.models import ActivityPlan, ActivityType, Profile, Supplement

FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "ration.json"


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--user", required=True)
        parser.add_argument("--diet-name", default="Раціон")

    @transaction.atomic
    def handle(self, *args, user, diet_name, **opts):
        data = json.loads(FIXTURE.read_text())
        user = User.objects.get(username=user)
        today = timezone.localdate()

        for a in data["activity_types"]:
            ActivityType.objects.update_or_create(name=a.pop("name"), defaults=a)

        ingredients = {}
        for p in data["products"]:
            category, _ = Category.objects.get_or_create(
                name=p["category"], parent=None
            )
            ingredients[p["name"]], _ = Ingredient.objects.update_or_create(
                name=p["name"],
                is_personal=False,
                defaults={
                    "category": category,
                    "proteins": p["proteins"],
                    "fats": p["fats"],
                    "carbs": p["carbs"],
                    "calories": round(
                        4 * p["proteins"] + 9 * p["fats"] + 4 * p["carbs"], 1
                    ),
                },
            )

        for s in data["supplements"]:
            Supplement.objects.update_or_create(
                user=user,
                name=s["name"],
                defaults={"dose": s["dose"], "schedule": s["schedule"]},
            )

        pr = data["profile"]
        profile, _ = Profile.objects.update_or_create(
            user=user,
            defaults={
                "sex": pr["sex"],
                "birth_date": today - timedelta(days=round(pr["age"] * 365.25)),
                "height_cm": pr["height_cm"],
                "target_body_fat_pct": pr["target_body_fat_pct"],
                "deficit_pct": pr["deficit_pct"],
                "steps_per_day": pr["steps_per_day"],
                "answers": pr["answers"],
            },
        )
        profile.activities.all().delete()
        for a in pr["activities"]:
            ActivityPlan.objects.create(
                profile=profile,
                activity_type=ActivityType.objects.get(name=a["name"]),
                hours_per_session=a["hours"],
                times_per_week=a["times_per_week"],
            )
        for metric, value in (
            ("weight_kg", pr["weight_kg"]),
            ("body_fat_percentage", pr["body_fat_pct"]),
        ):
            if not BodyMeasurement.objects.filter(user=user, metric=metric).exists():
                BodyMeasurement.objects.create(
                    user=user,
                    metric=metric,
                    measurement_type="baseline",
                    value=value,
                    timestamp=timezone.now(),
                )
        for name in pr["basket"]:
            MealPreference.objects.get_or_create(
                user=user,
                ingredient=ingredients[name],
                defaults={"preference_type": "like"},
            )

        calc, err = run_calculator(profile)
        if err:
            raise RuntimeError(err)
        diet, _ = Diet.objects.update_or_create(
            user=user,
            name=diet_name,
            defaults={
                "day_calories_kcal": calc["calories_in_kcal"],
                "day_proteins_g": calc["protein_g"],
                "day_fats_g": calc["fat_g"],
                "day_carbohydrates_g": calc["carbs_g"],
                "is_active": True,
            },
        )
        diet.meal_set.all().delete()
        for d, meals in enumerate(data["days"], 1):
            for m, items in enumerate(meals, 1):
                meal = Meal.objects.create(
                    diet=diet, name=f"День {d} · #{m}", plan_day=d, order=m
                )
                MealIngredient.objects.bulk_create(
                    MealIngredient(
                        meal=meal,
                        ingredient=ingredients[i["product"]],
                        quantity=i["grams"],
                        unit="g",
                    )
                    for i in items
                )
        self.stdout.write(
            f"{diet.name}: {calc['calories_in_kcal']} kcal, P{calc['protein_g']} F{calc['fat_g']} C{calc['carbs_g']}; {diet.meal_set.count()} meals"
        )
