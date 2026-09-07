/**
 * OSMMap — OpenStreetMap via React-Leaflet. No API key needed.
 * Props:
 *   points: [{lat, lon, label, value, color?}]
 *   center: [lat, lon]
 *   zoom: number
 *   height: string
 *   tileStyle: "street" | "dark" | "satellite"
 */
import { useEffect } from "react";
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";

// Fix Leaflet default icon path issue with bundlers
import L from "leaflet";
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl:       "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl:     "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

const TILES = {
  street:    "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
  dark:      "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
  satellite: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
};

const ATTR = {
  street:    '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
  dark:      '© <a href="https://carto.com/">CARTO</a> © <a href="https://www.openstreetmap.org/copyright">OSM</a>',
  satellite: '© <a href="https://www.esri.com/">Esri</a>',
};

function FitBounds({ points }) {
  const map = useMap();
  useEffect(() => {
    if (points?.length > 1) {
      const bounds = points.map(p => [p.lat, p.lon]);
      map.fitBounds(bounds, { padding: [30, 30] });
    }
  }, [points, map]);
  return null;
}

export default function OSMMap({
  points = [],
  center = [20, 0],
  zoom = 2,
  height = "320px",
  tileStyle = "dark",
  showControls = true,
}) {
  const maxVal = Math.max(...points.map(p => p.value || 1), 1);

  return (
    <div style={{ height, borderRadius: 10, overflow: "hidden", position: "relative" }}>
      <MapContainer
        center={center}
        zoom={zoom}
        style={{ height: "100%", width: "100%", background: "#09090b" }}
        zoomControl={showControls}
        scrollWheelZoom={true}
      >
        <TileLayer url={TILES[tileStyle]} attribution={ATTR[tileStyle]} />
        {points.length > 1 && <FitBounds points={points} />}
        {points.map((p, i) => {
          const radius = 6 + (p.value / maxVal) * 18;
          const color  = p.color || "#6366f1";
          return (
            <CircleMarker
              key={i}
              center={[p.lat, p.lon]}
              radius={radius}
              pathOptions={{
                color,
                fillColor: color,
                fillOpacity: 0.75,
                weight: 1.5,
              }}
            >
              <Popup>
                <div style={{ minWidth: 120 }}>
                  <strong>{p.label || `Point ${i + 1}`}</strong>
                  {p.value != null && (
                    <div style={{ marginTop: 4, color: "#555" }}>
                      Value: <strong>{p.value.toLocaleString()}</strong>
                    </div>
                  )}
                  {p.extra && <div style={{ marginTop: 4, fontSize: 12, color: "#777" }}>{p.extra}</div>}
                </div>
              </Popup>
            </CircleMarker>
          );
        })}
      </MapContainer>
    </div>
  );
}
