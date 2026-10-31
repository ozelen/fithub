from django.contrib.auth.models import User
from django.db import models


class ActivityType(models.Model):
    name = models.CharField(max_length=120, unique=True)
    met = models.FloatField(help_text="kcal per kg per hour")
    protein_g_per_kg = models.FloatField(default=1.5)
    fat_g_per_kg = models.FloatField(default=1.0)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Profile(models.Model):
    SEX = [("male", "Male"), ("female", "Female")]

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="plan_profile"
    )
    sex = models.CharField(max_length=6, choices=SEX)
    birth_date = models.DateField()
    height_cm = models.FloatField()
    target_body_fat_pct = models.FloatField(null=True, blank=True)
    target_weight_kg = models.FloatField(null=True, blank=True)
    deficit_pct = models.IntegerField(
        default=0, help_text="Signed % of TDEE: -30 = 30% deficit, +10 = 10% surplus"
    )
    steps_per_day = models.PositiveIntegerField(default=0)
    answers = models.JSONField(
        default=dict, blank=True, help_text="Questionnaire answers"
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} profile"


class ActivityPlan(models.Model):
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="activities"
    )
    activity_type = models.ForeignKey(ActivityType, on_delete=models.PROTECT)
    hours_per_session = models.FloatField()
    times_per_week = models.FloatField()

    def __str__(self):
        return (
            f"{self.activity_type} {self.hours_per_session}h x{self.times_per_week}/wk"
        )


class Supplement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    dose = models.CharField(max_length=60, blank=True)
    schedule = models.JSONField(
        default=list, help_text='[{"when": "after_breakfast", "qty": 1, "note": ""}]'
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [("user", "name")]
        ordering = ["name"]

    def __str__(self):
        return self.name


class SupplementIntake(models.Model):
    supplement = models.ForeignKey(
        Supplement, on_delete=models.CASCADE, related_name="intakes"
    )
    taken_at = models.DateTimeField()
    qty = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ["-taken_at"]
