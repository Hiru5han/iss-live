import { useEffect, useRef } from 'react';
import Globe from 'globe.gl';

export type GlobePoint = {
  lat: number;
  lon: number;
};

interface GlobeViewProps {
  position?: GlobePoint;
  track: GlobePoint[];
}

const CAMERA_ALTITUDE = 1.8;

const GlobeView = ({ position, track }: GlobeViewProps) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const globeRef = useRef<ReturnType<typeof Globe>>();

  useEffect(() => {
    if (!containerRef.current || globeRef.current) {
      return;
    }

    const container = containerRef.current;
    const globe = Globe()(container);
    globe.pointColor(() => '#fde047');
    globe.pointLabel(() => 'International Space Station');
    globe.backgroundColor('#020617');
    globe.globeImageUrl('//unpkg.com/three-globe/example/img/earth-dark.jpg');
    globe.bumpImageUrl(
      '//unpkg.com/three-globe/example/img/earth-topology.png',
    );
    globe.showAtmosphere(true);
    globe.atmosphereColor('#38bdf8');
    globe.atmosphereAltitude(0.15);
    globe.controls().autoRotate = true;
    globe.controls().autoRotateSpeed = 0.35;
    globe.pathColor(() => '#38bdf8');
    globe.pathDashLength(0.2);
    globe.pathDashGap(0.015);
    globe.pathDashAnimateTime(2000);
    globe.pathPointLat('lat');
    globe.pathPointLng('lon');
    globe.pointLat('lat');
    globe.pointLng('lon');
    globe.pointAltitude(() => 0.015);

    globeRef.current = globe;

    return () => {
      globeRef.current = undefined;
      container.innerHTML = '';
    };
  }, []);

  useEffect(() => {
    const globe = globeRef.current;
    if (!globe || !position) {
      return;
    }

    const point = { lat: position.lat, lon: position.lon };
    globe.pointsData([point]);
    globe.pointOfView(
      {
        lat: point.lat,
        lng: point.lon,
        altitude: CAMERA_ALTITUDE,
      },
      1500,
    );
  }, [position]);

  useEffect(() => {
    const globe = globeRef.current;
    if (!globe) {
      return;
    }

    if (!track.length) {
      globe.pathsData([]);
      return;
    }

    globe.pathsData([track]);
  }, [track]);

  return <div ref={containerRef} className="globe-container" />;
};

export default GlobeView;
