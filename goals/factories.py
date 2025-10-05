from datetime import date, timedelta

import factory
from django.contrib.auth.models import User
from factory.django import DjangoModelFactory
from faker import Faker

from .models import BodyMeasurement, Goal

fake = Faker()


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")


class GoalFactory(DjangoModelFactory):
    class Meta:
        model = Goal

    user = factory.SubFactory(UserFactory)
    goal_type = factory.Faker(
        "random_element",
        elements=[
            "weight_loss",
            "muscle_gain",
            "endurance",
            "strength",
            "flexibility",
            "general_fitness",
        ],
    )
    target_date = factory.LazyFunction(lambda: date.today() + timedelta(days=30))
    notes = factory.Faker("text", max_nb_chars=500)
    is_active = True


class BodyMeasurementFactory(DjangoModelFactory):
    class Meta:
        model = BodyMeasurement

    user = factory.SubFactory(UserFactory)
    metric = factory.Faker(
        "random_element",
        elements=[
            "weight_kg",
            "waist_cm",
            "hip_cm",
            "neck_cm",
            "arm_circumference_cm",
            "thigh_circumference_cm",
            "calf_circumference_cm",
            "body_fat_percentage",
            "muscle_mass_percentage",
            "bmi_value",
        ],
    )
    measurement_type = factory.Faker(
        "random_element", elements=["target", "baseline", "log"]
    )
    value = factory.Faker("pyfloat", min_value=1, max_value=200, right_digits=2)
    timestamp = factory.Faker("date_time_this_month")
