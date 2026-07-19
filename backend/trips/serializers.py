from rest_framework import serializers
from .models import Trip, LogSheet


class LogSheetSerializer(serializers.ModelSerializer):
    class Meta:
        model = LogSheet
        fields = ["id", "date", "day_index", "events", "totals"]


class TripInputSerializer(serializers.Serializer):
    current_location = serializers.CharField(max_length=255)
    pickup_location = serializers.CharField(max_length=255)
    dropoff_location = serializers.CharField(max_length=255)
    current_cycle_used = serializers.FloatField(min_value=0, max_value=70)
    start_time = serializers.DateTimeField(required=False)

    driver_name = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    driver_number = serializers.CharField(max_length=50, required=False, allow_blank=True, default="")
    driver_initials = serializers.CharField(max_length=10, required=False, allow_blank=True, default="")
    co_driver = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    truck_number = serializers.CharField(max_length=50, required=False, allow_blank=True, default="")
    trailer_number = serializers.CharField(max_length=50, required=False, allow_blank=True, default="")
    carrier_name = serializers.CharField(max_length=150, required=False, allow_blank=True, default="")
    home_terminal_address = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")
    shipper = serializers.CharField(max_length=150, required=False, allow_blank=True, default="")
    commodity = serializers.CharField(max_length=150, required=False, allow_blank=True, default="")
    load_number = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")


class TripSerializer(serializers.ModelSerializer):
    log_sheets = LogSheetSerializer(many=True, read_only=True)

    class Meta:
        model = Trip
        fields = [
            "id",
            "current_location",
            "pickup_location",
            "dropoff_location",
            "current_cycle_used_hours",
            "total_distance_miles",
            "total_duration_hours",
            "route_geometry",
            "stops",
            "manifest",
            "created_at",
            "log_sheets",
        ]
