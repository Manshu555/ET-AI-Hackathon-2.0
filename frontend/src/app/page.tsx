"use client";
import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const router = useRouter();

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    if (email) {
      router.push('/dashboard');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden">
      {/* Background aesthetic */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-primary/20 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-accent/20 rounded-full blur-[120px] pointer-events-none" />
      
      <div className="glass p-10 rounded-2xl w-full max-w-md relative z-10">
        <h1 className="text-3xl font-bold mb-2 text-center text-transparent bg-clip-text bg-gradient-to-r from-primary to-accent">
          EPC-Intel
        </h1>
        <p className="text-sm text-gray-400 text-center mb-8">AI Intelligence Platform for Data Centre Delivery</p>
        
        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-sm text-gray-300 mb-1">Email</label>
            <input 
              type="email" 
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="admin@epc-intel.com" 
              className="w-full bg-secondary/50 border border-white/10 rounded-lg px-4 py-2 focus:outline-none focus:border-primary transition-colors" 
              required
            />
          </div>
          <div>
            <label className="block text-sm text-gray-300 mb-1">Password</label>
            <input 
              type="password" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••" 
              className="w-full bg-secondary/50 border border-white/10 rounded-lg px-4 py-2 focus:outline-none focus:border-primary transition-colors" 
              required
            />
          </div>
          
          <button type="submit" className="block w-full text-center bg-primary hover:bg-primary-hover text-white font-medium py-2 rounded-lg transition-colors mt-6">
            Sign In
          </button>
        </form>
      </div>
    </div>
  );
}
