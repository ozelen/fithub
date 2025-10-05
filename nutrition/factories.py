import factory
from django.contrib.auth.models import User
from factory.django import DjangoModelFactory
from faker import Faker

from .models import Category, Diet, Ingredient, Meal, MealIngredient, MealPreference, MealRecord

fake = Faker()


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")


class CategoryFactory(DjangoModelFactory):
    class Meta:
        model = Category

    name = factory.Faker("word")
    parent = None


class IngredientFactory(DjangoModelFactory):
    class Meta:
        model = Ingredient

    name = factory.Faker("word")
    category = factory.SubFactory(CategoryFactory)
    proteins = factory.Faker("pyfloat", min_value=0, max_value=50, right_digits=2)
    fats = factory.Faker("pyfloat", min_value=0, max_value=50, right_digits=2)
    carbs = factory.Faker("pyfloat", min_value=0, max_value=100, right_digits=2)
    calories = factory.Faker("pyfloat", min_value=0, max_value=500, right_digits=2)
    fibers = factory.Faker("pyfloat", min_value=0, max_value=20, right_digits=2)
    sugars = factory.Faker("pyfloat", min_value=0, max_value=50, right_digits=2)
    description = factory.Faker("text", max_nb_chars=200)
    is_personal = False
    created_by = None


class DietFactory(DjangoModelFactory):
    class Meta:
        model = Diet

    name = factory.Faker("sentence", nb_words=3)
    user = factory.SubFactory(UserFactory)
    day_proteins_g = factory.Faker("pyfloat", min_value=50, max_value=200, right_digits=2)
    day_fats_g = factory.Faker("pyfloat", min_value=30, max_value=100, right_digits=2)
    day_carbohydrates_g = factory.Faker("pyfloat", min_value=100, max_value=400, right_digits=2)
    day_calories_kcal = factory.Faker("pyfloat", min_value=1500, max_value=3000, right_digits=2)
    is_active = False
    start_date = factory.Faker("date_this_year")
    end_date = None
    notes = factory.Faker("text", max_nb_chars=500)


class MealFactory(DjangoModelFactory):
    class Meta:
        model = Meal

    name = factory.Faker("sentence", nb_words=3)
    description = factory.Faker("text", max_nb_chars=300)
    diet = factory.SubFactory(DietFactory)
    is_scheduled = False
    start_date = None
    end_date = None
    start_time = None
    duration_minutes = 30
    recurrence_type = "none"
    recurrence_until = None
    google_calendar_event_id = ""
    last_synced_to_calendar = None
    meal_type = "regular"


class MealIngredientFactory(DjangoModelFactory):
    class Meta:
        model = MealIngredient

    meal = factory.SubFactory(MealFactory)
    ingredient = factory.SubFactory(IngredientFactory)
    barcode = factory.Faker("ean13")
    quantity = factory.Faker("pyfloat", min_value=10, max_value=500, right_digits=2)
    unit = "g"


class MealRecordFactory(DjangoModelFactory):
    class Meta:
        model = MealRecord

    meal = factory.SubFactory(MealFactory)
    user = factory.SubFactory(UserFactory)
    meal_name = None
    quantity_grams = None
    calories = None
    proteins = None
    carbs = None
    fats = None
    timestamp = factory.Faker("date_time_this_month")
    photo = None
    feedback = factory.Faker("text", max_nb_chars=200)


class MealPreferenceFactory(DjangoModelFactory):
    class Meta:
        model = MealPreference

    user = factory.SubFactory(UserFactory)
    ingredient = factory.SubFactory(IngredientFactory)
    barcode = factory.Faker("ean13")
    description = factory.Faker("text", max_nb_chars=200)
    preference_type = factory.Faker(
        "random_element",
        elements=["love", "like", "dislike", "hate", "restriction", "allergy"],
    )
