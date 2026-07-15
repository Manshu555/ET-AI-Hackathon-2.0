"use client";

import { useEffect, useMemo, useState } from 'react';
import dynamic from 'next/dynamic';
import { apiFetch } from '@/lib/api-client';
import type { MapShipment } from '@/components/SupplyChainMap';

const SupplyChainMap = dynamic(() => import('@/components/SupplyChainMap'), {
  ssr: false,
  loading: () => <div className="glass flex h-[520px] items-center justify-center rounded-2xl text-sm text-gray-400">Loading map…</div>,
});

type StatusFilter = 'all' | 'at_risk' | 'watch' | 'on_track' | 'delivered';

const statusStyle: Record<string, string> = {
  at_risk: 'bg-red-500/15 text-red-300 border-red-500/25', watch: 'bg-amber-500/15 text-amber-300 border-amber-500/25',
  on_track: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/25', delivered: 'bg-slate-500/15 text-slate-300 border-slate-500/25',
};

function daysUntil(date?: string | null) {
  if (!date) return null;
  return Math.ceil((new Date(date).getTime() - Date.now()) / 86_400_000);
}

export default function SupplyChainPage() {
  const [shipments, setShipments] = useState<MapShipment[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [query, setQuery] = useState('');
  const [status, setStatus] = useState<StatusFilter>('all');
  const [atRiskOnly, setAtRiskOnly] = useState(false);
  const [showRoutes, setShowRoutes] = useState(true);
  const [resetToken, setResetToken] = useState(0);

  useEffect(() => {
    apiFetch<MapShipment[]>('/shipments/map')
      .then(data => { setShipments(data); setSelectedId(data[0]?.id || null); })
      .catch(error => console.error('Failed to load shipments', error))
      .finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(() => shipments.filter(s => {
    const search = `${s.equipment_type} ${s.description || ''} ${s.vendor_name || ''}`.toLowerCase();
    return (!query || search.includes(query.toLowerCase())) && (status === 'all' || s.status === status) && (!atRiskOnly || s.risk_score >= 70);
  }), [shipments, query, status, atRiskOnly]);
  const selected = shipments.find(s => s.id === selectedId) || null;
  const kpis = {
    total: shipments.length, atRisk: shipments.filter(s => s.risk_score >= 70).length,
    dueSoon: shipments.filter(s => { const days = daysUntil(s.required_on_site); return days !== null && days >= 0 && days <= 14; }).length,
    delivered: shipments.filter(s => s.status === 'delivered').length,
  };

  return <div className="space-y-6">
    <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
      <div><h1 className="text-3xl font-bold">Supply Chain Control Tower</h1><p className="mt-1 text-sm text-gray-400">Live location, delivery risk, and mitigation visibility for long-lead equipment.</p></div>
      <button onClick={() => setResetToken(value => value + 1)} className="rounded-lg border border-white/10 px-3 py-2 text-sm text-gray-300 hover:bg-white/5">Fit visible shipments</button>
    </div>

    <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
      {[['Tracked', kpis.total, 'text-white'], ['At risk', kpis.atRisk, 'text-red-400'], ['Due in 14 days', kpis.dueSoon, 'text-amber-400'], ['Delivered', kpis.delivered, 'text-emerald-400']].map(([label, value, color]) => <div key={String(label)} className="glass rounded-xl p-4"><p className="text-xs text-gray-400">{label}</p><p className={`mt-1 text-2xl font-semibold ${color}`}>{value}</p></div>)}
    </div>

    <div className="glass flex flex-col gap-3 rounded-2xl p-4 lg:flex-row lg:items-center">
      <input value={query} onChange={event => setQuery(event.target.value)} placeholder="Search equipment or vendor" className="rounded-lg border border-white/10 bg-secondary/40 px-3 py-2 text-sm outline-none focus:border-primary lg:w-64" />
      <div className="flex flex-wrap gap-2">{(['all', 'at_risk', 'watch', 'on_track', 'delivered'] as StatusFilter[]).map(filter => <button key={filter} onClick={() => setStatus(filter)} className={`rounded-lg px-3 py-2 text-xs font-medium ${status === filter ? 'bg-primary text-white' : 'bg-white/5 text-gray-300 hover:bg-white/10'}`}>{filter.replace('_', ' ')}</button>)}</div>
      <div className="ml-auto flex gap-2"><button onClick={() => setAtRiskOnly(value => !value)} className={`rounded-lg px-3 py-2 text-xs ${atRiskOnly ? 'bg-red-500/20 text-red-300' : 'bg-white/5 text-gray-300'}`}>At-risk only</button><button onClick={() => setShowRoutes(value => !value)} className="rounded-lg bg-white/5 px-3 py-2 text-xs text-gray-300">{showRoutes ? 'Hide routes' : 'Show routes'}</button></div>
    </div>

    {loading ? <div className="glass rounded-2xl p-12 text-center text-gray-400">Loading project shipments…</div> : filtered.length === 0 ? <div className="glass rounded-2xl p-12 text-center text-gray-400">No shipments match these filters.</div> : <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_340px]">
      <div className="space-y-3"><SupplyChainMap shipments={filtered} selectedId={selectedId} onSelect={setSelectedId} showRoutes={showRoutes} resetToken={resetToken} /><div className="flex flex-wrap gap-4 px-1 text-xs text-gray-400"><span><i className="mr-1 inline-block h-2 w-2 rounded-full bg-red-500" />At risk</span><span><i className="mr-1 inline-block h-2 w-2 rounded-full bg-amber-500" />Watch</span><span><i className="mr-1 inline-block h-2 w-2 rounded-full bg-emerald-500" />On track</span><span>⌂ Project destination</span></div></div>
      <aside className="glass rounded-2xl p-5">{selected ? <><p className="text-xs font-medium uppercase tracking-wider text-primary">Selected shipment</p><h2 className="mt-2 text-xl font-semibold">{selected.equipment_type}</h2><p className="mt-1 text-sm text-gray-400">{selected.description || 'No description provided'}</p><div className="mt-5 space-y-4 text-sm"><div className="flex justify-between"><span className="text-gray-400">Risk</span><strong className={selected.risk_score >= 70 ? 'text-red-400' : selected.risk_score >= 40 ? 'text-amber-400' : 'text-emerald-400'}>{Math.round(selected.risk_score)}%</strong></div><div className="flex justify-between"><span className="text-gray-400">Status</span><span className={`rounded-full border px-2 py-0.5 text-xs ${statusStyle[selected.status] || statusStyle.watch}`}>{selected.status.replace('_', ' ')}</span></div><div className="flex justify-between"><span className="text-gray-400">Vendor</span><span>{selected.vendor_name || 'Not assigned'}</span></div><div className="flex justify-between"><span className="text-gray-400">Required on site</span><span>{selected.required_on_site || 'Not set'}</span></div></div><div className="mt-6 border-t border-white/10 pt-4"><p className="text-xs font-medium text-gray-400">Mitigation</p><p className="mt-2 text-sm text-gray-300">{selected.risk_score >= 70 ? 'Confirm vendor ETA, review alternate transport, and escalate delivery risk.' : 'Continue monitoring milestone updates and delivery commitments.'}</p></div></> : <p className="text-sm text-gray-400">Select a shipment on the map or list.</p>}</aside>
    </div>}

    <div className="glass overflow-hidden rounded-2xl"><div className="border-b border-white/10 p-4"><h2 className="font-semibold">Visible shipments</h2></div><div className="divide-y divide-white/5">{filtered.map(s => <button key={s.id} onClick={() => setSelectedId(s.id)} className={`flex w-full items-center gap-4 p-4 text-left transition-colors ${s.id === selectedId ? 'bg-primary/10' : 'hover:bg-white/[0.03]'}`}><span className={`h-2.5 w-2.5 rounded-full ${s.risk_score >= 70 ? 'bg-red-500' : s.risk_score >= 40 ? 'bg-amber-500' : 'bg-emerald-500'}`} /><span className="min-w-0 flex-1"><span className="block font-medium">{s.equipment_type}</span><span className="block truncate text-xs text-gray-400">{s.vendor_name || 'Vendor unassigned'} · {s.description || 'No description'}</span></span><span className="text-sm font-semibold">{Math.round(s.risk_score)}%</span><span className={`rounded-full border px-2 py-1 text-[10px] ${statusStyle[s.status] || statusStyle.watch}`}>{s.status.replace('_', ' ')}</span></button>)}</div></div>
  </div>;
}
