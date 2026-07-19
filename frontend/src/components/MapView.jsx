import { MapContainer, TileLayer, Polyline, Marker, Popup } from "react-leaflet";
import L from "leaflet";
import "./MapView.css";

// Leaflet's default marker icons reference bundled assets that don't resolve
// under Vite; point them at the CDN instead.
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

const stopIcon = (color) =>
  new L.DivIcon({
    className: "map-stop-icon",
    html: `<span style="background:${color}"></span>`,
    iconSize: [16, 16],
    iconAnchor: [8, 8],
  });

const ICONS = {
  waypoint: stopIcon("#f2a93b"),
  D: stopIcon("#5b6b78"),
  ON: stopIcon("#2f6f4f"),
  OFF: stopIcon("#b23a2e"),
};

function labelFor(stop) {
  const start = new Date(stop.start);
  return `${stop.label} — ${start.toLocaleString()} (${stop.duration_hours}h)`;
}

export default function MapView({ route, stops }) {
  const fullGeometry = [...route.leg_to_pickup, ...route.leg_to_dropoff];
  if (!fullGeometry.length) return null;

  const center = fullGeometry[Math.floor(fullGeometry.length / 2)];
  const { current, pickup, dropoff } = route.waypoints;

  return (
    <div className="map-view">
      <MapContainer center={center} zoom={6} scrollWheelZoom={true} className="map-view__container">
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <Polyline positions={route.leg_to_pickup} pathOptions={{ color: "#f2a93b", weight: 4 }} />
        <Polyline positions={route.leg_to_dropoff} pathOptions={{ color: "#2f6f4f", weight: 4 }} />

        <Marker position={[current.lat, current.lon]} icon={ICONS.waypoint}>
          <Popup>Current location: {current.display_name}</Popup>
        </Marker>
        <Marker position={[pickup.lat, pickup.lon]} icon={ICONS.waypoint}>
          <Popup>Pickup: {pickup.display_name}</Popup>
        </Marker>
        <Marker position={[dropoff.lat, dropoff.lon]} icon={ICONS.waypoint}>
          <Popup>Drop-off: {dropoff.display_name}</Popup>
        </Marker>

        {stops
          .filter((s) => s.location)
          .map((stop, idx) => (
            <Marker
              key={idx}
              position={[stop.location.lat, stop.location.lon]}
              icon={ICONS[stop.type] || ICONS.ON}
            >
              <Popup>{labelFor(stop)}</Popup>
            </Marker>
          ))}
      </MapContainer>

      <div className="map-view__legend">
        <span><i style={{ background: "#f2a93b" }} /> To pickup</span>
        <span><i style={{ background: "#2f6f4f" }} /> To drop-off</span>
        <span><i style={{ background: "#5b6b78" }} /> Driving stop</span>
        <span><i style={{ background: "#b23a2e" }} /> Rest / break</span>
      </div>
    </div>
  );
}
