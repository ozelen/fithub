from django.contrib.auth.models import User
from rest_framework import serializers

from .models import BodyMeasurement, Goal


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name"]


class GoalSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    days_remaining = serializers.ReadOnlyField()

    class Meta:
        model = Goal
        fields = [
            "id",
            "user",
            "goal_type",
            "target_date",
            "notes",
            "is_active",
            "created_at",
            "updated_at",
            "days_remaining",
        ]
        read_only_fields = ["id", "user", "created_at", "updated_at"]


class GoalCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Goal
        fields = ["goal_type", "target_date", "notes", "is_active"]


class BodyMeasurementSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    metric_display = serializers.CharField(source="get_metric_display", read_only=True)
    measurement_type_display = serializers.CharField(source="get_measurement_type_display", read_only=True)

    class Meta:
        model = BodyMeasurement
        fields = [
            "id",
            "user",
            "metric",
            "metric_display",
            "measurement_type",
            "measurement_type_display",
            "value",
            "timestamp",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user", "created_at", "updated_at"]


class BodyMeasurementCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BodyMeasurement
        fields = ["metric", "measurement_type", "value", "timestamp"]


class BodyMeasurementBulkSerializer(serializers.Serializer):
    measurements = BodyMeasurementCreateSerializer(many=True)

    def create(self, validated_data):
        measurements_data = validated_data["measurements"]
        measurements = []
        for measurement_data in measurements_data:
            measurements.append(BodyMeasurement.objects.create(**measurement_data))
        return measurements
