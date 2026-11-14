import pytest
from rest_framework.test import APIClient

from facts.models import Product
from nutrition.models import Ingredient, MealRecord

pytestmark = pytest.mark.django_db


@pytest.fixture
def nutella():
    return Product.objects.create(
        code="3017620422003",
        name="Nutella",
        brands="Ferrero",
        per="100g",
        energy_kcal=539,
        proteins=6.3,
        fat=30.9,
        carbohydrates=57.5,
        sugars=56.3,
    )


def test_scan_creates_one_personal_ingredient(authenticated_client, user, nutella):
    r = authenticated_client.post("/api/nutrition/ingredients/from_barcode/", {"barcode": "3017620422003"}, format="json")
    assert r.status_code == 201, r.content
    assert (r.data["name"], r.data["calories"], r.data["barcode"]) == ("Nutella (Ferrero)", 539, "3017620422003")
    again = authenticated_client.post("/api/nutrition/ingredients/from_barcode/", {"barcode": "3017620422003"}, format="json")
    assert again.status_code == 200 and again.data["id"] == r.data["id"]
    assert Ingredient.objects.filter(created_by=user, is_personal=True).count() == 1


def test_scan_unknown_or_factless_barcode(authenticated_client):
    assert (
        authenticated_client.post("/api/nutrition/ingredients/from_barcode/", {"barcode": "123"}, format="json").status_code
        == 404
    )
    Product.objects.create(code="8480000000001", name="Mystery", per="")
    r = authenticated_client.post("/api/nutrition/ingredients/from_barcode/", {"barcode": "8480000000001"}, format="json")
    assert r.status_code == 422 and r.data["name"] == "Mystery"
    assert (
        authenticated_client.post("/api/nutrition/ingredients/from_barcode/", {"barcode": "abc"}, format="json").status_code
        == 400
    )


def test_upc_a_matches_the_13_digit_code(authenticated_client):
    Product.objects.create(code="0049000006346", name="Coke", per="100g", energy_kcal=42)
    r = authenticated_client.post("/api/nutrition/ingredients/from_barcode/", {"barcode": "049000006346"}, format="json")
    assert r.status_code == 201 and r.data["barcode"] == "0049000006346"


def test_meal_from_items_snapshots_nutrients(authenticated_client, user):
    oats = Ingredient.objects.create(
        name="Oats", calories=380, proteins=13, fats=7, carbs=60, is_personal=True, created_by=user
    )
    milk = Ingredient.objects.create(name="Milk", calories=64, proteins=3.2, fats=3.6, carbs=4.8)
    r = authenticated_client.post(
        "/api/nutrition/records/",
        {
            "meal_name": "Porridge",
            "items": [{"ingredient_id": oats.id, "grams": 50}, {"ingredient_id": milk.id, "grams": 200}],
        },
        format="json",
    )
    assert r.status_code == 201, r.content
    assert (r.data["calories"], r.data["proteins"], r.data["fats"], r.data["carbs"], r.data["quantity_grams"]) == (
        318.0,
        12.9,
        10.7,
        39.6,
        250.0,
    )
    assert [i["name"] for i in r.data["items"]] == ["Oats", "Milk"]

    oats.calories = 999  # editing the ingredient later must not rewrite the day
    oats.save()
    record = MealRecord.objects.get(id=r.data["id"])
    assert record.get_total_calories() == 318.0
    today = authenticated_client.get("/api/plan/today/")
    assert today.data["eaten"]["calories"] == 318.0

    edited = authenticated_client.patch(
        f"/api/nutrition/records/{record.id}/", {"items": [{"ingredient_id": milk.id, "grams": 100}]}, format="json"
    )
    assert edited.status_code == 200 and edited.data["calories"] == 64.0


def test_meal_items_reject_foreign_ingredients_and_empty_records(authenticated_client):
    from django.contrib.auth.models import User

    other = User.objects.create_user("other")
    theirs = Ingredient.objects.create(
        name="Secret", calories=1, proteins=0, fats=0, carbs=0, is_personal=True, created_by=other
    )
    r = authenticated_client.post(
        "/api/nutrition/records/", {"meal_name": "x", "items": [{"ingredient_id": theirs.id, "grams": 10}]}, format="json"
    )
    assert r.status_code == 400
    assert authenticated_client.post("/api/nutrition/records/", {"meal_name": "x"}, format="json").status_code == 400
    assert APIClient().get("/api/nutrition/records/").status_code == 401
