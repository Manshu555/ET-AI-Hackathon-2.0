"use client";
import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { useEffect } from 'react';

// Fix for default marker icons in Leaflet + Next.js
const customIcon = (color: string) => L.divIcon({
  className: 'custom-leaflet-marker',
  html: `<div style="background-color: ${color}; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 0 4px rgba(255,255,255,0.2);"></div>`,
  iconSize: [12, 12],
  iconAnchor: [6, 6]
});

const destinationIcon = L.divIcon({
  className: 'custom-leaflet-marker',
  html: `<div style="background-color: #3b82f6; width: 16px; height: 16px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.4); animation: pulse 2s infinite;"></div><div style="position: absolute; top: 20px; left: -20px; width: 60px; text-align: center; color: #1e293b; font-weight: bold; font-size: 10px; background: white; padding: 2px 4px; border-radius: 4px; border: 1px solid #e2e8f0;">📍 Mumbai</div>`,
  iconSize: [16, 16],
  iconAnchor: [8, 8]
});

interface Shipment {
  id: string;
  equipment_type: string;
  description: string;
  status: string;
  risk_score: number;
  current_lat: number | null;
  current_lng: number | null;
}

// Generates points along a quadratic bezier curve to create a nice arc between two coordinates
function getCurvePoints(start: [number, number], end: [number, number]): [number, number][] {
  const points: [number, number][] = [];
  const [lat1, lng1] = start;
  const [lat2, lng2] = end;
  
  // Midpoint
  const midLat = (lat1 + lat2) / 2;
  const midLng = (lng1 + lng2) / 2;
  
  // Offset the control point upwards (latitude) based on the distance to create an arc
  const distance = Math.sqrt(Math.pow(lat2 - lat1, 2) + Math.pow(lng2 - lng1, 2));
  // A slight positive offset curves the line 'upwards' visually on the map
  const controlLat = midLat + (distance * 0.2); 
  const controlLng = midLng;
  
  // Generate 20 points along the curve
  for (let i = 0; i <= 20; i++) {
    const t = i / 20;
    const lat = (1 - t) * (1 - t) * lat1 + 2 * (1 - t) * t * controlLat + t * t * lat2;
    const lng = (1 - t) * (1 - t) * lng1 + 2 * (1 - t) * t * controlLng + t * t * lng2;
    points.push([lat, lng]);
  }
  return points;
}

export default function SupplyChainMap({ shipments }: { shipments: Shipment[] }) {
  useEffect(() => {
    // Add pulse animation styles for the destination marker
    const style = document.createElement('style');
    style.innerHTML = `
      @keyframes pulse {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.7); }
        70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(59, 130, 246, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(59, 130, 246, 0); }
      }
      .leaflet-container {
        background: #0b1121;
        font-family: inherit;
      }
      /* Style popups for dark mode natively */
      .leaflet-popup-content-wrapper,
      .leaflet-popup-tip {
        background: #1e293b !important;
        color: #f8fafc !important;
        border-radius: 8px;
      }
      .leaflet-popup-content {
        margin: 12px;
      }
    `;
    document.head.appendChild(style);
    return () => { document.head.removeChild(style); };
  }, []);

  return (
    <div style={{ height: '500px', width: '100%', borderRadius: '0.75rem', overflow: 'hidden' }}>
      <MapContainer 
        center={[25, 45]} 
        zoom={3} 
        style={{ height: '100%', width: '100%', zIndex: 0 }}
        scrollWheelZoom={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />
        
        {/* Destination Marker */}
        <Marker position={[19.08, 72.88]} icon={destinationIcon}>
          <Popup>
            <div>
              <strong>Project Site</strong><br/>
              Mumbai, India
            </div>
          </Popup>
        </Marker>

        {/* Shipment Markers and Spline Curves */}
        {shipments.map((ship) => {
          if (!ship.current_lat || !ship.current_lng) return null;
          const color = ship.risk_score >= 70 ? "#ef4444" : ship.risk_score >= 40 ? "#f59e0b" : "#10b981";
          
          const startCoord: [number, number] = [ship.current_lat, ship.current_lng];
          const destCoord: [number, number] = [19.08, 72.88]; // Mumbai
          const curvePath = getCurvePoints(startCoord, destCoord);

          return (
            <div key={ship.id}>
              {/* Spline line connecting shipment to destination */}
              <Polyline 
                positions={curvePath} 
                color={color} 
                weight={2} 
                opacity={0.6}
                dashArray="5, 8"
              />
              
              <Marker 
                position={startCoord}
                icon={customIcon(color)}
              >
                <Popup>
                  <div>
                    <strong>{ship.equipment_type}</strong><br/>
                    {ship.description}<br/>
                    Risk Score: {ship.risk_score}%
                  </div>
                </Popup>
              </Marker>
            </div>
          );
        })}
      </MapContainer>
    </div>
  );
}
