from django.contrib.auth.models import User
from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers

from goals.models import Goal

from .models import Category, Diet, Ingredient, Meal, MealIngredient, MealPreference, MealRecord


def visible_ingredients(user):
    """The global catalog plus the user's own ingredients."""
    return Ingredient.objects.filter(Q(is_personal=False) | Q(created_by=user))


class OwnedRefsMixin:
    """Ids a client sends must point at rows the caller may use."""

    def _check(self, queryset, value):
        if value is not None and not queryset.filter(pk=getattr(value, "pk", value)).exists():
            raise serializers.ValidationError("Not found.")
        return value

    def validate_diet_id(self, value):
        return self._check(Diet.objects.filter(user=self.context["request"].user), value)

    def validate_meal_id(self, value):
        return self._check(Meal.objects.filter(diet__user=self.context["request"].user), value)

    validate_meal = validate_meal_id

    def validate_ingredient_id(self, value):
        return self._check(visible_ingredients(self.context["request"].user), value)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name"]


class GoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Goal
        fields = ["id", "goal_type", "notes", "target_date", "is_active"]


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "parent"]


class IngredientSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Ingredient
        fields = [
            "id",
            "name",
            "category",
            "category_id",
            "proteins",
            "fats",
            "carbs",
            "calories",
            "fibers",
            "sugars",
            "description",
            "barcode",
            "created_at",
            "updated_at",
        ]


class DietSerializer(serializers.ModelSerializer):
    goal = GoalSerializer(read_only=True)
    goal_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    user = UserSerializer(read_only=True)
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False, allow_null=True)

    class Meta:
        model = Diet
        fields = [
            "id",
            "name",
            "user",
            "goal",
            "goal_id",
            "day_proteins_g",
            "day_fats_g",
            "day_carbohydrates_g",
            "day_calories_kcal",
            "is_active",
            "start_date",
            "end_date",
            "notes",
            "created_at",
            "updated_at",
        ]


class MealIngredientSerializer(OwnedRefsMixin, serializers.ModelSerializer):
    ingredient = IngredientSerializer(read_only=True)
    ingredient_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = MealIngredient
        fields = [
            "id",
            "meal",
            "ingredient",
            "ingredient_id",
            "barcode",
            "quantity",
            "unit",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        ingredient_id = validated_data.pop("ingredient_id")
        ingredient = Ingredient.objects.get(id=ingredient_id)
        validated_data["ingredient"] = ingredient
        return super().create(validated_data)


class MealSerializer(OwnedRefsMixin, serializers.ModelSerializer):
    diet = DietSerializer(read_only=True)
    diet_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    ingredients = MealIngredientSerializer(many=True, read_only=True)
    start_date = serializers.DateField(required=False, allow_null=True)
    end_date = serializers.DateField(required=False, allow_null=True)
    recurrence_until = serializers.DateField(required=False, allow_null=True)

    class Meta:
        model = Meal
        fields = [
            "id",
            "name",
            "description",
            "diet",
            "diet_id",
            "ingredients",
            "is_scheduled",
            "start_date",
            "end_date",
            "start_time",
            "duration_minutes",
            "recurrence_type",
            "recurrence_until",
            "meal_type",
            "created_at",
            "updated_at",
        ]


class MealEditSerializer(serializers.ModelSerializer):
    """Simplified serializer for meal editing without nested Goal serialization"""

    diet_id = serializers.IntegerField(source="diet.id", read_only=True)

    class Meta:
        model = Meal
        fields = ["id", "name", "description", "diet_id", "created_at", "updated_at"]


class MealRecordItemSerializer(serializers.Serializer):
    ingredient_id = serializers.IntegerField()
    grams = serializers.FloatField(min_value=0.1)


class MealRecordSerializer(OwnedRefsMixin, serializers.ModelSerializer):
    """Either a planned meal (`meal_id`) or a meal composed here (`meal_name` + `items` in grams)."""

    meal = MealSerializer(read_only=True)
    meal_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    user = UserSerializer(read_only=True)
    timestamp = serializers.DateTimeField(required=False)
    items = serializers.JSONField(required=False)

    class Meta:
        model = MealRecord
        fields = [
            "id",
            "meal",
            "meal_id",
            "meal_name",
            "items",
            "quantity_grams",
            "calories",
            "proteins",
            "carbs",
            "fats",
            "timestamp",
            "photo",
            "user",
            "feedback",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["quantity_grams", "calories", "proteins", "carbs", "fats"]

    def validate_items(self, value):
        rows = MealRecordItemSerializer(data=value, many=True)
        rows.is_valid(raise_exception=True)
        found = visible_ingredients(self.context["request"].user).in_bulk([r["ingredient_id"] for r in rows.validated_data])
        items = []
        for r in rows.validated_data:
            ing = found.get(r["ingredient_id"])
            if ing is None:
                raise serializers.ValidationError(f"Ingredient {r['ingredient_id']} not found.")
            k = r["grams"] / 100
            items.append(
                {
                    "ingredient_id": ing.id,
                    "name": ing.name,
                    "grams": r["grams"],
                    **{f: round(getattr(ing, f) * k, 1) for f in ("calories", "proteins", "fats", "carbs")},
                }
            )
        return items

    def validate(self, attrs):
        if self.instance is None and not attrs.get("meal_id") and not attrs.get("items"):
            raise serializers.ValidationError("Send meal_id or items.")
        if "items" in attrs:
            items = attrs["items"]
            attrs["quantity_grams"] = round(sum(i["grams"] for i in items), 1)
            for f in ("calories", "proteins", "fats", "carbs"):
                attrs[f] = round(sum(i[f] for i in items), 1)
        return attrs

    def create(self, validated_data):
        validated_data.setdefault("timestamp", timezone.now())
        return super().create(validated_data)


class MealPreferenceSerializer(OwnedRefsMixin, serializers.ModelSerializer):
    ingredient = IngredientSerializer(read_only=True)
    ingredient_id = serializers.IntegerField(write_only=True)
    user = UserSerializer(read_only=True)

    class Meta:
        model = MealPreference
        fields = [
            "id",
            "user",
            "ingredient",
            "ingredient_id",
            "barcode",
            "description",
            "preference_type",
            "created_at",
            "updated_at",
        ]


class MealPreferenceCreateSerializer(serializers.ModelSerializer):
    ingredient_id = serializers.IntegerField(write_only=True)
    ingredient_name = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = MealPreference
        fields = [
            "ingredient_id",
            "ingredient_name",
            "barcode",
            "description",
            "preference_type",
        ]


class MealPreferenceUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MealPreference
        fields = ["description", "preference_type"]


class IngredientSearchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ["id", "name", "category", "calories", "proteins", "fats", "carbs"]
