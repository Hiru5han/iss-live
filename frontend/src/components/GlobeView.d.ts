export type GlobePoint = {
  lat: number;
  lon: number;
};
interface GlobeViewProps {
  position?: GlobePoint;
  track: GlobePoint[];
}
declare const GlobeView: ({
  position,
  track,
}: GlobeViewProps) => import('react/jsx-runtime').JSX.Element;
export default GlobeView;
