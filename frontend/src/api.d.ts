export type IssNowResponse = {
  lat: number;
  lon: number;
  altitude_km: number;
  velocity_kmh: number;
  timestamp: string;
  source: string;
  stale?: boolean;
};
export declare function fetchIssNow(): Promise<IssNowResponse>;
