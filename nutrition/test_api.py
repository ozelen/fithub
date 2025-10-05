from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from .factories import (
    DietFactory,
    IngredientFactory,
    MealFactory,
    MealIngredientFactory,
    MealPreferenceFactory,
    MealRecordFactory,
    UserFactory,
)
from .models import Diet, MealIngredient, MealPreference, MealRecord


class NutritionAPITestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory()
        self.other_user = UserFactory()
        self.client.force_authenticate(user=self.user)

    def test_diet_list_authenticated(self):
        """Test that authenticated users can list their diets"""
        diet1 = DietFactory(user=self.user)
        diet2 = DietFactory(user=self.user)
        diet3 = DietFactory(user=self.other_user)  # Should not appear

        url = reverse("diet-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)
        diet_ids = [diet["id"] for diet in response.data["results"]]
        self.assertIn(diet1.id, diet_ids)
        self.assertIn(diet2.id, diet_ids)
        self.assertNotIn(diet3.id, diet_ids)

    def test_diet_create(self):
        """Test creating a new diet"""
        url = reverse("diet-list")
        data = {
            "name": "Test Diet",
            "day_proteins_g": 150.0,
            "day_fats_g": 60.0,
            "day_carbohydrates_g": 200.0,
            "day_calories_kcal": 2000.0,
            "is_active": True,
            "notes": "Test diet notes",
        }

        response = self.client.post(url, data)

        # Check if it's a validation error and print the details
        if response.status_code == 400:
            print(f"Validation errors: {response.data}")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Diet.objects.count(), 1)
        diet = Diet.objects.first()
        self.assertEqual(diet.user, self.user)
        self.assertEqual(diet.name, "Test Diet")

    def test_diet_activate(self):
        """Test activating a diet"""
        diet1 = DietFactory(user=self.user, is_active=False)
        diet2 = DietFactory(user=self.user, is_active=True)

        url = reverse("diet-activate", kwargs={"pk": diet1.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        diet1.refresh_from_db()
        diet2.refresh_from_db()
        self.assertTrue(diet1.is_active)
        self.assertFalse(diet2.is_active)

    def test_diet_active_endpoint(self):
        """Test getting the active diet"""
        diet = DietFactory(user=self.user, is_active=True)

        url = reverse("diet-active")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], diet.id)

    def test_meal_list_filtered_by_user(self):
        """Test that meals are filtered by user's diets"""
        diet = DietFactory(user=self.user)
        other_diet = DietFactory(user=self.other_user)

        meal1 = MealFactory(diet=diet)
        meal2 = MealFactory(diet=diet)
        meal3 = MealFactory(diet=other_diet)  # Should not appear

        url = reverse("meal-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)
        meal_ids = [meal["id"] for meal in response.data["results"]]
        self.assertIn(meal1.id, meal_ids)
        self.assertIn(meal2.id, meal_ids)
        self.assertNotIn(meal3.id, meal_ids)

    def test_meal_nutrition_summary(self):
        """Test getting nutrition summary for a meal"""
        diet = DietFactory(user=self.user)
        meal = MealFactory(diet=diet)
        ingredient = IngredientFactory(calories=100, proteins=10, fats=5, carbs=20)
        MealIngredientFactory(meal=meal, ingredient=ingredient, quantity=200)  # 200g

        url = reverse("meal-nutrition-summary", kwargs={"pk": meal.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 200g of ingredient with 100 cal/100g = 200 calories
        self.assertEqual(response.data["total_calories"], 200.0)
        self.assertEqual(response.data["total_proteins"], 20.0)  # 10 * 2
        self.assertEqual(response.data["total_fats"], 10.0)  # 5 * 2
        self.assertEqual(response.data["total_carbs"], 40.0)  # 20 * 2

    def test_ingredient_search(self):
        """Test ingredient search functionality"""
        ingredient1 = IngredientFactory(name="Chicken Breast")
        ingredient2 = IngredientFactory(name="Chicken Thigh")
        ingredient3 = IngredientFactory(name="Beef Steak")

        url = reverse("ingredient-search")
        response = self.client.get(url, {"q": "chicken"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        ingredient_names = [ing["name"] for ing in response.data]
        self.assertIn("Chicken Breast", ingredient_names)
        self.assertIn("Chicken Thigh", ingredient_names)
        self.assertNotIn("Beef Steak", ingredient_names)

    def test_ingredient_personal(self):
        """Test getting user's personal ingredients"""
        personal_ingredient = IngredientFactory(created_by=self.user, is_personal=True)
        public_ingredient = IngredientFactory(is_personal=False)
        other_personal = IngredientFactory(created_by=self.other_user, is_personal=True)

        url = reverse("ingredient-personal")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], personal_ingredient.id)

    def test_meal_record_today(self):
        """Test getting today's meal records"""
        from django.utils import timezone

        today = timezone.now().date()

        record1 = MealRecordFactory(user=self.user, timestamp=timezone.now())
        record2 = MealRecordFactory(user=self.user, timestamp=timezone.now())
        record3 = MealRecordFactory(user=self.other_user, timestamp=timezone.now())

        url = reverse("mealrecord-today")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        record_ids = [record["id"] for record in response.data]
        self.assertIn(record1.id, record_ids)
        self.assertIn(record2.id, record_ids)
        self.assertNotIn(record3.id, record_ids)

    def test_meal_record_nutrition_summary(self):
        """Test getting nutrition summary for meal records"""
        from datetime import timedelta

        from django.utils import timezone

        # Create records for the last 7 days
        for i in range(7):
            record = MealRecordFactory(
                user=self.user,
                timestamp=timezone.now() - timedelta(days=i),
                meal=None,  # No meal, use direct calories
                calories=100 * (i + 1),  # 100, 200, 300, etc.
            )

        url = reverse("mealrecord-nutrition-summary")
        response = self.client.get(url, {"days": 7})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["period_days"], 7)
        self.assertEqual(response.data["total_calories"], 2800)  # Sum of 100+200+...+700
        self.assertEqual(response.data["record_count"], 7)

    def test_meal_preference_by_type(self):
        """Test getting preferences by type"""
        love_pref = MealPreferenceFactory(user=self.user, preference_type="love")
        like_pref = MealPreferenceFactory(user=self.user, preference_type="like")
        dislike_pref = MealPreferenceFactory(user=self.user, preference_type="dislike")

        url = reverse("mealpreference-by-type")
        response = self.client.get(url, {"type": "love"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], love_pref.id)

    def test_unauthorized_access(self):
        """Test that unauthenticated users cannot access endpoints"""
        self.client.force_authenticate(user=None)

        url = reverse("diet-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cross_user_access_denied(self):
        """Test that users cannot access other users' data"""
        other_diet = DietFactory(user=self.other_user)

        url = reverse("diet-detail", kwargs={"pk": other_diet.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_meal_add_ingredient(self):
        """Test adding an ingredient to a meal"""
        diet = DietFactory(user=self.user)
        meal = MealFactory(diet=diet)
        ingredient = IngredientFactory()

        url = reverse("meal-add-ingredient", kwargs={"pk": meal.id})
        data = {"ingredient_id": ingredient.id, "quantity": 150.0, "unit": "g"}

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(MealIngredient.objects.count(), 1)
        meal_ingredient = MealIngredient.objects.first()
        self.assertEqual(meal_ingredient.meal, meal)
        self.assertEqual(meal_ingredient.ingredient, ingredient)

    def test_pagination(self):
        """Test that pagination works correctly"""
        # Create 25 diets to test pagination (default page size is 20)
        for _ in range(25):
            DietFactory(user=self.user)

        url = reverse("diet-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 20)  # First page
        self.assertIsNotNone(response.data["next"])  # Has next page

    def test_filtering(self):
        """Test filtering functionality"""
        active_diet = DietFactory(user=self.user, is_active=True)
        inactive_diet = DietFactory(user=self.user, is_active=False)

        url = reverse("diet-list")
        response = self.client.get(url, {"is_active": "true"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], active_diet.id)

    def test_search(self):
        """Test search functionality"""
        diet1 = DietFactory(user=self.user, name="Weight Loss Diet")
        diet2 = DietFactory(user=self.user, name="Muscle Gain Diet")
        diet3 = DietFactory(user=self.user, name="Healthy Eating")

        url = reverse("diet-list")
        response = self.client.get(url, {"search": "weight"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], diet1.id)

    def test_ordering(self):
        """Test ordering functionality"""
        diet1 = DietFactory(user=self.user, name="Z Diet")
        diet2 = DietFactory(user=self.user, name="A Diet")

        url = reverse("diet-list")
        response = self.client.get(url, {"ordering": "name"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"][0]["name"], "A Diet")
        self.assertEqual(response.data["results"][1]["name"], "Z Diet")
