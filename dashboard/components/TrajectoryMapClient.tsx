"use client";

import {
  MapContainer,
  TileLayer,
} from "react-leaflet";

import TrajectoryLayer from "./TrajectoryLayer";

interface Camera {
  camera_id: string;
  name: string;
  latitude: number;
  longitude: number;
}

interface TrajectoryMapClientProps {
  cameras?: Camera[];
}

export default function TrajectoryMapClient({
  cameras = [],
}: TrajectoryMapClientProps) {
  const trajectory = {
    id: 1,
    plate_number: "",
    route: cameras
      .map((camera) => camera.camera_id)
      .join("→"),
    completed: true,
  };

  return (
    <MapContainer
      center={[28.8955, 76.6066]}
      zoom={13}
      scrollWheelZoom={true}
      className="h-[450px] w-full rounded-lg"
    >
      <TileLayer
        attribution="&copy; OpenStreetMap contributors"
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      <TrajectoryLayer
        cameras={cameras}
        trajectories={[trajectory]}
      />
    </MapContainer>
  );
}