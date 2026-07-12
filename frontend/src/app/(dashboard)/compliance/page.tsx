"use client";
import { useState, useEffect } from 'react';

export default function CompliancePage() {
  const [deviations, setDeviations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/api/v1/compliance/deviations')
      .then(res => res.json())
      .then(data => {
        setDeviations(data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to fetch deviations", err);
        setLoading(false);
      });
  }, []);

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">Compliance Review</h1>
      
      <div className="glass rounded-2xl overflow-hidden">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-white/5 border-b border-white/10">
              <th className="p-4 font-medium text-gray-300">Spec Reference</th>
              <th className="p-4 font-medium text-gray-300">Severity</th>
              <th className="p-4 font-medium text-gray-300">AI Deviation Note</th>
              <th className="p-4 font-medium text-gray-300">Action</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={4} className="p-4 text-center text-gray-400">Loading deviations...</td>
              </tr>
            ) : deviations.length === 0 ? (
              <tr>
                <td colSpan={4} className="p-4 text-center text-gray-400">No deviations found.</td>
              </tr>
            ) : (
              deviations.map(dev => (
                <tr key={dev.id} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                  <td className="p-4 font-medium">{dev.spec}</td>
                  <td className="p-4">
                    <span className={`px-2 py-1 rounded text-xs font-semibold ${dev.severity === 'Critical' ? 'bg-red-500/20 text-red-400' : 'bg-yellow-500/20 text-yellow-400'}`}>
                      {dev.severity}
                    </span>
                  </td>
                  <td className="p-4 text-sm text-gray-300">{dev.description}</td>
                  <td className="p-4">
                    <button className="text-sm bg-primary/20 text-primary px-3 py-1 rounded hover:bg-primary hover:text-white transition-colors mr-2">Override</button>
                    <button className="text-sm bg-red-500/20 text-red-400 px-3 py-1 rounded hover:bg-red-500 hover:text-white transition-colors">Reject</button>
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
