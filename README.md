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
