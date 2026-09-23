import { DecisionOutput } from '../types/contracts';

// Assuming Vite environment variable for API base URL
const API_BASE =
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8004/api/v1';

export interface ProcessReturnParams {
  text: string;
  order_id?: string;
  tenant_id?: string;
}

export const processReturn = async (
  params: ProcessReturnParams
): Promise<DecisionOutput> => {
  const response = await fetch(`${API_BASE}/returns`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      text: params.text,
      order_id: params.order_id,
      tenant_id: params.tenant_id || 'demo',
    }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`API error: ${response.status} - ${errorText}`);
  }

  return response.json();
};

export const checkHealth = async (): Promise<{
  status: string;
  service: string;
}> => {
  const response = await fetch(`${API_BASE}/health`);
  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }
  return response.json();
};
