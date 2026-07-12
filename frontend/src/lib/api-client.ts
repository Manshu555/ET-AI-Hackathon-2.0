const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

let accessToken: string | null = null;

export function setAccessToken(token: string | null) {
  accessToken = token;
}

export function getAccessToken(): string | null {
  return accessToken;
}

export async function apiFetch<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const token = getAccessToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(opts.headers as Record<string, string> || {}),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...opts,
    headers,
    credentials: 'include', // for refresh token cookie
  });

  // Auto-refresh on 401
  if (res.status === 401 && token) {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      headers['Authorization'] = `Bearer ${getAccessToken()}`;
      const retry = await fetch(`${API_BASE}${path}`, { ...opts, headers, credentials: 'include' });
      if (!retry.ok) throw await retry.json().catch(() => ({ error: { message: 'Request failed' } }));
      return retry.json();
    }
  }

  if (!res.ok) {
    const error = await res.json().catch(() => ({ error: { message: `HTTP ${res.status}` } }));
    throw error;
  }

  return res.json();
}

export async function refreshAccessToken(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/auth/refresh`, {
      method: 'POST',
      credentials: 'include',
    });
    if (res.ok) {
      const data = await res.json();
      setAccessToken(data.access_token);
      return true;
    }
  } catch { }
  // Refresh failed — clear state
  setAccessToken(null);
  return false;
}

// Convenience for file uploads (no Content-Type — browser sets multipart boundary)
export async function apiUpload<T>(path: string, formData: FormData): Promise<T> {
  const token = getAccessToken();
  const headers: Record<string, string> = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    body: formData,
    headers,
    credentials: 'include',
  });

  if (!res.ok) throw await res.json().catch(() => ({ error: { message: `HTTP ${res.status}` } }));
  return res.json();
}
