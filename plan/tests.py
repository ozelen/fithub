import pytest
from django.contrib.auth.models import User
from django.core.management import call_command
from rest_framework.test import APIClient

from nutrition.models import Diet, Ingredient
from plan.calculator import calculate
from plan.models import ActivityType, Supplement

SHEET = dict(
    sex="male",
    age=41,
    weight_kg=97,
    height_cm=192,
    body_fat_pct=20,
    target_body_fat_pct=12,
    deficit_pct=-30,
)
# the sheet counted both sessions every day (frequency blank): times_per_week=7 reproduces its numbers
ACTS = [(3.0, 2.0, 1.0, 1.38, 7), (7.4, 2.0, 1.0, 1.93, 7)]


def test_calculator_matches_sheet():
    r = calculate(**SHEET, activities=ACTS)
    assert (r["lbm_kg"], r["bmr_kcal"], r["tdee_kcal"]) == (77.6, 2046.16, 4037.71)
    assert r["calories_in_kcal"] == 2826.4
    assert (r["protein_g"], r["fat_g"], r["carbs_g"]) == (155, 78, 376)
    assert (r["excess_kg"], r["kg_per_week"], r["weeks"]) == (8.82, 1.1, 8)
    assert r["warning"] is None


def test_calculator_guards_and_mifflin():
    r = calculate(sex="female", age=30, weight_kg=60, height_cm=165, deficit_pct=-30)
    assert r["bmr_kcal"] == 10 * 60 + 6.25 * 165 - 150 - 161
    assert r["warning"] and r["lbm_kg"] is None and r["protein_g"] == 90


@pytest.mark.django_db
def test_import_ration_and_today():
    user = User.objects.create_user("oleksiy", password="x")
    call_command("import_ration", user="oleksiy")
    call_command("import_ration", user="oleksiy")  # idempotent
    assert ActivityType.objects.count() == 24
    assert Ingredient.objects.count() == 126
    assert Supplement.objects.filter(user=user).count() == 7
    diet = Diet.objects.get(user=user, is_active=True)
    assert diet.meal_set.count() == 20
    day1 = sum(m.macros()["proteins"] for m in diet.meal_set.filter(plan_day=1))
    assert abs(day1 - 163.18) < 0.5  # Тиждень!D7
    assert (diet.day_proteins_g, diet.day_fats_g) == (155, 78)

    client = APIClient()
    client.force_authenticate(user)
    today = client.get("/api/plan/today/").json()
    assert today["diet"]["plan_day"] == 1 and len(today["meals"]) == 4
    assert today["meals"][0]["items"][0] == {"ingredient": "Кус Кус", "grams": 130.0}
    assert len(today["supplements"]) == 7
    calc = client.get("/api/plan/calculator/").json()
    assert calc["tdee_kcal"] < 3100  # 3x/week, not daily
    assert today["targets"]["calories"] == calc["calories_in_kcal"]

    # targets are per user: a new measurement moves them without touching the diet
    for kind, value in (("log", 90), ("target", 80)):  # a target is not a current weight
        body = {"metric": "weight_kg", "measurement_type": kind, "value": value, "timestamp": "2100-01-01T00:00:00Z"}
        assert client.post("/api/goals/measurements/", body).status_code == 201
    lighter = client.get("/api/plan/today/").json()["targets"]
    assert lighter["calories"] < today["targets"]["calories"]
    assert client.get("/api/plan/calculator/").json()["inputs"]["weight_kg"] == 90
    newcomer = APIClient()
    newcomer.force_authenticate(User.objects.create_user("friend"))
    assert newcomer.get("/api/plan/today/").json()["targets"] is None


@pytest.mark.django_db
def test_supplement_intake_needs_own_supplement():
    me, other = User.objects.create_user("me"), User.objects.create_user("other")
    mine = Supplement.objects.create(user=me, name="D3")
    theirs = Supplement.objects.create(user=other, name="D3")
    client = APIClient()
    client.force_authenticate(me)
    body = {"taken_at": "2026-11-10T08:00:00Z", "qty": 1}
    url = "/api/plan/supplement-intakes/"
    assert client.post(url, {**body, "supplement": theirs.id}).status_code == 400
    created = client.post(url, {**body, "supplement": mine.id})
    assert created.status_code == 201
    assert client.patch(f"{url}{created.data['id']}/", {"supplement": theirs.id}).status_code == 400
