"use client";

import { useEffect } from 'react';
import L from 'leaflet';
import { MapContainer, Marker, Polyline, TileLayer, Tooltip, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

export interface MapShipment {
  id: string;
  equipment_type: string;
  description?: string | null;
  vendor_name?: string | null;
  status: string;
  risk_score: number;
  current_lat?: number | null;
  current_lng?: number | null;
  destination_lat?: number | null;
  destination_lng?: number | null;
  required_on_site?: string | null;
}

const riskColor = (score: number) => score >= 70 ? '#ef4444' : score >= 40 ? '#f59e0b' : '#10b981';

const markerIcon = (color: string, selected = false) => L.divIcon({
  className: 'shipment-marker',
  html: `<span style="display:block;width:${selected ? 18 : 14}px;height:${selected ? 18 : 14}px;border-radius:999px;background:${color};border:3px solid #fff;box-shadow:0 0 0 ${selected ? 5 : 3}px ${color}55"></span>`,
  iconSize: [22, 22], iconAnchor: [11, 11],
});

const destinationIcon = L.divIcon({
  className: 'shipment-marker',
  html: '<span style="display:grid;place-items:center;width:28px;height:28px;border-radius:9px;background:#2563eb;border:2px solid #fff;box-shadow:0 4px 12px #2563eb88;color:#fff;font-size:14px">⌂</span>',
  iconSize: [28, 28], iconAnchor: [14, 14],
});

function FitVisible({ shipments, resetToken }: { shipments: MapShipment[]; resetToken: number }) {
  const map = useMap();
  useEffect(() => {
    const points: L.LatLngTuple[] = [];
    shipments.forEach(s => {
      if (s.current_lat != null && s.current_lng != null) points.push([s.current_lat, s.current_lng]);
      if (s.destination_lat != null && s.destination_lng != null) points.push([s.destination_lat, s.destination_lng]);
    });
    if (points.length > 1) map.fitBounds(points, { padding: [48, 48], maxZoom: 5 });
    else if (points.length === 1) map.setView(points[0], 5);
  }, [map, shipments, resetToken]);
  return null;
}

function FocusShipment({ shipment }: { shipment: MapShipment | null }) {
  const map = useMap();
  useEffect(() => {
    if (shipment?.current_lat != null && shipment.current_lng != null) map.flyTo([shipment.current_lat, shipment.current_lng], 5, { duration: 0.6 });
  }, [map, shipment]);
  return null;
}

export default function SupplyChainMap({ shipments, selectedId, onSelect, showRoutes, resetToken }: {
  shipments: MapShipment[]; selectedId: string | null; onSelect: (id: string) => void; showRoutes: boolean; resetToken: number;
}) {
  const visible = shipments.filter(s => s.current_lat != null && s.current_lng != null);
  const selected = shipments.find(s => s.id === selectedId) || null;
  const destination = visible.find(s => s.destination_lat != null && s.destination_lng != null);

  return (
    <div className="h-[520px] overflow-hidden rounded-2xl border border-white/10">
      <MapContainer center={[20, 72]} zoom={3} className="h-full w-full" scrollWheelZoom>
        <TileLayer attribution="&copy; OpenStreetMap &copy; CARTO" url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png" />
        <FitVisible shipments={visible} resetToken={resetToken} />
        <FocusShipment shipment={selected} />
        {destination?.destination_lat != null && destination.destination_lng != null && (
          <Marker position={[destination.destination_lat, destination.destination_lng]} icon={destinationIcon}>
            <Tooltip direction="bottom" permanent>Project destination</Tooltip>
          </Marker>
        )}
        {visible.map(shipment => {
          const selectedRoute = shipment.id === selectedId;
          const color = riskColor(shipment.risk_score);
          const destinationPoint = shipment.destination_lat != null && shipment.destination_lng != null
            ? [shipment.destination_lat, shipment.destination_lng] as [number, number] : null;
          return (
            <div key={shipment.id}>
              {showRoutes && destinationPoint && (
                <Polyline positions={[[shipment.current_lat!, shipment.current_lng!], destinationPoint]} color={color}
                  weight={selectedId && !selectedRoute ? 1 : selectedRoute ? 4 : 2} opacity={selectedId && !selectedRoute ? 0.15 : 0.75}
                  dashArray={shipment.status === 'delivered' ? undefined : '8 8'} />
              )}
              <Marker position={[shipment.current_lat!, shipment.current_lng!]} icon={markerIcon(color, selectedRoute)} eventHandlers={{ click: () => onSelect(shipment.id) }}>
                <Tooltip direction="top" offset={[0, -12]}>{shipment.equipment_type} · {Math.round(shipment.risk_score)}% risk</Tooltip>
              </Marker>
            </div>
          );
        })}
      </MapContainer>
    </div>
  );
}
