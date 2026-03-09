import { CrewResponse } from '../api';

interface CrewPanelProps {
  data: CrewResponse | null;
  onClose?: () => void;
}

const CrewPanel = ({ data, onClose }: CrewPanelProps) => (
  <div className="crew-container">
    {/* Drag handle — visible only on mobile */}
    <div className="crew-handle" />

    <div className="crew-header">
      <p className="hud-title">ISS CREW</p>
      {onClose && (
        <button
          className="crew-close-btn"
          onClick={onClose}
          aria-label="Close crew panel"
        >
          ✕
        </button>
      )}
    </div>

    {data ? (
      <>
        <div className="crew-count">{data.count} aboard</div>
        <ul className="crew-list">
          {data.members.map((member) => (
            <li key={member.name} className="crew-member">
              <span className="crew-member-icon">👩‍🚀</span>
              {member.name}
            </li>
          ))}
        </ul>
      </>
    ) : (
      <div className="crew-count">Loading...</div>
    )}
  </div>
);

export default CrewPanel;
