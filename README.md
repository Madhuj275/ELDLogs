# ELD Trip Planner

Full-stack app (Django + React) that takes trip details and outputs a route
plus FMCSA-style daily driver logs.

**Inputs:** current location, pickup location, drop-off location, current
cycle hours used (70hrs/8-day cycle).
**Outputs:** map with route + stops/rests, and one or more drawn daily log
sheets (24-hr grid, 4 duty-status rows, remarks, recap) — matching the
paper ELD log format.

Assumptions: property-carrying driver, 70hrs/8-day cycle, no adverse
driving conditions, fueling at least every 1,000 miles, 1 hour on-duty
each for pickup and drop-off.

## Stack
- **Backend:** Django + DRF, SQLite (local db, no setup needed)
- **Routing:** OSRM public API (free, no key) for driving routes
- **Geocoding:** OpenStreetMap Nominatim (free, no key)
- **Frontend:** React (Vite) + Leaflet (free OSM map tiles)
- **HOS logic:** `backend/trips/hos_engine.py` — simulates duty-status
  changes (driving, on-duty, off-duty, sleeper berth) honoring the
  11-hr driving limit, 14-hr duty window, 30-min break after 8hrs
  driving, 10-hr resets, 34-hr restarts, and fuel stops.

## Run locally

### Backend
```bash
cd backend
python3 -m venv venv && source venv/bin/activate   # optional
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```
API is now at `http://127.0.0.1:8000/api/`.

### Frontend
```bash
cd frontend
npm install
npm run dev
```
Open `http://127.0.0.1:5173`. It calls the API at the URL in
`VITE_API_BASE_URL` (see `.env.example`); defaults to `http://127.0.0.1:8000/api`.

## Deploy

**Backend (Render.com, free tier):**
1. Push this repo to GitHub.
2. New Web Service → point at `backend/` → Build command `./build.sh` →
   Start command `gunicorn config.wsgi:application`.
3. Set env vars: `DJANGO_DEBUG=False`, `DJANGO_ALLOWED_HOSTS=<your-render-domain>`,
   `DJANGO_SECRET_KEY=<random string>`.

**Frontend (Vercel):**
1. Import the repo, set root directory to `frontend/`.
2. Add env var `VITE_API_BASE_URL=https://<your-render-domain>/api`.
3. Deploy (Vercel auto-detects the Vite build).

Also update `CORS_ALLOW_ALL_ORIGINS` in `backend/config/settings.py` to a
specific allow-list for production if you want to lock it down.

## API
`POST /api/trips/plan/`
```json
{
  "current_location": "Green Bay, WI",
  "pickup_location": "Fond du Lac, WI",
  "dropoff_location": "Indianapolis, IN",
  "current_cycle_used": 12,
  "driver_name": "Y. Smith",
  "driver_number": "1224213",
  "driver_initials": "YS",
  "co_driver": "NA",
  "truck_number": "48872",
  "trailer_number": "TA939200",
  "carrier_name": "Schneider National Carriers, Inc.",
  "home_terminal_address": "Green Bay, WI",
  "shipper": "Don's Paper Co.",
  "commodity": "Paper products",
  "load_number": "ST13241564114"
}
```
All the driver/vehicle/carrier/shipment fields are optional — leave them
out and the log sheet header shows placeholders. When provided, they're
echoed into `trip.manifest` and printed on every daily log sheet header,
matching a standard J. J. Keller-style paper log (driver info, vehicle
numbers, mileage today, carrier/home terminal, shipper/commodity/load,
and a post-trip inspection block).

Returns route geometry, stops, and `daily_logs` (one per calendar day of
the trip, each with its own duty-status totals and `miles_today`) — each
trip and its logs are also saved to the local SQLite DB (`GET /api/trips/`
for history, `GET /api/trips/<id>/` for one trip).

## Notes / limitations
- OSRM's public demo server and Nominatim are free but rate-limited —
  fine for a demo/assessment, not for production volume.
- Stop locations along the route are interpolated from route geometry
  (not reverse-geocoded to city names) to avoid extra rate-limited calls;
  the map shows exact coordinates.
- The HOS engine is a best-effort simulation for planning/demo purposes,
  not a certified compliance tool. Daily 10-hour resets are logged as
  **Sleeper Berth** time (realistic for an OTR driver resting in the cab);
  the mandatory 30-minute break and the final end-of-trip rest are logged
  as **Off Duty**. A 34-hour restart is inserted if the 70-hour/8-day
  cycle would otherwise be exceeded.
