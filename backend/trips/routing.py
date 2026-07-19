"""
Free routing/geocoding integrations.

* Geocoding: OpenStreetMap Nominatim (https://nominatim.org) - free, no
  API key required, but requires a descriptive User-Agent and is rate
  limited (max ~1 req/sec). Fine for this app's traffic pattern.

* Routing: OSRM public demo server (https://router.project-osrm.org) -
  free, no API key required, driving profile, returns distance/duration
  and route geometry as GeoJSON.

Both services are used server-side only.
"""
import requests
import os

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OSRM_URL = "https://router.project-osrm.org/route/v1/driving"
GEOAPIFY_URL = "https://api.geoapify.com/v1/geocode/search"
GEOAPIFY_API_KEY = os.getenv("GEOAPIFY_API_KEY")

HEADERS = {
    "User-Agent": "ELDTripPlanner/1.0 (educational assessment project)"
}

METERS_TO_MILES = 0.000621371
SECONDS_TO_HOURS = 1 / 3600.0


class RoutingError(Exception):
    pass


def geocode(location_text: str):
    params = {
        "text": location_text,
        "apiKey": GEOAPIFY_API_KEY,
        "limit": 1,
    }

    response = requests.get(
        GEOAPIFY_URL,
        params=params,
        timeout=15,
    )

    response.raise_for_status()

    data = response.json()

    features = data.get("features", [])

    if not features:
        raise RoutingError(f"Could not find location: {location_text}")

    point = features[0]

    return {
        "lat": point["properties"]["lat"],
        "lon": point["properties"]["lon"],
        "display_name": point["properties"]["formatted"],
    }


def get_route(origin: dict, destination: dict) -> dict:
    """origin/destination: {"lat":.., "lon":..}. Returns distance (miles),
    duration (hours) and geometry (list of [lat, lon])."""
    coords = f"{origin['lon']},{origin['lat']};{destination['lon']},{destination['lat']}"
    url = f"{OSRM_URL}/{coords}"
    params = {"overview": "full", "geometries": "geojson"}
    resp = requests.get(url, params=params, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != "Ok" or not data.get("routes"):
        raise RoutingError("No route could be found between the given locations")
    route = data["routes"][0]
    geometry = [[lat, lon] for lon, lat in route["geometry"]["coordinates"]]
    return {
        "distance_miles": route["distance"] * METERS_TO_MILES,
        "duration_hours": route["duration"] * SECONDS_TO_HOURS,
        "geometry": geometry,
    }


def point_at_fraction(geometry, fraction):
    """Approximate the [lat, lon] at a given fraction (0-1) along a
    polyline, by fraction of number of points (good enough for labeling
    stops on a map, not for precision routing)."""
    if not geometry:
        return None
    fraction = min(max(fraction, 0.0), 1.0)
    idx = int(round(fraction * (len(geometry) - 1)))
    return geometry[idx]
