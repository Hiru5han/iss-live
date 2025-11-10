import { IssNowResponse } from '../api';
interface HudProps {
  data: IssNowResponse | null;
}
declare const Hud: ({
  data,
}: HudProps) => import('react/jsx-runtime').JSX.Element;
export default Hud;
