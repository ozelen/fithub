from rest_framework import serializers

from .models import ActivityPlan, ActivityType, Profile, Supplement, SupplementIntake


class ActivityTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityType
        fields = ["id", "name", "met", "protein_g_per_kg", "fat_g_per_kg"]


class ActivityPlanSerializer(serializers.ModelSerializer):
    activity_type_name = serializers.CharField(
        source="activity_type.name", read_only=True
    )

    class Meta:
        model = ActivityPlan
        fields = [
            "id",
            "activity_type",
            "activity_type_name",
            "hours_per_session",
            "times_per_week",
        ]


class ProfileSerializer(serializers.ModelSerializer):
    activities = ActivityPlanSerializer(many=True, read_only=True)

    class Meta:
        model = Profile
        fields = [
            "sex",
            "birth_date",
            "height_cm",
            "target_body_fat_pct",
            "target_weight_kg",
            "deficit_pct",
            "steps_per_day",
            "answers",
            "activities",
            "updated_at",
        ]


class SupplementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplement
        fields = ["id", "name", "dose", "schedule", "is_active"]


class SupplementIntakeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplementIntake
        fields = ["id", "supplement", "taken_at", "qty"]
