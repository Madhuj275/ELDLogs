from datetime import datetime
import traceback
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status as http_status

from .hos_engine import HOSSimulator, Leg, build_daily_logs, DRIVING, ON_DUTY
from .models import Trip, LogSheet
from .routing import geocode, get_route, RoutingError
from .serializers import TripInputSerializer, TripSerializer

PICKUP_DROPOFF_DURATION = 1.0


@api_view(["POST"])
def plan_trip(request):
    input_serializer = TripInputSerializer(data=request.data)
    input_serializer.is_valid(raise_exception=True)
    data = input_serializer.validated_data

    start_time = data.get("start_time") or datetime.now().replace(
        minute=0, second=0, microsecond=0
    )

    manifest = {
        "driver_name": data.get("driver_name") or "Driver on file",
        "driver_number": data.get("driver_number") or "N/A",
        "driver_initials": data.get("driver_initials") or "",
        "co_driver": data.get("co_driver") or "NA",
        "truck_number": data.get("truck_number") or "N/A",
        "trailer_number": data.get("trailer_number") or "N/A",
        "carrier_name": data.get("carrier_name") or "Carrier name on file",
        "home_terminal_address": data.get("home_terminal_address") or data["current_location"],
        "shipper": data.get("shipper") or "N/A",
        "commodity": data.get("commodity") or "N/A",
        "load_number": data.get("load_number") or "N/A",
    }

    try:
        current = geocode(data["current_location"])
        pickup = geocode(data["pickup_location"])
        dropoff = geocode(data["dropoff_location"])

        leg1 = get_route(current, pickup)
        leg2 = get_route(pickup, dropoff)
    except RoutingError as exc:
        return Response({"error": str(exc)}, status=http_status.HTTP_400_BAD_REQUEST)
    except Exception as exc:
        traceback.print_exc()
        return Response(
            {
                "error": str(exc),
                "type": type(exc).__name__,
            },
            status=http_status.HTTP_502_BAD_GATEWAY,
        )

    legs = [
        Leg(
            kind="drive",
            duration_hours=leg1["duration_hours"],
            distance_miles=leg1["distance_miles"],
            label=f"En route to pickup ({data['pickup_location']})",
            location={"lat": current["lat"], "lon": current["lon"]},
            geometry=leg1["geometry"],
        ),
        Leg(
            kind="onduty",
            duration_hours=PICKUP_DROPOFF_DURATION,
            label=f"Pickup at {data['pickup_location']}",
            location={"lat": pickup["lat"], "lon": pickup["lon"]},
        ),
        Leg(
            kind="drive",
            duration_hours=leg2["duration_hours"],
            distance_miles=leg2["distance_miles"],
            label=f"En route to drop-off ({data['dropoff_location']})",
            location={"lat": pickup["lat"], "lon": pickup["lon"]},
            geometry=leg2["geometry"],
        ),
        Leg(
            kind="onduty",
            duration_hours=PICKUP_DROPOFF_DURATION,
            label=f"Drop-off at {data['dropoff_location']}",
            location={"lat": dropoff["lat"], "lon": dropoff["lon"]},
        ),
    ]

    simulator = HOSSimulator(cycle_used_hours=data["current_cycle_used"], start_time=start_time)
    try:
        events = simulator.run(legs)
    except RuntimeError as exc:
        return Response({"error": str(exc)}, status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)

    daily_logs = build_daily_logs(events)

    stops = []
    for ev in events:
        if ev.label in ("Required 30-minute break",) or ev.label.startswith("Fuel stop") \
                or ev.label.startswith("10-hour") or ev.label.startswith("34-hour") \
                or ev.status == ON_DUTY or ev.label.startswith("Trip complete"):
            stops.append({
                "type": ev.status,
                "label": ev.label,
                "start": ev.start.isoformat(),
                "end": ev.end.isoformat(),
                "duration_hours": round(ev.duration_hours, 2),
                "location": ev.location,
            })

    total_distance = leg1["distance_miles"] + leg2["distance_miles"]
    total_duration = leg1["duration_hours"] + leg2["duration_hours"]

    trip = Trip.objects.create(
        current_location=data["current_location"],
        pickup_location=data["pickup_location"],
        dropoff_location=data["dropoff_location"],
        current_cycle_used_hours=data["current_cycle_used"],
        total_distance_miles=total_distance,
        total_duration_hours=total_duration,
        route_geometry=leg1["geometry"] + leg2["geometry"],
        stops=stops,
        manifest=manifest,
    )

    for idx, log in enumerate(daily_logs, start=1):
        LogSheet.objects.create(
            trip=trip,
            date=log["date"],
            day_index=idx,
            events=log["events"],
            totals=log["totals"],
        )

    trip_serialized = TripSerializer(trip).data
    return Response({
        "trip": trip_serialized,
        "route": {
            "leg_to_pickup": leg1["geometry"],
            "leg_to_dropoff": leg2["geometry"],
            "distance_miles": round(total_distance, 1),
            "duration_hours": round(total_duration, 2),
            "waypoints": {
                "current": current,
                "pickup": pickup,
                "dropoff": dropoff,
            },
        },
        "stops": stops,
        "daily_logs": daily_logs,
    })


@api_view(["GET"])
def trip_history(request):
    trips = Trip.objects.order_by("-created_at")[:20]
    return Response(TripSerializer(trips, many=True).data)


@api_view(["GET"])
def trip_detail(request, trip_id):
    try:
        trip = Trip.objects.get(pk=trip_id)
    except Trip.DoesNotExist:
        return Response({"error": "Trip not found"}, status=http_status.HTTP_404_NOT_FOUND)
    return Response(TripSerializer(trip).data)
