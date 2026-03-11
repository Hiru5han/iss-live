import { useState } from 'react';

import { IssNowResponse } from '../api';

interface HudProps {
  data: IssNowResponse | null;
}

const formatNumber = (value?: number, fraction = 2) =>
  typeof value === 'number' ? value.toFixed(fraction) : '—';

const formatTime = (timestamp?: string) => {
  if (!timestamp) {
    return '—';
  }

  try {
    const formatter = new Intl.DateTimeFormat('en-GB', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
      timeZone: 'UTC',
    });
    return `${formatter.format(new Date(timestamp))} UTC`;
  } catch (error) {
    return timestamp;
  }
};

const Hud = ({ data }: HudProps) => {
  const [coordsOpen, setCoordsOpen] = useState(false);

  return (
    <div className="hud-container">
      <p className="hud-title">ISS TELEMETRY</p>

      {/* Desktop: lat/lon as normal rows */}
      <div className="coords-desktop">
        <div className="metric-row">
          <span>Latitude</span>
          <span>{formatNumber(data?.lat)}°</span>
        </div>
        <div className="metric-row">
          <span>Longitude</span>
          <span>{formatNumber(data?.lon)}°</span>
        </div>
      </div>

      {/* Mobile: collapsed behind an info button */}
      <div className="coords-mobile">
        <button
          className="coords-info-btn"
          aria-label="Show coordinates"
          aria-expanded={coordsOpen}
          onClick={() => setCoordsOpen((v) => !v)}
        >
          <span className="coords-info-icon">ℹ</span>
          <span className="coords-info-label">Coordinates</span>
          <span className="coords-info-summary">
            {formatNumber(data?.lat)}°, {formatNumber(data?.lon)}°
          </span>
        </button>

        {coordsOpen && (
          <div className="coords-bubble" role="tooltip">
            <div className="metric-row">
              <span>Latitude</span>
              <span>{formatNumber(data?.lat)}°</span>
            </div>
            <div className="metric-row">
              <span>Longitude</span>
              <span>{formatNumber(data?.lon)}°</span>
            </div>
          </div>
        )}
      </div>

      <div className="metric-row">
        <span>Altitude</span>
        <span>{formatNumber(data?.altitude_km, 1)} km</span>
      </div>
      <div className="metric-row">
        <span>Velocity</span>
        <span>{formatNumber(data?.velocity_kmh, 0)} km/h</span>
      </div>
      <div className="metric-row">
        <span>Source</span>
        <span>{data?.source ?? '—'}</span>
      </div>
      <div className="timestamp">Last update: {formatTime(data?.timestamp)}</div>
      <div className="pills">
        <span className="pill pill-live">{data ? 'LIVE' : 'ACQ'}</span>
        {data?.stale && <span className="pill pill-stale">STALE</span>}
      </div>
    </div>
  );
};

export default Hud;
