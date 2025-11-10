import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useMemo, useState } from 'react';
import GlobeView from './components/GlobeView';
import Hud from './components/Hud';
import { fetchIssNow } from './api';
const POLL_INTERVAL_MS = 5000;
const MAX_TRACK_POINTS = 180; // ~15 minutes of history at 5s cadence
function App() {
    const [telemetry, setTelemetry] = useState(null);
    const [track, setTrack] = useState([]);
    const [error, setError] = useState(null);
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
            }
            catch (err) {
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
    const currentPosition = useMemo(() => {
        if (!telemetry) {
            return undefined;
        }
        return { lat: telemetry.lat, lon: telemetry.lon };
    }, [telemetry]);
    return (_jsxs("div", { className: "app-shell", children: [_jsx(GlobeView, { position: currentPosition, track: track }), _jsx(Hud, { data: telemetry }), error && _jsx("div", { className: "error-toast", children: error })] }));
}
export default App;
