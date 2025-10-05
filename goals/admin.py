from django.contrib import admin

from .models import BodyMeasurement, Goal

# Register your models here.
admin.site.register(Goal)
admin.site.register(BodyMeasurement)
