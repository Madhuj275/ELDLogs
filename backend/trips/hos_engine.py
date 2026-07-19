"""
Hours-of-Service (HOS) simulation engine.

Implements the FMCSA property-carrying driver rules under the
70-hour/8-day cycle, no adverse driving conditions, assuming:
  * 11-hour driving limit per duty day
  * 14-hour on-duty window per duty day
  * 30-minute break required after 8 cumulative hours of driving
  * 10 consecutive hours off duty required to reset a duty day
  * 34-hour restart used if the 70-hour/8-day cycle would be exceeded
  * Fueling stop (on-duty, not driving) at least once every 1,000 miles
  * 1 hour on-duty (not driving) for each of pickup and drop-off

The engine does not try to be a certified compliance product -- it is a
best-effort simulation good enough for route/log planning and demo
purposes.
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional

from .routing import point_at_fraction

MAX_DRIVE_PER_DAY = 11.0
MAX_DUTY_WINDOW = 14.0
DRIVE_BEFORE_BREAK = 8.0
MANDATORY_BREAK = 0.5
MIN_OFF_DUTY_RESET = 10.0
CYCLE_LIMIT_HOURS = 70.0
RESTART_HOURS = 34.0
FUEL_INTERVAL_MILES = 1000.0
FUEL_STOP_DURATION = 0.5
PICKUP_DROPOFF_DURATION = 1.0

OFF_DUTY = "OFF"
SLEEPER_BERTH = "SB"
DRIVING = "D"
ON_DUTY = "ON"


@dataclass
class Leg:
    """A drivable segment of the trip."""
    kind: str  # "drive" or "onduty"
    duration_hours: float
    distance_miles: float = 0.0
    label: str = ""
    location: Optional[dict] = None  # {"lat":.., "lon":.., "name": ".."}
    geometry: Optional[list] = None  # list of [lat, lon] for drive legs


@dataclass
class DutyEvent:
    status: str
    start: datetime
    end: datetime
    label: str
    location: Optional[dict] = None
    distance_miles: float = 0.0

    @property
    def duration_hours(self):
        return (self.end - self.start).total_seconds() / 3600.0


class HOSSimulator:
    def __init__(self, cycle_used_hours: float, start_time: datetime):
        self.cycle_used = cycle_used_hours
        self.t = start_time
        self.drive_today = 0.0
        self.duty_window_start = start_time
        self.drive_since_break = 0.0
        self.distance_since_fuel = 0.0
        self.cycle_remaining = max(CYCLE_LIMIT_HOURS - cycle_used_hours, 0.0)
        self.events: List[DutyEvent] = []
        self._iterations = 0
        self._max_iterations = 20000

    # ---- helpers -----------------------------------------------------
    def _add(self, status, hours, label, location=None, distance_miles=0.0):
        if hours <= 1e-9:
            return
        start = self.t
        end = start + timedelta(hours=hours)
        # merge with previous identical status for cleanliness
        if self.events and self.events[-1].status == status and \
                self.events[-1].label == label and self.events[-1].end == start:
            self.events[-1].end = end
            self.events[-1].distance_miles += distance_miles
        else:
            self.events.append(DutyEvent(status, start, end, label, location, distance_miles))
        self.t = end

    def _duty_window_used(self):
        return (self.t - self.duty_window_start).total_seconds() / 3600.0

    def _reset_day(self, reason="10-hour sleeper berth reset"):
        self._add(SLEEPER_BERTH, MIN_OFF_DUTY_RESET, reason)
        self.drive_today = 0.0
        self.drive_since_break = 0.0
        self.duty_window_start = self.t

    def _restart_cycle(self):
        self._add(OFF_DUTY, RESTART_HOURS, "34-hour restart (70-hour cycle limit reached)")
        self.drive_today = 0.0
        self.drive_since_break = 0.0
        self.duty_window_start = self.t
        self.cycle_used = 0.0
        self.cycle_remaining = CYCLE_LIMIT_HOURS

    # ---- main driving loop --------------------------------------------
    def _drive_leg(self, leg: Leg):
        remaining = leg.duration_hours
        miles_per_hour = (leg.distance_miles / leg.duration_hours) if leg.duration_hours else 0
        distance_done_in_leg = 0.0

        def location_for(distance_done):
            if leg.geometry and leg.distance_miles:
                fraction = distance_done / leg.distance_miles
                pt = point_at_fraction(leg.geometry, fraction)
                if pt:
                    return {"lat": pt[0], "lon": pt[1]}
            return leg.location

        while remaining > 1e-6:
            self._iterations += 1
            if self._iterations > self._max_iterations:
                raise RuntimeError("HOS simulation exceeded iteration limit")

            if self.cycle_remaining <= 1e-6:
                self._restart_cycle()
                continue

            drive_left_today = MAX_DRIVE_PER_DAY - self.drive_today
            duty_left_today = MAX_DUTY_WINDOW - self._duty_window_used()
            drive_left_before_break = DRIVE_BEFORE_BREAK - self.drive_since_break
            miles_left_before_fuel = (
                FUEL_INTERVAL_MILES - self.distance_since_fuel
            ) / miles_per_hour if miles_per_hour else float("inf")

            if drive_left_today <= 1e-6 or duty_left_today <= 1e-6:
                self._reset_day()
                continue
            if drive_left_before_break <= 1e-6:
                self._add(OFF_DUTY, MANDATORY_BREAK, "Required 30-minute break")
                self.drive_since_break = 0.0
                continue

            chunk = min(
                remaining,
                drive_left_today,
                duty_left_today,
                drive_left_before_break,
                self.cycle_remaining,
                miles_left_before_fuel if miles_per_hour else remaining,
            )
            chunk = max(chunk, 0.0)
            if chunk <= 1e-6:
                # Safety valve: force a reset to avoid infinite loop
                self._reset_day()
                continue

            self._add(DRIVING, chunk, leg.label, location_for(distance_done_in_leg), distance_miles=chunk * miles_per_hour)
            self.drive_today += chunk
            self.drive_since_break += chunk
            self.cycle_remaining -= chunk
            self.cycle_used += chunk
            remaining -= chunk
            chunk_distance = chunk * miles_per_hour
            distance_done_in_leg += chunk_distance
            self.distance_since_fuel += chunk_distance

            if remaining > 1e-6 and self.distance_since_fuel >= FUEL_INTERVAL_MILES - 1e-6:
                duty_left_today = MAX_DUTY_WINDOW - self._duty_window_used()
                stop_location = location_for(distance_done_in_leg)
                if duty_left_today <= FUEL_STOP_DURATION:
                    self._reset_day()
                else:
                    self._add(ON_DUTY, FUEL_STOP_DURATION, "Fuel stop", stop_location)
                self.distance_since_fuel = 0.0

    def run(self, legs: List[Leg]) -> List[DutyEvent]:
        for leg in legs:
            if leg.kind == "drive":
                self._drive_leg(leg)
            else:
                # fixed-duration on-duty (not driving) activity, e.g. pickup/drop-off
                duty_left_today = MAX_DUTY_WINDOW - self._duty_window_used()
                if duty_left_today <= 1e-6:
                    self._reset_day()
                self._add(ON_DUTY, leg.duration_hours, leg.label, leg.location)
        # final rest so the last log day is complete
        self._add(OFF_DUTY, MIN_OFF_DUTY_RESET, "Trip complete - off duty")
        return self.events


def build_daily_logs(events: List[DutyEvent]):
    """Split a continuous list of DutyEvents (which may span multiple
    calendar days) into per-day log sheets, each covering midnight to
    midnight, with each event clipped to the day boundaries.
    """
    if not events:
        return []

    day_start = events[0].start.replace(hour=0, minute=0, second=0, microsecond=0)
    logs = []
    idx = 0
    current_day_start = day_start

    while idx < len(events):
        current_day_end = current_day_start + timedelta(days=1)
        day_events = []
        for ev in events:
            if ev.end <= current_day_start or ev.start >= current_day_end:
                continue
            clipped_start = max(ev.start, current_day_start)
            clipped_end = min(ev.end, current_day_end)
            if clipped_end <= clipped_start:
                continue
            full_duration = (ev.end - ev.start).total_seconds()
            fraction = (
                (clipped_end - clipped_start).total_seconds() / full_duration
                if full_duration > 0 else 1.0
            )
            day_events.append({
                "status": ev.status,
                "start_hour": (clipped_start - current_day_start).total_seconds() / 3600.0,
                "end_hour": (clipped_end - current_day_start).total_seconds() / 3600.0,
                "label": ev.label,
                "location": ev.location,
                "clock_start": clipped_start.strftime("%H:%M"),
                "clock_end": clipped_end.strftime("%H:%M"),
                "distance_miles": round(ev.distance_miles * fraction, 1),
            })

        if day_events:
            totals = {OFF_DUTY: 0.0, SLEEPER_BERTH: 0.0, DRIVING: 0.0, ON_DUTY: 0.0}
            miles_today = 0.0
            for de in day_events:
                totals[de["status"]] += de["end_hour"] - de["start_hour"]
                miles_today += de["distance_miles"]

            logs.append({
                "date": current_day_start.strftime("%Y-%m-%d"),
                "events": day_events,
                "totals": {
                    "off_duty": round(totals[OFF_DUTY], 2),
                    "sleeper_berth": round(totals[SLEEPER_BERTH], 2),
                    "driving": round(totals[DRIVING], 2),
                    "on_duty": round(totals[ON_DUTY], 2),
                },
                "total_on_duty_plus_driving": round(
                    totals[DRIVING] + totals[ON_DUTY], 2
                ),
                "miles_today": round(miles_today, 1),
            })

        current_day_start = current_day_end
        if current_day_start > events[-1].end:
            break

    return logs
