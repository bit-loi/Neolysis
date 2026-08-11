import { QuantumVariantRankRequest, QuantumVariantRankResponse } from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

async function readErrorMessage(response: Response): Promise<string> {
  let message = `Quantum variant ranking failed with status ${response.status}`;

  try {
    const payload: unknown = await response.json();
    if (isApiErrorPayload(payload)) {
      message = payload.detail.message;
    } else if (typeof payload === 'object' && payload !== null && 'detail' in payload) {
      const detail = (payload as { detail?: unknown }).detail;
      if (typeof detail === 'string') {
        message = detail;
      }
    }
  } catch {
    // Keep default message when backend returns a non-JSON error body.
  }

  return message;
}

function isApiErrorPayload(value: unknown): value is { detail: { message: string } } {
  if (typeof value !== 'object' || value === null || !('detail' in value)) {
    return false;
  }

  const detail = (value as { detail?: unknown }).detail;
  return (
    typeof detail === 'object' &&
    detail !== null &&
    'message' in detail &&
    typeof (detail as { message?: unknown }).message === 'string'
  );
}

export async function rankQuantumVariants(
  body: QuantumVariantRankRequest
): Promise<QuantumVariantRankResponse> {
  const response = await fetch(`${API_BASE}/variants/quantum-rank`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  return response.json() as Promise<QuantumVariantRankResponse>;
}
