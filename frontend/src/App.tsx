import { useEffect, useMemo, useState } from 'react';
import GlobeView, { GlobePoint } from './components/GlobeView';
import CrewPanel from './components/CrewPanel';
import Hud from './components/Hud';
import { fetchIssNow, fetchCrew, IssNowResponse, CrewResponse } from './api';

const POLL_INTERVAL_MS = 5000;
const CREW_POLL_INTERVAL_MS = 300_000; // 5 minutes
const MAX_TRACK_POINTS = 180; // ~15 minutes of history at 5s cadence

function App() {
  const [telemetry, setTelemetry] = useState<IssNowResponse | null>(null);
  const [crew, setCrew] = useState<CrewResponse | null>(null);
  const [track, setTrack] = useState<GlobePoint[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    const load = async () => {
      try {
        const next = await fetchIssNow();
        if (!mounted) {
          return;
        }

        setTelemetry(next);
        setTrack((prev) => {
          const updated = [...prev, { lat: next.lat, lon: next.lon }];
          return updated.slice(-MAX_TRACK_POINTS);
        });
        setError(null);
      } catch (err) {
        if (!mounted) {
          return;
        }
        setError('Unable to reach local ISS API. Showing last known state.');
      }
    };

    load();
    const intervalId = window.setInterval(load, POLL_INTERVAL_MS);

    return () => {
      mounted = false;
      window.clearInterval(intervalId);
    };
  }, []);

  useEffect(() => {
    let mounted = true;
    const loadCrew = async () => {
      try {
        const data = await fetchCrew();
        if (mounted) {
          setCrew(data);
        }
      } catch {
        // silently keep last known crew data
      }
    };

    loadCrew();
    const intervalId = window.setInterval(loadCrew, CREW_POLL_INTERVAL_MS);

    return () => {
      mounted = false;
      window.clearInterval(intervalId);
    };
  }, []);

  const currentPosition = useMemo(() => {
    if (!telemetry) {
      return undefined;
    }
    return { lat: telemetry.lat, lon: telemetry.lon };
  }, [telemetry]);

  return (
    <div className="app-shell">
      <GlobeView position={currentPosition} track={track} />
      <Hud data={telemetry} />
      <CrewPanel data={crew} />
      {error && <div className="error-toast">{error}</div>}
    </div>
  );
}

export default App;
