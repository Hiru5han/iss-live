export type IssNowResponse = {
  lat: number;
  lon: number;
  altitude_km: number;
  velocity_kmh: number;
  timestamp: string;
  source: string;
  stale?: boolean;
};

export type CrewMember = {
  name: string;
  craft: string;
};

export type CrewResponse = {
  count: number;
  members: CrewMember[];
};

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000';
const API_URL = import.meta.env.VITE_API_URL ?? `${API_BASE}/iss/now`;
const CREW_URL = `${API_BASE}/iss/crew`;

export async function fetchIssNow(): Promise<IssNowResponse> {
  const response = await fetch(API_URL, {
    cache: 'no-store',
  });

  if (!response.ok) {
    throw new Error(`Upstream error: ${response.status}`);
  }

  return response.json();
}

export async function fetchCrew(): Promise<CrewResponse> {
  const response = await fetch(CREW_URL, {
    cache: 'no-store',
  });

  if (!response.ok) {
    throw new Error(`Crew API error: ${response.status}`);
  }

  return response.json();
}
