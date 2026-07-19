from django.db import models


class Trip(models.Model):
    current_location = models.CharField(max_length=255)
    pickup_location = models.CharField(max_length=255)
    dropoff_location = models.CharField(max_length=255)
    current_cycle_used_hours = models.FloatField()

    total_distance_miles = models.FloatField(default=0)
    total_duration_hours = models.FloatField(default=0)

    route_geometry = models.JSONField(default=list, blank=True)
    stops = models.JSONField(default=list, blank=True)
    manifest = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Trip #{self.pk}: {self.current_location} -> {self.pickup_location} -> {self.dropoff_location}"


class LogSheet(models.Model):
    trip = models.ForeignKey(Trip, related_name="log_sheets", on_delete=models.CASCADE)
    date = models.DateField()
    events = models.JSONField(default=list)
    totals = models.JSONField(default=dict)
    day_index = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["day_index"]

    def __str__(self):
        return f"LogSheet for Trip #{self.trip_id} - {self.date}"
