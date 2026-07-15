"use client";
import { useState, useEffect } from 'react';
import { apiFetch } from '@/lib/api-client';

interface DashboardData {
  open_deviations: number;
  critical_deviations: number;
  pending_rfis: number;
  approved_submittals: number;
  total_submittals: number;
  schedule_risk: any[];
  at_risk_shipments: number;
  total_shipments: number;
  active_commissioning: number;
}

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch<DashboardData>('/dashboard/summary')
      .then(setData)
      .catch(error => console.error('Failed to load project dashboard', error))
      .finally(() => setLoading(false));
  }, []);

  const stats = [
    { label: 'Open Deviations', value: data?.open_deviations ?? 0, color: 'from-red-500 to-rose-600', border: 'border-t-red-500', icon: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z' },
    { label: 'Pending RFIs', value: data?.pending_rfis ?? 0, color: 'from-blue-500 to-indigo-600', border: 'border-t-blue-500', icon: 'M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z' },
    { label: 'Submittals', value: `${data?.approved_submittals ?? 0}/${data?.total_submittals ?? 0}`, color: 'from-emerald-500 to-green-600', border: 'border-t-emerald-500', icon: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z', sub: 'approved' },
    { label: 'At-Risk Shipments', value: data?.at_risk_shipments ?? 0, color: 'from-amber-500 to-orange-600', border: 'border-t-amber-500', icon: 'M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7' },
    { label: 'Active Commissioning', value: data?.active_commissioning ?? 0, color: 'from-violet-500 to-purple-600', border: 'border-t-violet-500', icon: 'M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z' },
    { label: 'Critical Deviations', value: data?.critical_deviations ?? 0, color: 'from-red-600 to-red-800', border: 'border-t-red-600', icon: 'M20.618 5.984A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z' },
  ];

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold">Project Dashboard</h1>
          <p className="text-gray-400 mt-1 text-sm">Hyperscale Data Center — Phase 1</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-xs text-gray-400">Live</span>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
        {stats.map((stat, i) => (
          <div key={i} className={`glass p-5 rounded-2xl ${stat.border} border-t-4 hover:scale-[1.02] transition-transform duration-200`}>
            <div className="flex items-center gap-2 mb-3">
              <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d={stat.icon} />
              </svg>
              <p className="text-xs text-gray-400">{stat.label}</p>
            </div>
            <h2 className="text-2xl font-bold">{loading ? '...' : stat.value}</h2>
            {stat.sub && <p className="text-[10px] text-gray-500 mt-1">{stat.sub}</p>}
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Schedule Risk */}
        <div className="glass p-6 rounded-2xl">
          <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-red-400" />
            High-Risk Schedule Tasks
          </h2>
          <div className="space-y-3">
            {(data?.schedule_risk || []).map((task: any, idx: number) => (
              <div key={idx} className="p-4 bg-secondary/30 rounded-xl border border-white/5 hover:border-white/10 transition-colors">
                <div className="flex justify-between items-start">
                  <div>
                    <span className="font-medium text-sm">{task.task_name || task.task_id}</span>
                    {task.predicted_delay_days > 0 && (
                      <p className="text-xs text-red-400 mt-1">+{task.predicted_delay_days} days predicted delay</p>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="h-1.5 w-16 bg-gray-700 rounded-full overflow-hidden">
                      <div className={`h-full rounded-full ${task.risk_score >= 70 ? 'bg-red-500' : task.risk_score >= 40 ? 'bg-amber-500' : 'bg-emerald-500'}`}
                           style={{ width: `${task.risk_score}%` }} />
                    </div>
                    <span className={`text-xs font-bold ${task.risk_score >= 70 ? 'text-red-400' : task.risk_score >= 40 ? 'text-amber-400' : 'text-emerald-400'}`}>
                      {task.risk_score}%
                    </span>
                  </div>
                </div>
                {task.contributing_factors?.length > 0 && (
                  <div className="flex gap-1.5 mt-2 flex-wrap">
                    {task.contributing_factors.slice(0, 3).map((f: string, fi: number) => (
                      <span key={fi} className="text-[10px] px-2 py-0.5 rounded-full bg-white/5 text-gray-400">{f}</span>
                    ))}
                  </div>
                )}
              </div>
            ))}
            {!loading && (!data?.schedule_risk || data.schedule_risk.length === 0) && (
              <p className="text-sm text-gray-500">No high-risk tasks detected.</p>
            )}
          </div>
        </div>

        {/* Recent Activity / Notifications */}
        <div className="glass p-6 rounded-2xl">
          <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-blue-400" />
            Recent Activity
          </h2>
          <div className="space-y-3">
            <div className="p-4 bg-secondary/30 rounded-xl border border-white/5">
              <div className="flex justify-between">
                <span className="font-medium text-sm flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-red-400" />
                  Critical Deviation
                </span>
                <span className="text-[10px] text-gray-500">Today</span>
              </div>
              <p className="text-xs text-gray-300 mt-1">Chiller capacity 450kW vs required 500kW — needs PM review</p>
            </div>
            <div className="p-4 bg-secondary/30 rounded-xl border border-white/5">
              <div className="flex justify-between">
                <span className="font-medium text-sm flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                  Shipment Alert
                </span>
                <span className="text-[10px] text-gray-500">2h ago</span>
              </div>
              <p className="text-xs text-gray-300 mt-1">Switchgear shipment held at Suez Canal — 91% risk score</p>
            </div>
            <div className="p-4 bg-secondary/30 rounded-xl border border-white/5">
              <div className="flex justify-between">
                <span className="font-medium text-sm flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />
                  RFI Submitted
                </span>
                <span className="text-[10px] text-gray-500">5h ago</span>
              </div>
              <p className="text-xs text-gray-300 mt-1">Battery room ventilation question from QA engineer</p>
            </div>
            <div className="p-4 bg-secondary/30 rounded-xl border border-white/5">
              <div className="flex justify-between">
                <span className="font-medium text-sm flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-violet-400" />
                  Schedule Risk
                </span>
                <span className="text-[10px] text-gray-500">6h ago</span>
              </div>
              <p className="text-xs text-gray-300 mt-1">HVAC Chiller Installation at 78% risk — workforce at 60%</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
