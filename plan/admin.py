from django.contrib import admin

from .models import ActivityPlan, ActivityType, Profile, Supplement, SupplementIntake


class ActivityPlanInline(admin.TabularInline):
    model = ActivityPlan
    extra = 0


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "sex", "height_cm", "target_body_fat_pct", "deficit_pct"]
    inlines = [ActivityPlanInline]


@admin.register(ActivityType)
class ActivityTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "met", "protein_g_per_kg", "fat_g_per_kg"]
    search_fields = ["name"]


@admin.register(Supplement)
class SupplementAdmin(admin.ModelAdmin):
    list_display = ["name", "user", "dose", "is_active"]


admin.site.register(SupplementIntake)
