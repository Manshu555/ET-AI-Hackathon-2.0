'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { apiFetch, setAccessToken, getAccessToken } from '@/lib/api-client';

interface User {
  id: string;
  name: string;
  email: string;
  role: string;
}

interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  login: async () => {},
  logout: () => {},
  isLoading: true,
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Try to restore session on mount
  useEffect(() => {
    const stored = typeof window !== 'undefined' ? sessionStorage.getItem('epc_user') : null;
    const storedToken = typeof window !== 'undefined' ? sessionStorage.getItem('epc_token') : null;
    if (stored && storedToken) {
      setUser(JSON.parse(stored));
      setAccessToken(storedToken);
    }
    setIsLoading(false);
  }, []);

  const login = async (email: string, password: string) => {
    const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
      credentials: 'include',
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Login failed' }));
      throw new Error(err.detail || 'Login failed');
    }

    const data = await res.json();
    setAccessToken(data.access_token);
    setUser(data.user);
    if (typeof window !== 'undefined') {
      sessionStorage.setItem('epc_user', JSON.stringify(data.user));
      sessionStorage.setItem('epc_token', data.access_token);
    }
  };

  const logout = () => {
    setAccessToken(null);
    setUser(null);
    if (typeof window !== 'undefined') {
      sessionStorage.removeItem('epc_user');
      sessionStorage.removeItem('epc_token');
    }
    fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}/auth/logout`, {
      method: 'POST',
      credentials: 'include',
    }).catch(() => {});
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
