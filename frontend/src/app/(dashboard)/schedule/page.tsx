"use client";
import { useState, useEffect } from 'react';
import { apiFetch } from '@/lib/api-client';

interface RiskTask {
  task_id: string;
  task_name: string;
  wbs_code: string | null;
  risk_score: number;
  predicted_delay_days: number;
  contributing_factors: string[];
  status: string;
  is_critical_path: boolean;
}

export default function SchedulePage() {
  const [tasks, setTasks] = useState<RiskTask[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/api/v1/dashboard/summary')
      .then(res => res.json())
      .then(data => {
        if (data.schedule_risk) {
          setTasks(data.schedule_risk);
        }
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      completed: 'bg-emerald-500/20 text-emerald-400',
      in_progress: 'bg-blue-500/20 text-blue-400',
      not_started: 'bg-gray-500/20 text-gray-400',
      delayed: 'bg-red-500/20 text-red-400',
    };
    return styles[status] || styles['not_started'];
  };

  const getRiskColor = (score: number) => {
    if (score >= 70) return 'text-red-400';
    if (score >= 40) return 'text-amber-400';
    return 'text-emerald-400';
  };

  const getRiskBg = (score: number) => {
    if (score >= 70) return 'bg-red-500';
    if (score >= 40) return 'bg-amber-500';
    return 'bg-emerald-500';
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold">Schedule Risk Engine</h1>
          <p className="text-gray-400 mt-1 text-sm">Predictive delay-risk scoring with contributing factor analysis</p>
        </div>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="glass p-5 rounded-2xl border-t-4 border-t-red-500">
          <p className="text-xs text-gray-400 mb-2">High Risk (&gt;70%)</p>
          <h2 className="text-2xl font-bold text-red-400">{tasks.filter(t => t.risk_score >= 70).length}</h2>
        </div>
        <div className="glass p-5 rounded-2xl border-t-4 border-t-amber-500">
          <p className="text-xs text-gray-400 mb-2">Medium Risk (40-70%)</p>
          <h2 className="text-2xl font-bold text-amber-400">{tasks.filter(t => t.risk_score >= 40 && t.risk_score < 70).length}</h2>
        </div>
        <div className="glass p-5 rounded-2xl border-t-4 border-t-emerald-500">
          <p className="text-xs text-gray-400 mb-2">Low Risk (&lt;40%)</p>
          <h2 className="text-2xl font-bold text-emerald-400">{tasks.filter(t => t.risk_score < 40).length}</h2>
        </div>
        <div className="glass p-5 rounded-2xl border-t-4 border-t-violet-500">
          <p className="text-xs text-gray-400 mb-2">Critical Path Tasks</p>
          <h2 className="text-2xl font-bold text-violet-400">{tasks.filter(t => t.is_critical_path).length}</h2>
        </div>
      </div>

      {/* Task list */}
      <div className="glass rounded-2xl overflow-hidden">
        <div className="p-4 border-b border-white/5">
          <h2 className="font-semibold">All Schedule Tasks — Ranked by Risk</h2>
        </div>
        <div className="divide-y divide-white/5">
          {loading ? (
            <div className="p-8 text-center text-gray-400">Loading schedule risk data...</div>
          ) : tasks.length === 0 ? (
            <div className="p-8 text-center text-gray-400">No schedule tasks found. Import a schedule CSV to get started.</div>
          ) : (
            tasks.map((task, idx) => (
              <div key={idx} className="p-4 hover:bg-white/[0.02] transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      {task.wbs_code && (
                        <span className="text-xs font-mono text-gray-500 bg-white/5 px-2 py-0.5 rounded">{task.wbs_code}</span>
                      )}
                      <span className="font-medium text-sm">{task.task_name}</span>
                      {task.is_critical_path && (
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-violet-500/20 text-violet-400 font-semibold">CRITICAL PATH</span>
                      )}
                      <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${getStatusBadge(task.status)}`}>
                        {task.status.replace('_', ' ')}
                      </span>
                    </div>
                    {task.contributing_factors.length > 0 && (
                      <div className="flex gap-1.5 mt-2 flex-wrap">
                        {task.contributing_factors.map((f, fi) => (
                          <span key={fi} className="text-[10px] px-2 py-0.5 rounded-full bg-white/5 text-gray-400">{f}</span>
                        ))}
                      </div>
                    )}
                  </div>
                  <div className="flex items-center gap-4 ml-4">
                    {task.predicted_delay_days > 0 && (
                      <div className="text-right">
                        <p className="text-xs text-gray-500">Predicted delay</p>
                        <p className="text-sm font-semibold text-red-400">+{task.predicted_delay_days}d</p>
                      </div>
                    )}
                    <div className="text-right min-w-[80px]">
                      <div className="flex items-center gap-2 justify-end">
                        <div className="h-2 w-20 bg-gray-700 rounded-full overflow-hidden">
                          <div className={`h-full rounded-full ${getRiskBg(task.risk_score)}`}
                               style={{ width: `${task.risk_score}%` }} />
                        </div>
                        <span className={`text-sm font-bold min-w-[40px] text-right ${getRiskColor(task.risk_score)}`}>
                          {task.risk_score}%
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
