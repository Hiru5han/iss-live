import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
const formatNumber = (value, fraction = 2) => typeof value === 'number' ? value.toFixed(fraction) : '—';
const formatTime = (timestamp) => {
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
    }
    catch (error) {
        return timestamp;
    }
};
const Hud = ({ data }) => (_jsxs("div", { className: "hud-container", children: [_jsx("p", { className: "hud-title", children: "ISS TELEMETRY" }), _jsxs("div", { className: "metric-row", children: [_jsx("span", { children: "Latitude" }), _jsxs("span", { children: [formatNumber(data?.lat), "\u00B0"] })] }), _jsxs("div", { className: "metric-row", children: [_jsx("span", { children: "Longitude" }), _jsxs("span", { children: [formatNumber(data?.lon), "\u00B0"] })] }), _jsxs("div", { className: "metric-row", children: [_jsx("span", { children: "Altitude" }), _jsxs("span", { children: [formatNumber(data?.altitude_km, 1), " km"] })] }), _jsxs("div", { className: "metric-row", children: [_jsx("span", { children: "Velocity" }), _jsxs("span", { children: [formatNumber(data?.velocity_kmh, 0), " km/h"] })] }), _jsxs("div", { className: "metric-row", children: [_jsx("span", { children: "Source" }), _jsx("span", { children: data?.source ?? '—' })] }), _jsxs("div", { className: "timestamp", children: ["Last update: ", formatTime(data?.timestamp)] }), _jsxs("div", { className: "pills", children: [_jsx("span", { className: "pill pill-live", children: data ? 'LIVE' : 'ACQ' }), data?.stale && _jsx("span", { className: "pill pill-stale", children: "STALE" })] })] }));
export default Hud;
