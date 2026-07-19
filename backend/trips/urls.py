from django.urls import path
from . import views

urlpatterns = [
    path("trips/plan/", views.plan_trip, name="plan_trip"),
    path("trips/", views.trip_history, name="trip_history"),
    path("trips/<int:trip_id>/", views.trip_detail, name="trip_detail"),
]
