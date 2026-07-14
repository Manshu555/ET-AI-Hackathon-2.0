'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { apiFetch, setAccessToken, getAccessToken } from '@/lib/api-client';
import toast from 'react-hot-toast';

const API_BASE = typeof window !== 'undefined'
  ? (process.env.NEXT_PUBLIC_AUTH_API_URL || 'http://localhost:5000/api/v1')
  : 'http://localhost:5000/api/v1';

interface User {
  id: string;
  name: string;
  email: string;
  role: string;
}

interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string, role: string) => Promise<void>;
  googleLogin: () => Promise<void>;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  login: async () => {},
  register: async () => {},
  googleLogin: async () => {},
  logout: () => {},
  isLoading: true,
});

// Load Google Identity Services script
function loadGoogleScript(): Promise<void> {
  return new Promise((resolve, reject) => {
    if (typeof window === 'undefined') return reject('No window');
    if ((window as any).google?.accounts) return resolve();
    
    const existing = document.getElementById('google-gsi-script');
    if (existing) {
      existing.addEventListener('load', () => resolve());
      return;
    }
    
    const script = document.createElement('script');
    script.id = 'google-gsi-script';
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    script.onload = () => resolve();
    script.onerror = () => reject('Failed to load Google script');
    document.head.appendChild(script);
  });
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

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

  const _saveSession = (data: { access_token: string; user: User }) => {
    setAccessToken(data.access_token);
    setUser(data.user);
    if (typeof window !== 'undefined') {
      sessionStorage.setItem('epc_user', JSON.stringify(data.user));
      sessionStorage.setItem('epc_token', data.access_token);
    }
  };

  const login = async (email: string, password: string) => {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
      credentials: 'include',
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Login failed' }));
      toast.error(err.detail || 'Login failed');
      throw new Error(err.detail || 'Login failed');
    }

    const data = await res.json();
    _saveSession(data);
  };

  const register = async (name: string, email: string, password: string, role: string) => {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, password, role }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Registration failed' }));
      toast.error(err.detail || 'Registration failed');
      throw new Error(err.detail || 'Registration failed');
    }

    // Auto-login after successful registration
    await login(email, password);
  };

  const googleLogin = async () => {
    await loadGoogleScript();

    const google = (window as any).google;
    if (!google?.accounts) throw new Error('Google Sign-In not available');

    const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || '';
    if (!clientId) throw new Error('Google Client ID not configured');

    return new Promise<void>((resolve, reject) => {
      const client = google.accounts.oauth2.initTokenClient({
        client_id: clientId,
        scope: 'email profile openid',
        callback: async (tokenResponse: any) => {
          if (tokenResponse.error) {
            return reject(new Error(tokenResponse.error_description || 'Google auth failed'));
          }

          try {
            const res = await fetch(`${API_BASE}/auth/google`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ access_token: tokenResponse.access_token }),
              credentials: 'include',
            });

            if (!res.ok) {
              const err = await res.json().catch(() => ({ detail: 'Google auth failed' }));
              toast.error(err.detail || 'Google auth failed');
              throw new Error(err.detail || 'Google auth failed');
            }

            const data = await res.json();
            _saveSession(data);
            resolve();
          } catch (err: any) {
            reject(err);
          }
        },
      });
      client.requestAccessToken();
    });
  };

  const logout = () => {
    setAccessToken(null);
    setUser(null);
    if (typeof window !== 'undefined') {
      sessionStorage.removeItem('epc_user');
      sessionStorage.removeItem('epc_token');
    }
    fetch(`${API_BASE}/auth/logout`, {
      method: 'POST',
      credentials: 'include',
    }).catch(() => {});
    router.push('/');
  };

  return (
    <AuthContext.Provider value={{ user, login, register, googleLogin, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
