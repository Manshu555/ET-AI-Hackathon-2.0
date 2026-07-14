"use client";
import { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';

const SupplyChainMap = dynamic(
  () => import('@/components/SupplyChainMap'),
  { ssr: false, loading: () => <div className="h-[500px] w-full flex items-center justify-center text-gray-400">Loading map...</div> }
);

interface Shipment {
  id: string;
  equipment_type: string;
  description: string;
  status: string;
  risk_score: number;
  current_lat: number | null;
  current_lng: number | null;
  destination_lat: number | null;
  destination_lng: number | null;
  required_on_site: string | null;
  days_until_required?: number;
  mitigation_suggestions?: string[];
}

export default function SupplyChainPage() {
  const [shipments, setShipments] = useState<Shipment[]>([]);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState<'list' | 'map'>('list');

  useEffect(() => {
    // Load both map data and at-risk data
    Promise.all([
      fetch('http://localhost:8000/api/v1/dashboard/summary').then(r => r.json()).catch(() => null),
    ]).then(([summary]) => {
      // For the demo, show hardcoded shipment data from our seed
      const demoShipments: Shipment[] = [
        { id: '1', equipment_type: 'Switchgear', description: 'Medium Voltage Switchgear Panel', status: 'at_risk', risk_score: 91.0, current_lat: 30.04, current_lng: 31.24, destination_lat: 19.08, destination_lng: 72.88, required_on_site: new Date(Date.now() + 10 * 86400000).toISOString().split('T')[0], days_until_required: 10, mitigation_suggestions: ['Consider expedited freight', 'Contact vendor for updated ETA', 'Check alternate vendor availability'] },
        { id: '2', equipment_type: 'Chiller', description: '500kW Centrifugal Chiller Unit', status: 'at_risk', risk_score: 85.0, current_lat: 13.08, current_lng: 80.27, destination_lat: 19.08, destination_lng: 72.88, required_on_site: new Date(Date.now() + 15 * 86400000).toISOString().split('T')[0], days_until_required: 15, mitigation_suggestions: ['Contact vendor for updated ETA', 'Increase tracking frequency'] },
        { id: '3', equipment_type: 'UPS', description: '2MW UPS System - Liebert EXL S1', status: 'in_transit', risk_score: 72.0, current_lat: 22.32, current_lng: 114.17, destination_lat: 19.08, destination_lng: 72.88, required_on_site: new Date(Date.now() + 25 * 86400000).toISOString().split('T')[0], days_until_required: 25, mitigation_suggestions: ['Increase tracking frequency'] },
        { id: '4', equipment_type: 'Generator', description: '2000kVA Diesel Generator Set', status: 'on_track', risk_score: 18.0, current_lat: 51.51, current_lng: -0.13, destination_lat: 19.08, destination_lng: 72.88, required_on_site: new Date(Date.now() + 50 * 86400000).toISOString().split('T')[0], days_until_required: 50, mitigation_suggestions: ['Shipment on track'] },
      ];
      setShipments(demoShipments);
      setLoading(false);
    });
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'at_risk': return 'bg-red-500/20 text-red-400 border-red-500/30';
      case 'watch': case 'in_transit': return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
      case 'delivered': case 'on_track': return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
      default: return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
    }
  };

  const getEquipmentIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'ups': return '🔋';
      case 'generator': return '⚡';
      case 'chiller': return '❄️';
      case 'switchgear': return '🔌';
      default: return '📦';
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold">Supply Chain Visibility</h1>
          <p className="text-gray-400 mt-1 text-sm">Track critical long-lead equipment and flag at-risk deliveries</p>
        </div>
        <div className="flex glass rounded-xl overflow-hidden">
          <button onClick={() => setView('list')} className={`px-4 py-2 text-sm font-medium transition-colors ${view === 'list' ? 'bg-primary text-white' : 'text-gray-400 hover:text-white'}`}>
            List View
          </button>
          <button onClick={() => setView('map')} className={`px-4 py-2 text-sm font-medium transition-colors ${view === 'map' ? 'bg-primary text-white' : 'text-gray-400 hover:text-white'}`}>
            Map View
          </button>
        </div>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <div className="glass p-5 rounded-2xl border-t-4 border-t-red-500">
          <p className="text-xs text-gray-400 mb-2">At Risk</p>
          <h2 className="text-2xl font-bold text-red-400">{shipments.filter(s => s.risk_score >= 70).length}</h2>
        </div>
        <div className="glass p-5 rounded-2xl border-t-4 border-t-amber-500">
          <p className="text-xs text-gray-400 mb-2">Watch</p>
          <h2 className="text-2xl font-bold text-amber-400">{shipments.filter(s => s.risk_score >= 40 && s.risk_score < 70).length}</h2>
        </div>
        <div className="glass p-5 rounded-2xl border-t-4 border-t-emerald-500">
          <p className="text-xs text-gray-400 mb-2">On Track</p>
          <h2 className="text-2xl font-bold text-emerald-400">{shipments.filter(s => s.risk_score < 40).length}</h2>
        </div>
        <div className="glass p-5 rounded-2xl border-t-4 border-t-blue-500">
          <p className="text-xs text-gray-400 mb-2">Total</p>
          <h2 className="text-2xl font-bold">{shipments.length}</h2>
        </div>
      </div>

      {view === 'list' ? (
        <div className="space-y-4">
          {loading ? (
            <div className="glass p-8 rounded-2xl text-center text-gray-400">Loading shipments...</div>
          ) : (
            shipments.sort((a, b) => b.risk_score - a.risk_score).map(ship => (
              <div key={ship.id} className="glass p-6 rounded-2xl hover:border-white/20 transition-all">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-4">
                    <div className="text-3xl">{getEquipmentIcon(ship.equipment_type)}</div>
                    <div>
                      <div className="flex items-center gap-3">
                        <h3 className="font-semibold">{ship.equipment_type}</h3>
                        <span className={`text-[10px] px-2 py-0.5 rounded-full font-semibold border ${getStatusColor(ship.status)}`}>
                          {ship.status.replace('_', ' ').toUpperCase()}
                        </span>
                      </div>
                      <p className="text-sm text-gray-400 mt-1">{ship.description}</p>
                      {ship.required_on_site && (
                        <p className="text-xs text-gray-500 mt-2">
                          Required on-site: <span className={ship.days_until_required && ship.days_until_required <= 14 ? 'text-red-400 font-semibold' : 'text-gray-300'}>
                            {ship.required_on_site} ({ship.days_until_required} days)
                          </span>
                        </p>
                      )}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="flex items-center gap-2">
                      <div className="h-2 w-24 bg-gray-700 rounded-full overflow-hidden">
                        <div className={`h-full rounded-full ${ship.risk_score >= 70 ? 'bg-red-500' : ship.risk_score >= 40 ? 'bg-amber-500' : 'bg-emerald-500'}`}
                             style={{ width: `${ship.risk_score}%` }} />
                      </div>
                      <span className={`text-lg font-bold ${ship.risk_score >= 70 ? 'text-red-400' : ship.risk_score >= 40 ? 'text-amber-400' : 'text-emerald-400'}`}>
                        {ship.risk_score}%
                      </span>
                    </div>
                    <p className="text-[10px] text-gray-500 mt-1">Risk Score</p>
                  </div>
                </div>
                {ship.mitigation_suggestions && ship.mitigation_suggestions.length > 0 && ship.risk_score >= 40 && (
                  <div className="mt-4 pt-4 border-t border-white/5">
                    <p className="text-xs text-gray-500 mb-2 font-semibold uppercase tracking-wider">Mitigation Suggestions</p>
                    <ul className="space-y-1">
                      {ship.mitigation_suggestions.map((s, i) => (
                        <li key={i} className="text-xs text-gray-300 flex items-start gap-2">
                          <span className="text-amber-400 mt-0.5">→</span> {s}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      ) : (
        <div className="glass rounded-2xl p-6">
          <SupplyChainMap shipments={shipments} />
        </div>
      )}
    </div>
  );
}
