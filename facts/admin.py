from django.contrib import admin

from .models import Category, ImportRun, Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "brands", "energy_kcal", "proteins", "completeness", "obsolete")
    search_fields = ("code", "name", "brands")
    list_filter = ("obsolete", "nutriscore_grade")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("tag", "parents")
    search_fields = ("tag",)


@admin.register(ImportRun)
class ImportRunAdmin(admin.ModelAdmin):
    list_display = ("name", "kind", "rows", "created_at")
