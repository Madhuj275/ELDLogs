from django.contrib import admin
from .models import Trip, LogSheet


class LogSheetInline(admin.TabularInline):
    model = LogSheet
    extra = 0


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ("id", "current_location", "pickup_location", "dropoff_location", "created_at")
    inlines = [LogSheetInline]


@admin.register(LogSheet)
class LogSheetAdmin(admin.ModelAdmin):
    list_display = ("id", "trip", "date", "day_index")
