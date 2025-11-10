export type IssNowResponse = {
  lat: number;
  lon: number;
  altitude_km: number;
  velocity_kmh: number;
  timestamp: string;
  source: string;
  stale?: boolean;
};

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/iss/now';

export async function fetchIssNow(): Promise<IssNowResponse> {
  const response = await fetch(API_URL, {
    cache: 'no-store',
  });

  if (!response.ok) {
    throw new Error(`Upstream error: ${response.status}`);
  }

  return response.json();
}
