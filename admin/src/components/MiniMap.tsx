/* Thin Leaflet wrapper — OSM tiles, no API key. CircleMarkers avoid the
   classic bundler problem with Leaflet's default marker image assets. */

import { CircleMarker, MapContainer, Polyline, TileLayer, Tooltip } from "react-leaflet";
import "leaflet/dist/leaflet.css";

export function MiniMap({
  points,
  trail = false,
  height = 320,
}: {
  points: { lat: number; lng: number; label?: string }[];
  trail?: boolean;
  height?: number;
}) {
  if (points.length === 0) return null;
  const center: [number, number] = [points[0].lat, points[0].lng];
  return (
    <div className="map-box" style={{ height }}>
      <MapContainer center={center} zoom={14} scrollWheelZoom={false}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {trail && points.length > 1 && (
          <Polyline
            positions={points.map((p) => [p.lat, p.lng] as [number, number])}
            pathOptions={{ color: "#0875FF", weight: 3, opacity: 0.7 }}
          />
        )}
        {points.map((p, i) => (
          <CircleMarker
            key={`${p.lat}-${p.lng}-${i}`}
            center={[p.lat, p.lng]}
            radius={i === 0 ? 9 : 6}
            pathOptions={{
              color: "white",
              weight: 2,
              fillColor: i === 0 ? "#EB493D" : "#0875FF",
              fillOpacity: 0.95,
            }}
          >
            {p.label && <Tooltip direction="top">{p.label}</Tooltip>}
          </CircleMarker>
        ))}
      </MapContainer>
    </div>
  );
}
