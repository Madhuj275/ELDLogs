import { useState } from "react";
import TripForm from "./components/TripForm";
import MapView from "./components/MapView";
import LogSheet from "./components/LogSheet";
import { planTrip } from "./api";
import "./App.css";

export default function App() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handlePlan(payload) {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await planTrip(payload);
      setResult(data);
    } catch (err) {
      const message =
        err?.response?.data?.error ||
        "Couldn't plan that trip. Check the locations and try again.";
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="app-header__mark">
          <span className="app-header__bolt" aria-hidden="true" />
          <div>
            <p className="app-header__eyebrow">Route &amp; Hours-of-Service Planner</p>
            <h1 className="app-header__title">ELD Trip Planner</h1>
          </div>
        </div>
        <p className="app-header__meta">
          Property-carrying &middot; 70&#8202;hrs / 8&#8202;days &middot; no adverse conditions
        </p>
      </header>

      <main className="app-main">
        <aside className="app-sidebar">
          <TripForm onSubmit={handlePlan} loading={loading} />
          {error && <p className="app-error" role="alert">{error}</p>}
        </aside>

        <section className="app-results">
          {!result && !loading && (
            <div className="app-placeholder">
              <p>
                Enter a current location, pickup, drop-off, and cycle hours used
                to generate a route and FMCSA-style daily log sheets.
              </p>
            </div>
          )}

          {loading && (
            <div className="app-placeholder">
              <p>Calculating route and duty-status schedule&hellip;</p>
            </div>
          )}

          {result && (
            <>
              <div className="app-summary">
                <div className="app-summary__stat">
                  <span className="app-summary__value">
                    {result.route.distance_miles.toLocaleString()}
                  </span>
                  <span className="app-summary__label">Total miles</span>
                </div>
                <div className="app-summary__stat">
                  <span className="app-summary__value">
                    {result.route.duration_hours.toFixed(1)}
                  </span>
                  <span className="app-summary__label">Drive hours</span>
                </div>
                <div className="app-summary__stat">
                  <span className="app-summary__value">{result.daily_logs.length}</span>
                  <span className="app-summary__label">Log sheet{result.daily_logs.length !== 1 ? "s" : ""}</span>
                </div>
                <div className="app-summary__stat">
                  <span className="app-summary__value">{result.stops.length}</span>
                  <span className="app-summary__label">Stops &amp; breaks</span>
                </div>
              </div>

              <MapView route={result.route} stops={result.stops} />

              <div className="app-logs">
                <h2 className="app-logs__title">Daily Log Sheets</h2>
                {result.daily_logs.map((log, idx) => (
                  <LogSheet
                    key={log.date}
                    log={log}
                    dayIndex={idx + 1}
                    manifest={result.trip.manifest}
                    route={result.route}
                  />
                ))}
              </div>
            </>
          )}
        </section>
      </main>
    </div>
  );
}
