export type IssNowResponse = {
  lat: number;
  lon: number;
  altitude_km: number;
  velocity_kmh: number;
  timestamp: string;
  source: string;
  stale?: boolean;
};

export type IssTrackPoint = {
  lat: number;
  lon: number;
  timestamp: string;
};

export type IssTrackResponse = {
  hours: number;
  points: IssTrackPoint[];
};

export type CrewMember = {
  name: string;
  craft: string;
};

export type CrewResponse = {
  count: number;
  members: CrewMember[];
};

const API_BASE =
  import.meta.env.VITE_API_BASE ??
  import.meta.env.VITE_API_URL?.replace(/\/iss\/now$/, '') ??
  'http://localhost:8000';
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

export async function fetchIssHistory(
  hours: number,
): Promise<IssTrackResponse> {
  const response = await fetch(`${API_BASE}/iss/history?hours=${hours}`, {
    cache: 'no-store',
  });

  if (!response.ok) {
    throw new Error(`History API error: ${response.status}`);
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
