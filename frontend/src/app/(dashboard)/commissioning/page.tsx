"use client";
import { useState, useEffect } from 'react';

interface Template {
  id: string;
  name: string;
  standard: string;
  system_type: string;
}

interface Step {
  id: string;
  step_number: number;
  description: string;
  expected_min: number | null;
  expected_max: number | null;
  expected_unit: string | null;
  actual_value: number | null;
  status: string;
}

interface RunDetail {
  id: string;
  template_name: string;
  standard: string;
  status: string;
  steps: Step[];
  pass_count: number;
  fail_count: number;
  pending_count: number;
}

export default function CommissioningPage() {
  const [templates, setTemplates] = useState<Template[]>([
    { id: 't1', name: 'TIA-942 Power Distribution Test', standard: 'TIA-942', system_type: 'power' },
    { id: 't2', name: 'BICSI Cooling System Commissioning', standard: 'BICSI', system_type: 'cooling' },
    { id: 't3', name: 'Uptime Tier III IT Infrastructure Test', standard: 'Uptime', system_type: 'IT' },
  ]);
  const [activeRun, setActiveRun] = useState<RunDetail | null>(null);
  const [mode, setMode] = useState<'templates' | 'checklist'>('templates');

  const startRun = (template: Template) => {
    // Demo: create a run with steps from template
    const demoSteps: Step[] = template.system_type === 'power' ? [
      { id: 's1', step_number: 1, description: 'Verify UPS input voltage (V)', expected_min: 380, expected_max: 420, expected_unit: 'V', actual_value: null, status: 'pending' },
      { id: 's2', step_number: 2, description: 'Verify UPS output voltage (V)', expected_min: 395, expected_max: 405, expected_unit: 'V', actual_value: null, status: 'pending' },
      { id: 's3', step_number: 3, description: 'Verify UPS output frequency (Hz)', expected_min: 49.5, expected_max: 50.5, expected_unit: 'Hz', actual_value: null, status: 'pending' },
      { id: 's4', step_number: 4, description: 'Verify transfer switch operation time (ms)', expected_min: 0, expected_max: 10, expected_unit: 'ms', actual_value: null, status: 'pending' },
      { id: 's5', step_number: 5, description: 'Verify generator start time (s)', expected_min: 0, expected_max: 15, expected_unit: 's', actual_value: null, status: 'pending' },
      { id: 's6', step_number: 6, description: 'Verify PDU output voltage per phase (V)', expected_min: 220, expected_max: 240, expected_unit: 'V', actual_value: null, status: 'pending' },
      { id: 's7', step_number: 7, description: 'Battery autonomy test duration (min)', expected_min: 10, expected_max: 999, expected_unit: 'min', actual_value: null, status: 'pending' },
      { id: 's8', step_number: 8, description: 'Verify earth fault loop impedance (Ω)', expected_min: 0, expected_max: 0.8, expected_unit: 'Ω', actual_value: null, status: 'pending' },
    ] : template.system_type === 'cooling' ? [
      { id: 's1', step_number: 1, description: 'Chilled water supply temperature (°C)', expected_min: 6, expected_max: 12, expected_unit: '°C', actual_value: null, status: 'pending' },
      { id: 's2', step_number: 2, description: 'Chilled water return temperature (°C)', expected_min: 12, expected_max: 18, expected_unit: '°C', actual_value: null, status: 'pending' },
      { id: 's3', step_number: 3, description: 'CRAC unit airflow rate (CFM)', expected_min: 3000, expected_max: 6000, expected_unit: 'CFM', actual_value: null, status: 'pending' },
      { id: 's4', step_number: 4, description: 'Cold aisle temperature at rack inlet (°C)', expected_min: 18, expected_max: 27, expected_unit: '°C', actual_value: null, status: 'pending' },
      { id: 's5', step_number: 5, description: 'Hot aisle temperature at rack exhaust (°C)', expected_min: 27, expected_max: 45, expected_unit: '°C', actual_value: null, status: 'pending' },
      { id: 's6', step_number: 6, description: 'Relative humidity in whitespace (%)', expected_min: 20, expected_max: 80, expected_unit: '%', actual_value: null, status: 'pending' },
      { id: 's7', step_number: 7, description: 'Differential pressure across raised floor (Pa)', expected_min: 10, expected_max: 30, expected_unit: 'Pa', actual_value: null, status: 'pending' },
    ] : [
      { id: 's1', step_number: 1, description: 'Network switch port link speed (Gbps)', expected_min: 10, expected_max: 100, expected_unit: 'Gbps', actual_value: null, status: 'pending' },
      { id: 's2', step_number: 2, description: 'UPS N+1 redundancy — modules online', expected_min: 2, expected_max: 10, expected_unit: 'count', actual_value: null, status: 'pending' },
      { id: 's3', step_number: 3, description: 'Cross-connect fiber attenuation (dB)', expected_min: 0, expected_max: 3, expected_unit: 'dB', actual_value: null, status: 'pending' },
      { id: 's4', step_number: 4, description: 'PDU load balancing deviation per phase (%)', expected_min: 0, expected_max: 10, expected_unit: '%', actual_value: null, status: 'pending' },
      { id: 's5', step_number: 5, description: 'Fire suppression system activation time (s)', expected_min: 0, expected_max: 60, expected_unit: 's', actual_value: null, status: 'pending' },
      { id: 's6', step_number: 6, description: 'Environmental monitoring sensor accuracy (±°C)', expected_min: 0, expected_max: 1, expected_unit: '°C', actual_value: null, status: 'pending' },
    ];

    setActiveRun({
      id: 'run-demo',
      template_name: template.name,
      standard: template.standard,
      status: 'in_progress',
      steps: demoSteps,
      pass_count: 0,
      fail_count: 0,
      pending_count: demoSteps.length,
    });
    setMode('checklist');
  };

  const submitValue = (stepId: string, value: string) => {
    if (!activeRun) return;
    const numValue = parseFloat(value);
    if (isNaN(numValue)) return;

    setActiveRun(prev => {
      if (!prev) return prev;
      const newSteps = prev.steps.map(s => {
        if (s.id !== stepId) return s;
        const inRange = (s.expected_min === null || numValue >= s.expected_min) &&
                        (s.expected_max === null || numValue <= s.expected_max);
        return { ...s, actual_value: numValue, status: inRange ? 'pass' : 'fail' };
      });
      return {
        ...prev,
        steps: newSteps,
        pass_count: newSteps.filter(s => s.status === 'pass').length,
        fail_count: newSteps.filter(s => s.status === 'fail').length,
        pending_count: newSteps.filter(s => s.status === 'pending').length,
        status: newSteps.every(s => s.status !== 'pending') ? (newSteps.some(s => s.status === 'fail') ? 'failed' : 'completed') : 'in_progress',
      };
    });
  };

  const getSystemIcon = (type: string) => {
    switch (type) {
      case 'power': return '⚡';
      case 'cooling': return '❄️';
      case 'IT': return '🖥️';
      default: return '📋';
    }
  };

  const downloadPDF = async () => {
    if (!activeRun) return;
    try {
      const jsPDFModule = await import('jspdf');
      const autoTableModule = await import('jspdf-autotable');
      const jsPDF = jsPDFModule.default;
      const autoTable = autoTableModule.default;
      const doc = new jsPDF();
      
      doc.setFontSize(20);
      doc.text("Commissioning Test Report", 14, 22);
      
      doc.setFontSize(12);
      doc.text(`Template: ${activeRun.template_name}`, 14, 32);
      doc.text(`Standard: ${activeRun.standard}`, 14, 40);
      doc.text(`Status: ${activeRun.status.toUpperCase()}`, 14, 48);
      
      doc.text(`Passed: ${activeRun.pass_count} | Failed: ${activeRun.fail_count} | Pending: ${activeRun.pending_count}`, 14, 58);
      
      const tableColumn = ["Step", "Description", "Expected", "Actual", "Result"];
      const tableRows = activeRun.steps.map(step => [
        step.step_number.toString(),
        step.description,
        `${step.expected_min !== null ? step.expected_min : '*'} - ${step.expected_max !== null ? step.expected_max : '*'} ${step.expected_unit || ''}`,
        step.actual_value !== null ? `${step.actual_value} ${step.expected_unit || ''}` : 'N/A',
        step.status.toUpperCase()
      ]);
      
      autoTable(doc, {
        head: [tableColumn],
        body: tableRows,
        startY: 65,
      });
      
      doc.save(`commissioning_report_${activeRun.id}.pdf`);
    } catch (error) {
      console.error("Failed to generate PDF", error);
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold">Commissioning Copilot</h1>
          <p className="text-gray-400 mt-1 text-sm">Standards-based test sequences with real-time validation</p>
        </div>
        {mode === 'checklist' && (
          <button onClick={() => { setMode('templates'); setActiveRun(null); }}
                  className="px-4 py-2 text-sm glass rounded-lg hover:bg-white/10 transition-colors">
            ← Back to Templates
          </button>
        )}
      </div>

      {mode === 'templates' ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {templates.map(t => (
            <div key={t.id} className="glass p-6 rounded-2xl hover:border-white/20 transition-all group cursor-pointer" onClick={() => startRun(t)}>
              <div className="text-4xl mb-4">{getSystemIcon(t.system_type)}</div>
              <h3 className="font-semibold text-lg mb-1">{t.name}</h3>
              <div className="flex gap-2 mb-4">
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-400">{t.standard}</span>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-violet-500/20 text-violet-400">{t.system_type}</span>
              </div>
              <button className="w-full py-2.5 rounded-lg bg-primary/10 text-primary text-sm font-medium hover:bg-primary hover:text-white transition-all group-hover:bg-primary group-hover:text-white">
                Start Test Run →
              </button>
            </div>
          ))}
        </div>
      ) : activeRun && (
        <div>
          {/* Progress bar */}
          <div className="glass p-4 rounded-2xl mb-6">
            <div className="flex items-center justify-between mb-2">
              <div>
                <h2 className="font-semibold">{activeRun.template_name}</h2>
                <p className="text-xs text-gray-400">{activeRun.standard} Standard</p>
              </div>
              <div className="flex gap-4 text-sm">
                <span className="text-emerald-400">✓ {activeRun.pass_count}</span>
                <span className="text-red-400">✗ {activeRun.fail_count}</span>
                <span className="text-gray-400">○ {activeRun.pending_count}</span>
              </div>
            </div>
            <div className="h-2 bg-gray-700 rounded-full overflow-hidden flex">
              <div className="bg-emerald-500 transition-all duration-500" style={{ width: `${(activeRun.pass_count / activeRun.steps.length) * 100}%` }} />
              <div className="bg-red-500 transition-all duration-500" style={{ width: `${(activeRun.fail_count / activeRun.steps.length) * 100}%` }} />
            </div>
          </div>

          {/* Checklist */}
          <div className="space-y-3">
            {activeRun.steps.map(step => (
              <div key={step.id} className={`glass p-5 rounded-2xl transition-all ${step.status === 'pass' ? 'border-emerald-500/30' : step.status === 'fail' ? 'border-red-500/30' : ''}`}>
                <div className="flex items-center justify-between gap-4">
                  <div className="flex items-center gap-3 flex-1">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0 ${
                      step.status === 'pass' ? 'bg-emerald-500/20 text-emerald-400' :
                      step.status === 'fail' ? 'bg-red-500/20 text-red-400' :
                      'bg-white/5 text-gray-400'
                    }`}>
                      {step.status === 'pass' ? '✓' : step.status === 'fail' ? '✗' : step.step_number}
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-medium">{step.description}</p>
                      <p className="text-xs text-gray-500 mt-0.5">
                        Expected: {step.expected_min} – {step.expected_max} {step.expected_unit}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {step.status === 'pending' ? (
                      <form onSubmit={(e) => {
                        e.preventDefault();
                        const input = (e.target as HTMLFormElement).querySelector('input');
                        if (input) submitValue(step.id, input.value);
                      }} className="flex gap-2">
                        <input
                          type="number"
                          step="any"
                          placeholder={`${step.expected_unit || 'value'}`}
                          className="w-24 bg-secondary/50 border border-white/10 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:border-primary text-center"
                        />
                        <button type="submit" className="px-3 py-1.5 bg-primary/20 text-primary rounded-lg text-sm hover:bg-primary hover:text-white transition-colors">
                          Submit
                        </button>
                      </form>
                    ) : (
                      <div className="text-right">
                        <p className={`text-sm font-semibold ${step.status === 'pass' ? 'text-emerald-400' : 'text-red-400'}`}>
                          {step.actual_value} {step.expected_unit}
                        </p>
                        <p className={`text-[10px] ${step.status === 'pass' ? 'text-emerald-500' : 'text-red-500'}`}>
                          {step.status === 'pass' ? 'WITHIN RANGE' : 'OUT OF TOLERANCE'}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
                {step.status === 'fail' && (
                  <div className="mt-3 p-2 bg-red-500/10 rounded-lg border border-red-500/20">
                    <p className="text-xs text-red-400">⚠️ Non-conformance detected — deviation record auto-created for tracking</p>
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Completion */}
          {activeRun.status !== 'in_progress' && (
            <div className={`glass p-6 rounded-2xl mt-6 text-center ${activeRun.status === 'completed' ? 'border-emerald-500/30' : 'border-red-500/30'}`}>
              <div className="text-4xl mb-3">{activeRun.status === 'completed' ? '🎉' : '⚠️'}</div>
              <h3 className="text-xl font-bold mb-1">
                {activeRun.status === 'completed' ? 'All Tests Passed!' : 'Tests Complete — Failures Detected'}
              </h3>
              <p className="text-sm text-gray-400 mb-4">
                {activeRun.pass_count} passed, {activeRun.fail_count} failed out of {activeRun.steps.length} steps
              </p>
              <button onClick={downloadPDF} className="px-6 py-2.5 bg-primary text-white rounded-lg text-sm font-medium hover:bg-primary-hover transition-colors">
                Download Report (PDF)
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
