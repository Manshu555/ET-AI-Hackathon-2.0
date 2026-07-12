"use client";
import { useState, useEffect } from 'react';

export default function Dashboard() {
  const [stats, setStats] = useState({
    open_deviations: 0,
    pending_rfis: 0,
    approved_submittals: 0,
    schedule_risk: [] as any[]
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/api/v1/dashboard/stats')
      .then(res => res.json())
      .then(data => {
        setStats(data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to load dashboard stats", err);
        setLoading(false);
      });
  }, []);

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">Dashboard</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="glass p-6 rounded-2xl border-t-4 border-t-primary">
          <p className="text-sm text-gray-400">Total Open Deviations</p>
          <h2 className="text-4xl font-bold mt-2">{loading ? '...' : stats.open_deviations}</h2>
        </div>
        <div className="glass p-6 rounded-2xl border-t-4 border-t-accent">
          <p className="text-sm text-gray-400">Pending RFIs</p>
          <h2 className="text-4xl font-bold mt-2">{loading ? '...' : stats.pending_rfis}</h2>
        </div>
        <div className="glass p-6 rounded-2xl border-t-4 border-t-green-500">
          <p className="text-sm text-gray-400">Approved Submittals</p>
          <h2 className="text-4xl font-bold mt-2">{loading ? '...' : stats.approved_submittals}</h2>
        </div>
        <div className="glass p-6 rounded-2xl border-t-4 border-t-red-500">
          <p className="text-sm text-gray-400">Avg Schedule Risk</p>
          <h2 className="text-4xl font-bold mt-2">
            {loading ? '...' : stats.schedule_risk.length > 0 
                ? `${Math.round(stats.schedule_risk.reduce((a, b) => a + b.risk_score, 0) / stats.schedule_risk.length)}%` 
                : 'N/A'}
          </h2>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="glass p-6 rounded-2xl">
          <h2 className="text-xl font-bold mb-4">Recent Activity</h2>
          <div className="space-y-4">
            <div className="p-4 bg-secondary/30 rounded-lg border border-white/5">
              <div className="flex justify-between">
                <span className="font-medium">Submittal SUB-009</span>
                <span className="text-xs text-gray-400">2 hours ago</span>
              </div>
              <p className="text-sm text-red-400 mt-1">AI flagged a Major deviation on section 4.2.1.</p>
            </div>
            <div className="p-4 bg-secondary/30 rounded-lg border border-white/5">
              <div className="flex justify-between">
                <span className="font-medium">RFI R-041</span>
                <span className="text-xs text-gray-400">5 hours ago</span>
              </div>
              <p className="text-sm text-blue-400 mt-1">New question asked by Vendor A regarding cooling specs.</p>
            </div>
          </div>
        </div>
        
        <div className="glass p-6 rounded-2xl">
          <h2 className="text-xl font-bold mb-4">High-Risk Schedule Tasks</h2>
          <div className="space-y-4">
            {stats.schedule_risk.map((task, idx) => (
              <div key={idx} className="p-4 bg-secondary/30 rounded-lg border border-white/5">
                <div className="flex justify-between">
                  <span className="font-medium text-red-400">{task.task_id}</span>
                  <span className="text-xs text-red-400 font-bold">{task.risk_score}% Risk</span>
                </div>
                <p className="text-sm text-gray-300 mt-1">Factors: {task.top_factors.join(", ")}</p>
              </div>
            ))}
            {!loading && stats.schedule_risk.length === 0 && (
                <p className="text-sm text-gray-400">No high-risk tasks detected.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
