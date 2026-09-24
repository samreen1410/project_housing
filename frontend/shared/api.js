// Shared across every page — one place to change the backend URL.
const API_BASE = "http://127.0.0.1:8000"; // update if backend runs elsewhere

async function fetchRegions() {
  const res = await fetch(`${API_BASE}/regions/`);
  if (!res.ok) throw new Error("Could not reach the regions endpoint");
  return res.json();
}

function money(value) {
  return "$" + Number(value).toLocaleString("en-CA", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}
