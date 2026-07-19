import { useState } from "react";
import "./TripForm.css";

const initialState = {
  current_location: "",
  pickup_location: "",
  dropoff_location: "",
  current_cycle_used: "",
};

const initialManifest = {
  driver_name: "",
  driver_number: "",
  driver_initials: "",
  co_driver: "",
  truck_number: "",
  trailer_number: "",
  carrier_name: "",
  home_terminal_address: "",
  shipper: "",
  commodity: "",
  load_number: "",
};

const MANIFEST_FIELDS = [
  ["driver_name", "Driver name"],
  ["driver_number", "Driver number"],
  ["driver_initials", "Driver initials"],
  ["co_driver", "Co-driver (or NA)"],
  ["truck_number", "Truck / tractor #"],
  ["trailer_number", "Trailer #"],
  ["carrier_name", "Carrier name"],
  ["home_terminal_address", "Home terminal address"],
  ["shipper", "Shipper"],
  ["commodity", "Commodity"],
  ["load_number", "Load / manifest #"],
];

export default function TripForm({ onSubmit, loading }) {
  const [form, setForm] = useState(initialState);
  const [manifest, setManifest] = useState(initialManifest);
  const [validationError, setValidationError] = useState(null);

  function update(field) {
    return (e) => setForm((prev) => ({ ...prev, [field]: e.target.value }));
  }

  function updateManifest(field) {
    return (e) => setManifest((prev) => ({ ...prev, [field]: e.target.value }));
  }

  function handleSubmit(e) {
    e.preventDefault();
    const cycle = Number(form.current_cycle_used);
    if (!form.current_location || !form.pickup_location || !form.dropoff_location) {
      setValidationError("All three locations are required.");
      return;
    }
    if (Number.isNaN(cycle) || cycle < 0 || cycle > 70) {
      setValidationError("Cycle hours used must be a number between 0 and 70.");
      return;
    }
    setValidationError(null);
    onSubmit({
      current_location: form.current_location,
      pickup_location: form.pickup_location,
      dropoff_location: form.dropoff_location,
      current_cycle_used: cycle,
      ...manifest,
    });
  }

  return (
    <form className="trip-form" onSubmit={handleSubmit}>
      <p className="trip-form__ticket-no">TICKET&nbsp;#{new Date().getFullYear()}-01</p>

      <label className="trip-form__field">
        <span>Current location</span>
        <input
          type="text"
          placeholder="e.g. Green Bay, WI"
          value={form.current_location}
          onChange={update("current_location")}
          autoComplete="off"
        />
      </label>

      <label className="trip-form__field">
        <span>Pickup location</span>
        <input
          type="text"
          placeholder="e.g. Fond du Lac, WI"
          value={form.pickup_location}
          onChange={update("pickup_location")}
          autoComplete="off"
        />
      </label>

      <label className="trip-form__field">
        <span>Drop-off location</span>
        <input
          type="text"
          placeholder="e.g. Indianapolis, IN"
          value={form.dropoff_location}
          onChange={update("dropoff_location")}
          autoComplete="off"
        />
      </label>

      <label className="trip-form__field">
        <span>Current cycle used (hrs)</span>
        <input
          type="number"
          min="0"
          max="70"
          step="0.25"
          placeholder="0 &ndash; 70"
          value={form.current_cycle_used}
          onChange={update("current_cycle_used")}
        />
      </label>

      <details className="trip-form__manifest">
        <summary>Carrier &amp; shipment details (optional)</summary>
        <p className="trip-form__manifest-hint">
          Fills in the log sheet header. Leave blank to use placeholders.
        </p>
        {MANIFEST_FIELDS.map(([key, label]) => (
          <label className="trip-form__field" key={key}>
            <span>{label}</span>
            <input
              type="text"
              value={manifest[key]}
              onChange={updateManifest(key)}
              autoComplete="off"
            />
          </label>
        ))}
      </details>

      {validationError && <p className="trip-form__error">{validationError}</p>}

      <button className="trip-form__submit" type="submit" disabled={loading}>
        {loading ? "Routing\u2026" : "Plan Trip"}
      </button>

      <ul className="trip-form__assumptions">
        <li>70&nbsp;hrs / 8&#8209;day cycle, no adverse driving conditions</li>
        <li>Fuel stop at least every 1,000 miles</li>
        <li>1 hour on-duty each for pickup and drop-off</li>
      </ul>
    </form>
  );
}
