const TRAIL_OPTIONS = [
  { label: '15m', hours: 0.25 },
  { label: '1h', hours: 1 },
  { label: '6h', hours: 6 },
  { label: '12h', hours: 12 },
  { label: '24h', hours: 24 },
];

interface TrailSelectorProps {
  value: number;
  onChange: (hours: number) => void;
  loading?: boolean;
}

const TrailSelector = ({
  value,
  onChange,
  loading = false,
}: TrailSelectorProps) => (
  <div className={`trail-selector${loading ? ' trail-selector--loading' : ''}`}>
    <span className="trail-label">TRAIL</span>
    <div className="trail-buttons">
      {TRAIL_OPTIONS.map(({ label, hours }) => (
        <button
          key={hours}
          className={`trail-btn${value === hours ? ' trail-btn--active' : ''}`}
          onClick={() => onChange(hours)}
          aria-pressed={value === hours}
          disabled={loading}
        >
          {label}
        </button>
      ))}
    </div>
  </div>
);

export default TrailSelector;
