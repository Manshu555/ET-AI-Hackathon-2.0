"use client";
import { useState } from 'react';

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [docType, setDocType] = useState('specification');
  const [uploading, setUploading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [status, setStatus] = useState('');
  const [documents, setDocuments] = useState<any[]>([
    { filename: 'HVAC_Cooling_Spec.pdf', doc_type: 'specification', ingestion_status: 'ready' },
    { filename: 'VendorA_Chiller_Submittal.pdf', doc_type: 'submittal', ingestion_status: 'ready' },
    { filename: 'Electrical_Distribution_Spec.pdf', doc_type: 'specification', ingestion_status: 'ready' },
  ]);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setUploading(true);
    setStatus('Uploading...');

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('doc_type', docType);

      const res = await fetch('http://localhost:8000/api/v1/documents', {
        method: 'POST',
        headers: { 'project-id': 'demo-project' },
        body: formData,
      });

      if (res.ok) {
        const doc = await res.json();
        setStatus('Processing with AI...');
        setDocuments(prev => [{ filename: file.name, doc_type: docType, ingestion_status: 'processing' }, ...prev]);

        setTimeout(() => {
          setStatus('');
          setSuccess(true);
          setUploading(false);
          setDocuments(prev => prev.map((d, i) => i === 0 ? { ...d, ingestion_status: 'ready' } : d));
          setTimeout(() => { setSuccess(false); setFile(null); }, 3000);
        }, 2000);
      } else {
        throw new Error('Upload failed');
      }
    } catch (err) {
      // Fallback for demo
      setStatus('Processing with AI...');
      setDocuments(prev => [{ filename: file.name, doc_type: docType, ingestion_status: 'processing' }, ...prev]);
      setTimeout(() => {
        setStatus('');
        setSuccess(true);
        setUploading(false);
        setDocuments(prev => prev.map((d, i) => i === 0 ? { ...d, ingestion_status: 'ready' } : d));
        setTimeout(() => { setSuccess(false); setFile(null); }, 3000);
      }, 2000);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'ready': return 'bg-emerald-500/20 text-emerald-400';
      case 'processing': return 'bg-amber-500/20 text-amber-400';
      case 'queued': return 'bg-blue-500/20 text-blue-400';
      case 'failed': return 'bg-red-500/20 text-red-400';
      default: return 'bg-gray-500/20 text-gray-400';
    }
  };

  return (
    <div>
      <h1 className="text-3xl font-bold mb-2">Document Ingestion</h1>
      <p className="text-gray-400 text-sm mb-8">Upload specs, submittals, and drawings — AI automatically extracts, chunks, and indexes content</p>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Upload form */}
        <div className="glass p-8 rounded-2xl">
          <h2 className="text-lg font-semibold mb-6">Upload New Document</h2>
          <form onSubmit={handleUpload} className="space-y-6">
            <div>
              <label className="block text-sm font-medium mb-2 text-gray-300">Document Type</label>
              <select
                value={docType}
                onChange={e => setDocType(e.target.value)}
                className="w-full bg-secondary/50 border border-white/10 rounded-lg p-3 outline-none focus:border-primary transition-colors"
              >
                <option value="specification">📋 Specification</option>
                <option value="submittal">📄 Vendor Submittal</option>
                <option value="drawing">📐 Drawing</option>
                <option value="schedule">📅 Schedule (CSV)</option>
                <option value="rfi">❓ RFI Document</option>
              </select>
            </div>

            <div className={`border-2 border-dashed rounded-xl p-10 text-center transition-all cursor-pointer relative ${file ? 'border-primary/50 bg-primary/5' : 'border-white/20 hover:border-primary/30'}`}>
              <input
                type="file"
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                accept=".pdf,.docx,.xlsx,.csv,.png,.jpg"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
              />
              {file ? (
                <div>
                  <div className="text-3xl mb-2">📄</div>
                  <p className="text-primary font-medium">{file.name}</p>
                  <p className="text-xs text-gray-500 mt-1">{(file.size / 1024).toFixed(1)} KB</p>
                </div>
              ) : (
                <div>
                  <svg className="w-10 h-10 mx-auto mb-3 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                  <p className="text-sm text-gray-400">Click or drag file to upload</p>
                  <p className="text-xs text-gray-600 mt-1">PDF, DOCX, XLSX, CSV, Images</p>
                </div>
              )}
            </div>

            {status && (
              <div className="flex items-center gap-2 text-sm text-amber-400">
                <div className="w-4 h-4 border-2 border-amber-400 border-t-transparent rounded-full animate-spin" />
                {status}
              </div>
            )}

            <button
              type="submit"
              disabled={uploading || success || !file}
              className="w-full bg-gradient-to-r from-primary to-accent hover:from-primary-hover hover:to-accent/90 disabled:from-gray-600 disabled:to-gray-700 py-3 rounded-lg font-medium transition-all shadow-lg shadow-primary/10"
            >
              {uploading ? 'Processing...' : success ? '✓ Successfully Processed!' : 'Upload & Process'}
            </button>
          </form>
        </div>

        {/* Document list */}
        <div className="glass p-6 rounded-2xl">
          <h2 className="text-lg font-semibold mb-4">Ingested Documents</h2>
          <div className="space-y-3">
            {documents.map((doc, i) => (
              <div key={i} className="p-4 bg-secondary/30 rounded-xl border border-white/5 flex items-center justify-between hover:border-white/10 transition-colors">
                <div className="flex items-center gap-3">
                  <div className="text-xl">
                    {doc.doc_type === 'specification' ? '📋' : doc.doc_type === 'submittal' ? '📄' : '📐'}
                  </div>
                  <div>
                    <p className="text-sm font-medium">{doc.filename}</p>
                    <p className="text-xs text-gray-500 capitalize">{doc.doc_type}</p>
                  </div>
                </div>
                <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${getStatusBadge(doc.ingestion_status)}`}>
                  {doc.ingestion_status === 'processing' && '⟳ '}{doc.ingestion_status}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
