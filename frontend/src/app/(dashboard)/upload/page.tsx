"use client";
import { useState } from 'react';

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);

  const [uploading, setUploading] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleUpload = (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;
    
    setUploading(true);
    // Simulate upload and processing time for the demo
    setTimeout(() => {
      setUploading(false);
      setSuccess(true);
      setTimeout(() => {
        setSuccess(false);
        setFile(null);
      }, 3000);
    }, 2000);
  };

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Document Ingestion</h1>
      
      <div className="glass p-8 rounded-2xl">
        <form onSubmit={handleUpload} className="space-y-6">
          <div>
            <label className="block text-sm font-medium mb-2">Document Type</label>
            <select className="w-full bg-secondary border border-white/10 rounded-lg p-3 outline-none focus:border-primary">
              <option value="specification">Specification</option>
              <option value="submittal">Vendor Submittal</option>
            </select>
          </div>
          
          <div className="border-2 border-dashed border-white/20 rounded-xl p-10 text-center hover:border-primary transition-colors cursor-pointer relative">
            <input 
              type="file" 
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
            />
            {file ? (
              <p className="text-primary font-medium">{file.name}</p>
            ) : (
              <div>
                <svg className="w-10 h-10 mx-auto mb-2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path></svg>
                <p className="text-sm text-gray-400">Click or drag PDF here to upload</p>
              </div>
            )}
          </div>
          
          <button type="submit" disabled={uploading || success || !file} className="w-full bg-primary hover:bg-primary-hover disabled:bg-gray-600 py-3 rounded-lg font-medium transition-colors">
            {uploading ? "Uploading and Ingesting..." : success ? "Successfully Processed!" : "Upload & Process"}
          </button>
        </form>
      </div>
    </div>
  );
}
