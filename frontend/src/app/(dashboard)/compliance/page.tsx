"use client";
import { useState, useEffect } from 'react';
import { apiFetch } from '@/lib/api-client';

interface Deviation {
  id: string;
  spec_reference: string;
  severity: string;
  description: string;
  detected_by: string;
  status: string;
  resolution_note: string | null;
}

export default function CompliancePage() {
  const [deviations, setDeviations] = useState<Deviation[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');

  useEffect(() => {
    apiFetch<Deviation[]>('/compliance/deviations')
      .then(data => {
        setDeviations(data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to fetch deviations", err);
        setLoading(false);
      });
  }, []);

  const handleAction = async (id: string, action: string) => {
    try {
      const updated = await apiFetch<Deviation>(`/compliance/deviations/${id}`, {
        method: 'PATCH',
        body: JSON.stringify({ action, note: `${action.charAt(0).toUpperCase() + action.slice(1)} by user` }),
      });
      setDeviations(prev => prev.map(d => d.id === id ? { ...d, status: updated.status, resolution_note: updated.resolution_note } : d));
    } catch (e) {
      console.error(e);
    }
  };

  const filteredDevs = filter === 'all' ? deviations : deviations.filter(d => d.severity === filter);
  const openCount = deviations.filter(d => d.status === 'open').length;
  const criticalCount = deviations.filter(d => d.severity === 'Critical').length;

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'Critical': return 'bg-red-500/20 text-red-400 border border-red-500/30';
      case 'Major': return 'bg-amber-500/20 text-amber-400 border border-amber-500/30';
      case 'Minor': return 'bg-blue-500/20 text-blue-400 border border-blue-500/30';
      default: return 'bg-gray-500/20 text-gray-400';
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'open': return 'bg-red-500/10 text-red-400';
      case 'accepted': return 'bg-emerald-500/10 text-emerald-400';
      case 'overridden': return 'bg-amber-500/10 text-amber-400';
      case 'dismissed': return 'bg-gray-500/10 text-gray-400';
      default: return 'bg-gray-500/10 text-gray-400';
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold">Compliance Review</h1>
          <p className="text-gray-400 mt-1 text-sm">AI-detected deviations between submittals and specifications</p>
        </div>
        <div className="flex gap-3">
          <div className="glass px-4 py-2 rounded-xl text-center">
            <p className="text-2xl font-bold text-red-400">{criticalCount}</p>
            <p className="text-[10px] text-gray-500">Critical</p>
          </div>
          <div className="glass px-4 py-2 rounded-xl text-center">
            <p className="text-2xl font-bold text-amber-400">{openCount}</p>
            <p className="text-[10px] text-gray-500">Open</p>
          </div>
        </div>
      </div>

      {/* Filter tabs */}
      <div className="flex gap-2 mb-6">
        {['all', 'Critical', 'Major', 'Minor'].map(f => (
          <button key={f} onClick={() => setFilter(f)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${filter === f ? 'bg-primary text-white' : 'glass text-gray-400 hover:text-white'}`}>
            {f === 'all' ? 'All' : f} {f !== 'all' && `(${deviations.filter(d => d.severity === f).length})`}
          </button>
        ))}
      </div>

      <div className="glass rounded-2xl overflow-hidden">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-white/5 border-b border-white/10">
              <th className="p-4 font-medium text-gray-400 text-xs uppercase tracking-wider">Spec Reference</th>
              <th className="p-4 font-medium text-gray-400 text-xs uppercase tracking-wider">Severity</th>
              <th className="p-4 font-medium text-gray-400 text-xs uppercase tracking-wider">Source</th>
              <th className="p-4 font-medium text-gray-400 text-xs uppercase tracking-wider">Description</th>
              <th className="p-4 font-medium text-gray-400 text-xs uppercase tracking-wider">Status</th>
              <th className="p-4 font-medium text-gray-400 text-xs uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={6} className="p-8 text-center text-gray-400">Loading deviations...</td></tr>
            ) : filteredDevs.length === 0 ? (
              <tr><td colSpan={6} className="p-8 text-center text-gray-400">No deviations found.</td></tr>
            ) : (
              filteredDevs.map(dev => (
                <tr key={dev.id} className="border-b border-white/5 hover:bg-white/[0.02] transition-colors">
                  <td className="p-4">
                    <span className="text-sm font-mono bg-white/5 px-2 py-0.5 rounded">{dev.spec_reference || 'N/A'}</span>
                  </td>
                  <td className="p-4">
                    <span className={`px-2.5 py-1 rounded-full text-[10px] font-semibold ${getSeverityBadge(dev.severity)}`}>
                      {dev.severity}
                    </span>
                  </td>
                  <td className="p-4">
                    <span className={`text-xs ${dev.detected_by === 'ai' ? 'text-violet-400' : dev.detected_by === 'rule' ? 'text-blue-400' : 'text-gray-400'}`}>
                      {dev.detected_by === 'ai' ? '🤖 AI' : dev.detected_by === 'rule' ? '📏 Rule' : '🔧 ' + dev.detected_by}
                    </span>
                  </td>
                  <td className="p-4 text-sm text-gray-300 max-w-md">{dev.description}</td>
                  <td className="p-4">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-medium ${getStatusBadge(dev.status)}`}>
                      {dev.status}
                    </span>
                  </td>
                  <td className="p-4">
                    {dev.status === 'open' ? (
                      <div className="flex gap-1.5">
                        <button onClick={() => handleAction(dev.id, 'accept')}
                                className="text-[10px] bg-emerald-500/10 text-emerald-400 px-2.5 py-1 rounded-lg hover:bg-emerald-500 hover:text-white transition-colors font-medium">
                          Accept
                        </button>
                        <button onClick={() => handleAction(dev.id, 'override')}
                                className="text-[10px] bg-amber-500/10 text-amber-400 px-2.5 py-1 rounded-lg hover:bg-amber-500 hover:text-white transition-colors font-medium">
                          Override
                        </button>
                        <button onClick={() => handleAction(dev.id, 'dismiss')}
                                className="text-[10px] bg-gray-500/10 text-gray-400 px-2.5 py-1 rounded-lg hover:bg-gray-500 hover:text-white transition-colors font-medium">
                          Dismiss
                        </button>
                      </div>
                    ) : (
                      <span className="text-xs text-gray-500">{dev.resolution_note || '—'}</span>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
