/**
 * LeafletMap — drop-in replacement for scattermapbox Plotly figures.
 * Accepts either:
 *   - points: [{lat, lon, label, value, color}]
 *   - plotlyFig: a Plotly figure with scattermapbox traces (auto-converted)
 */
import { useEffect } from "react";
import { MapContainer, TileLayer, CircleMarker, Popup, Polyline, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl:       "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl:     "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

const DARK_TILE  = "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png";
const LIGHT_TILE = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";
const SAT_TILE   = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}";
const DARK_ATTR  = '© <a href="https://carto.com/">CARTO</a> © <a href="https://openstreetmap.org">OSM</a>';
const OSM_ATTR   = '© <a href="https://openstreetmap.org">OpenStreetMap</a>';

function AutoFit({ points }) {
  const map = useMap();
  useEffect(() => {
    if (points?.length > 0) {
      const valid = points.filter(p => p.lat != null && p.lon != null && !isNaN(p.lat) && !isNaN(p.lon));
      if (valid.length === 1) {
        map.setView([valid[0].lat, valid[0].lon], 10);
      } else if (valid.length > 1) {
        map.fitBounds(valid.map(p => [p.lat, p.lon]), { padding: [30, 30] });
      }
    }
  }, [points, map]);
  return null;
}

/** Convert a Plotly scattermapbox figure to points array */
function figToPoints(fig) {
  if (!fig?.data) return [];
  const points = [];
  fig.data.forEach(trace => {
    if (!trace.lat) return;
    const lats = trace.lat;
    const lons = trace.lon || [];
    const texts = trace.text || [];
    const colors = Array.isArray(trace.marker?.color) ? trace.marker.color : [];
    for (let i = 0; i < lats.length; i++) {
      if (lats[i] == null || lons[i] == null) continue;
      points.push({
        lat: parseFloat(lats[i]),
        lon: parseFloat(lons[i]),
        label: Array.isArray(texts) ? texts[i] : texts,
        value: typeof colors[i] === "number" ? colors[i] : null,
        color: typeof colors[i] === "string" ? colors[i] : "#6366f1",
        isLine: trace.mode === "lines",
      });
    }
  });
  return points;
}

/** Simple color scale: blue → green → yellow → red */
function valueToColor(val, min, max) {
  if (val == null || isNaN(val)) return "#6366f1";
  const t = Math.max(0, Math.min(1, (val - min) / (max - min || 1)));
  const r = Math.round(t * 220);
  const g = Math.round(100 + t * 100);
  const b = Math.round(240 - t * 200);
  return `rgb(${r},${g},${b})`;
}

export default function LeafletMap({
  points: pointsProp,
  plotlyFig,
  height = "380px",
  dark = true,
  satellite = false,
  center,
  zoom = 3,
}) {
  const rawPoints = pointsProp || figToPoints(plotlyFig);
  const points = rawPoints.filter(p => !isNaN(p.lat) && !isNaN(p.lon));

  const vals = points.map(p => p.value).filter(v => v != null && !isNaN(v));
  const minVal = Math.min(...vals, 0);
  const maxVal = Math.max(...vals, 1);
  const maxAbs = Math.max(...points.map(p => Math.abs(p.value || 0)), 1);

  const tileUrl  = satellite ? SAT_TILE : dark ? DARK_TILE : LIGHT_TILE;
  const tileAttr = satellite ? '© Esri' : dark ? DARK_ATTR : OSM_ATTR;

  const defaultCenter = center ||
    (points.length > 0
      ? [points.reduce((s, p) => s + p.lat, 0) / points.length,
         points.reduce((s, p) => s + p.lon, 0) / points.length]
      : [20, 0]);

  const linePoints = points.filter(p => p.isLine);
  const markerPoints = points.filter(p => !p.isLine);

  return (
    <div style={{ height, borderRadius: 10, overflow: "hidden" }}>
      <MapContainer
        center={defaultCenter}
        zoom={zoom}
        style={{ height: "100%", width: "100%", background: "#09090b" }}
        scrollWheelZoom
      >
        <TileLayer url={tileUrl} attribution={tileAttr} />
        {points.length > 0 && <AutoFit points={points} />}

        {/* Lines */}
        {linePoints.length > 1 && (
          <Polyline
            positions={linePoints.map(p => [p.lat, p.lon])}
            pathOptions={{ color: "#ef4444", weight: 2, opacity: 0.8 }}
          />
        )}

        {/* Markers */}
        {markerPoints.map((p, i) => {
          const color = p.value != null
            ? valueToColor(p.value, minVal, maxVal)
            : (p.color || "#6366f1");
          const radius = p.value != null
            ? 5 + (Math.abs(p.value) / maxAbs) * 15
            : 8;
          return (
            <CircleMarker
              key={i}
              center={[p.lat, p.lon]}
              radius={radius}
              pathOptions={{ color, fillColor: color, fillOpacity: 0.8, weight: 1 }}
            >
              <Popup>
                <div style={{ minWidth: 120 }}>
                  {p.label && <div><strong>{String(p.label).slice(0, 80)}</strong></div>}
                  {p.value != null && <div style={{ marginTop: 4 }}>Value: <strong>{typeof p.value === "number" ? p.value.toFixed(2) : p.value}</strong></div>}
                </div>
              </Popup>
            </CircleMarker>
          );
        })}
      </MapContainer>
    </div>
  );
}
