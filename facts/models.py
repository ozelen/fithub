from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex
from django.db import models

NUTRIENTS = ("energy_kcal", "fat", "saturated_fat", "carbohydrates", "sugars", "fiber", "proteins", "salt")


class Product(models.Model):
    """One Open Food Facts product, trimmed to what calorie counting needs. Nutrient values are per `per`."""

    code = models.CharField(primary_key=True, max_length=64)
    name = models.CharField(max_length=512, blank=True, default="")
    brands = models.CharField(max_length=512, blank=True, default="")
    quantity = models.CharField(max_length=128, blank=True, default="")
    serving_size = models.CharField(max_length=128, blank=True, default="")
    serving_quantity = models.FloatField(null=True, blank=True)
    stores_tags = ArrayField(models.CharField(max_length=128), default=list, blank=True)
    countries_tags = ArrayField(models.CharField(max_length=128), default=list, blank=True)
    categories_tags = ArrayField(models.CharField(max_length=256), default=list, blank=True)
    nutriscore_grade = models.CharField(max_length=16, blank=True, default="")
    completeness = models.FloatField(default=0)
    obsolete = models.BooleanField(default=False)
    last_modified_t = models.BigIntegerField(default=0)
    per = models.CharField(max_length=8, blank=True, default="")
    energy_kcal = models.FloatField(null=True, blank=True)
    fat = models.FloatField(null=True, blank=True)
    saturated_fat = models.FloatField(null=True, blank=True)
    carbohydrates = models.FloatField(null=True, blank=True)
    sugars = models.FloatField(null=True, blank=True)
    fiber = models.FloatField(null=True, blank=True)
    proteins = models.FloatField(null=True, blank=True)
    salt = models.FloatField(null=True, blank=True)

    class Meta:
        indexes = [
            GinIndex(fields=["categories_tags"], name="facts_product_cats_gin"),
            GinIndex(fields=["name"], name="facts_product_name_trgm", opclasses=["gin_trgm_ops"]),
        ]

    def __str__(self):
        return f"{self.code} {self.name}"


class Category(models.Model):
    """Open Food Facts categories taxonomy entry: `en:basmati-rices` with its parents and names per language."""

    tag = models.CharField(primary_key=True, max_length=256)
    parents = ArrayField(models.CharField(max_length=256), default=list, blank=True)
    names = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.tag


class CategoryNutrition(models.Model):
    """Median nutrients per category over reasonably complete products. Materialized view, refreshed by the import."""

    tag = models.CharField(primary_key=True, max_length=256)
    n = models.IntegerField()
    energy_kcal = models.FloatField(null=True)
    fat = models.FloatField(null=True)
    saturated_fat = models.FloatField(null=True)
    carbohydrates = models.FloatField(null=True)
    sugars = models.FloatField(null=True)
    fiber = models.FloatField(null=True)
    proteins = models.FloatField(null=True)
    salt = models.FloatField(null=True)

    class Meta:
        managed = False
        db_table = "facts_category_nutrition"


class ImportRun(models.Model):
    """One applied source file (delta name, parquet snapshot, taxonomy), so deltas are never applied twice."""

    name = models.CharField(max_length=256, unique=True)
    kind = models.CharField(max_length=16)
    rows = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.kind} {self.name} ({self.rows})"
