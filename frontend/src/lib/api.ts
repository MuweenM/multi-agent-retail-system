import {
  DecisionOutput,
  LoginResponse,
  AuthUser,
  UsageResponse,
  BulkJobStatus,
  BulkResultsResponse,
} from '../types/contracts';

// Assuming Vite environment variable for API base URL
const API_BASE =
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8004/api/v1';

// ── Auth Token Management ─────────────────────────────────────────────────────
export function getToken(): string | null {
  return localStorage.getItem('access_token');
}

export function setToken(token: string): void {
  localStorage.setItem('access_token', token);
}

export function clearToken(): void {
  localStorage.removeItem('access_token');
}

export function getCurrentUser(): AuthUser | null {
  const token = getToken();
  if (!token) return null;
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return {
      sub: payload.sub,
      tenant_id: payload.tenant_id,
      role: payload.role,
    };
  } catch {
    return null;
  }
}

// ── Upgrade Notice State ──────────────────────────────────────────────────────
let upgradeNoticeCallback: ((message: string) => void) | null = null;

export function onUpgradeNotice(cb: (message: string) => void): void {
  upgradeNoticeCallback = cb;
}

// ── Core Fetch Wrapper ────────────────────────────────────────────────────────
async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (response.status === 401) {
    clearToken();
    window.location.hash = '#/login';
    throw new Error('Unauthorized. Please log in.');
  }

  if (response.status === 402) {
    const data = await response.json().catch(() => ({}));
    const message =
      data?.detail || 'Plan limit exceeded. Please upgrade your plan.';
    if (upgradeNoticeCallback) upgradeNoticeCallback(message);
    throw new Error(message);
  }

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`API error ${response.status}: ${errorText}`);
  }

  return response.json();
}

// ── Auth ──────────────────────────────────────────────────────────────────────
export const login = async (
  username: string,
  password: string
): Promise<LoginResponse> => {
  const response = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: username, password }),
  });
  if (!response.ok) {
    throw new Error('Invalid credentials');
  }
  const data: LoginResponse = await response.json();
  setToken(data.access_token);
  return data;
};

export const logout = (): void => {
  clearToken();
  window.location.hash = '#/login';
};

// ── Returns ───────────────────────────────────────────────────────────────────
export interface ProcessReturnParams {
  text: string;
  order_id?: string;
  tenant_id?: string;
}

export const processReturn = async (
  params: ProcessReturnParams
): Promise<DecisionOutput> => {
  return apiFetch<DecisionOutput>('/returns', {
    method: 'POST',
    body: JSON.stringify({
      text: params.text,
      order_id: params.order_id,
      tenant_id: params.tenant_id || 'demo',
    }),
  });
};

export const submitReview = async (
  returnId: string,
  action: 'confirm' | 'override',
  reason?: string
): Promise<void> => {
  return apiFetch<void>(`/returns/${returnId}/review`, {
    method: 'POST',
    body: JSON.stringify({ action, reason }),
  });
};

export const checkHealth = async (): Promise<{
  status: string;
  service: string;
}> => {
  return apiFetch('/health');
};

// ── Bulk ──────────────────────────────────────────────────────────────────────
export const uploadBulk = async (
  file: File
): Promise<{ status: string; job_id: string; rows: number }> => {
  const formData = new FormData();
  formData.append('file', file);
  return apiFetch('/bulk', { method: 'POST', body: formData });
};

export const getBulkStatus = async (jobId: string): Promise<BulkJobStatus> => {
  return apiFetch<BulkJobStatus>(`/bulk/${jobId}`);
};

export const getBulkResults = async (
  jobId: string,
  page = 1,
  size = 50
): Promise<BulkResultsResponse> => {
  return apiFetch<BulkResultsResponse>(
    `/bulk/${jobId}/results?page=${page}&size=${size}`
  );
};

export const exportBulkCsv = (jobId: string): void => {
  const token = getToken();
  const url = `${API_BASE}/bulk/${jobId}/export.csv`;
  const a = document.createElement('a');
  a.href = token ? `${url}?token=${token}` : url;
  a.download = `bulk_results_${jobId}.csv`;
  a.click();
};

// ── Usage ─────────────────────────────────────────────────────────────────────
export const getUsage = async (): Promise<UsageResponse> => {
  return apiFetch<UsageResponse>('/usage');
};
