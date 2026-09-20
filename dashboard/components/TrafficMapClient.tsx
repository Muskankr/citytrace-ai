"use client";

import {
  MapContainer,
  TileLayer,
} from "react-leaflet";

import TrafficHeatmap from "./TrafficHeatmap";
import TrajectoryLayer from "./TrajectoryLayer";

type HeatmapItem = {
  camera_id: string;
  camera_name: string;
  latitude: number;
  longitude: number;
  road_name: string;
  direction: string;
  vehicle_count: number;
  traffic_density: number;
  average_speed: number;
  congestion_level: string;
  congestion_score: number;
  incoming_count: number;
  outgoing_count: number;
  bottleneck: boolean;
  heat_intensity: number;
};

type Camera = {
  camera_id: string;
  name: string;
  latitude: number;
  longitude: number;
};

type Trajectory = {
  id: number;
  plate_number: string;
  route?: string | null;
  distance_km?: number | null;
  average_speed_kmh?: number | null;
  direction?: string | null;
  completed?: boolean;
};

type TrafficMapClientProps = {
  heatmapData?: HeatmapItem[];
  cameras?: Camera[];
  trajectories?: Trajectory[];
};

export default function TrafficMapClient({
  heatmapData = [],
  cameras = [],
  trajectories = [],
}: TrafficMapClientProps) {
  return (
    <MapContainer
      center={[28.8955, 76.6066]}
      zoom={13}
      scrollWheelZoom={true}
      className="h-[500px] w-full rounded-2xl"
    >
      <TileLayer
        attribution="&copy; OpenStreetMap contributors"
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      <TrafficHeatmap
        data={heatmapData}
      />

      <TrajectoryLayer
        cameras={cameras}
        trajectories={trajectories}
      />
    </MapContainer>
  );
}