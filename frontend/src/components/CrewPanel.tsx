import { CrewResponse } from '../api';

interface CrewPanelProps {
  data: CrewResponse | null;
}

const CrewPanel = ({ data }: CrewPanelProps) => (
  <div className="crew-container">
    <p className="hud-title">ISS CREW</p>
    {data ? (
      <>
        <div className="crew-count">{data.count} aboard</div>
        <ul className="crew-list">
          {data.members.map((member) => (
            <li key={member.name} className="crew-member">
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
