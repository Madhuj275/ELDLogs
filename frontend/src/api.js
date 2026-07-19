import axios from "axios";

// In production, set VITE_API_BASE_URL to your deployed Django backend
// (e.g. https://your-app.onrender.com/api). Falls back to local dev server.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api";

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" },
});

export async function planTrip(payload) {
  const { data } = await client.post("/trips/plan/", payload);
  return data;
}

export async function fetchTripHistory() {
  const { data } = await client.get("/trips/");
  return data;
}

export default client;
