"use client";

import { useEffect, useState } from "react";
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Polyline,
  useMap,
} from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

type Camera = {
  id: number;
  camera_id: string;
  name: string;
  latitude: number;
  longitude: number;
  road_name: string;
  direction: string;
  location: string;
  is_active: boolean;
};

type Trajectory = {
  id: number;
  plate_number: string;
  route: string;
  distance_km: number;
  average_speed_kmh: number;
  direction: string;
  completed: boolean;
};

function MapResize() {
  const map = useMap();

  useEffect(() => {
    setTimeout(() => {
      map.invalidateSize();
    }, 200);
  }, [map]);

  return null;
}

const createCameraIcon = (active: boolean) => {
  return L.divIcon({
    className: "",
    html: `
      <div style="
        width: 34px;
        height: 34px;
        border-radius: 50%;
        background: ${active ? "#16a34a" : "#dc2626"};
        border: 4px solid white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 15px;
        font-weight: bold;
      ">
        ●
      </div>
    `,
    iconSize: [34, 34],
    iconAnchor: [17, 17],
  });
};

export default function TrafficMap() {
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [trajectories, setTrajectories] = useState<Trajectory[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadMapData() {
      try {
        const [cameraResponse, trajectoryResponse] = await Promise.all([
          fetch("http://127.0.0.1:8000/cameras/"),
          fetch("http://127.0.0.1:8000/trajectories/"),
        ]);

        if (!cameraResponse.ok || !trajectoryResponse.ok) {
          throw new Error("Failed to load map data");
        }

        const cameraData = await cameraResponse.json();
        const trajectoryData = await trajectoryResponse.json();

        setCameras(cameraData);
        setTrajectories(trajectoryData);
      } catch (error) {
        console.error("Map loading error:", error);
      } finally {
        setLoading(false);
      }
    }

    loadMapData();
  }, []);

  if (loading) {
    return (
      <div className="flex h-[500px] items-center justify-center rounded-xl border border-gray-200 bg-white">
        <div className="text-center">
          <div className="mx-auto mb-3 h-8 w-8 animate-spin rounded-full border-4 border-gray-300 border-t-black" />
          <p className="text-sm text-gray-500">
            Loading city traffic map...
          </p>
        </div>
      </div>
    );
  }

  if (cameras.length === 0) {
    return (
      <div className="flex h-[500px] items-center justify-center rounded-xl border border-gray-200 bg-white">
        <p className="text-sm text-gray-500">
          No camera data available.
        </p>
      </div>
    );
  }

  const center: [number, number] = [
    cameras.reduce((sum, camera) => sum + camera.latitude, 0) /
      cameras.length,
    cameras.reduce((sum, camera) => sum + camera.longitude, 0) /
      cameras.length,
  ];

  /*
    Build trajectory lines from the camera IDs stored
    in the route string.

    Example:
    CAM001 → CAM002 → CAM004
  */
  const trajectoryLines = trajectories
    .map((trajectory) => {
      if (!trajectory.route) return null;

      const cameraIds = trajectory.route
        .split("→")
        .map((id) => id.trim());

      const points: [number, number][] = cameraIds
        .map((cameraId) => {
          const camera = cameras.find(
            (item) => item.camera_id === cameraId
          );

          if (!camera) return null;

          return [camera.latitude, camera.longitude] as [
            number,
            number
          ];
        })
        .filter(
          (point): point is [number, number] => point !== null
        );

      if (points.length < 2) return null;

      return {
        trajectory,
        points,
      };
    })
    .filter(Boolean) as {
    trajectory: Trajectory;
    points: [number, number][];
  }[];

  return (
    <div className="relative overflow-hidden rounded-xl border border-gray-200 bg-white">
      <div className="absolute left-4 top-4 z-[1000] rounded-lg bg-white px-4 py-3 shadow-md">
        <h3 className="text-sm font-semibold text-black">
          City Traffic Network
        </h3>

        <div className="mt-2 flex items-center gap-4 text-xs text-gray-600">
          <div className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-green-600" />
            Active
          </div>

          <div className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-red-600" />
            Offline
          </div>

          <div className="flex items-center gap-1.5">
            <span className="h-0.5 w-5 bg-blue-600" />
            Trajectory
          </div>
        </div>
      </div>

      <MapContainer
        center={center}
        zoom={13}
        scrollWheelZoom={true}
        className="h-[500px] w-full"
      >
        <MapResize />

        <TileLayer
          attribution='&copy; OpenStreetMap contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {cameras.map((camera) => (
          <Marker
            key={camera.camera_id}
            position={[camera.latitude, camera.longitude]}
            icon={createCameraIcon(camera.is_active)}
          >
            <Popup>
              <div className="min-w-[220px]">
                <h3 className="text-base font-bold">
                  {camera.camera_id}
                </h3>

                <p className="mt-1 text-sm font-medium">
                  {camera.name}
                </p>

                <div className="mt-3 space-y-1 text-xs text-gray-600">
                  <p>
                    <strong>Road:</strong> {camera.road_name}
                  </p>

                  <p>
                    <strong>Direction:</strong> {camera.direction}
                  </p>

                  <p>
                    <strong>Location:</strong> {camera.location}
                  </p>

                  <p>
                    <strong>Coordinates:</strong>{" "}
                    {camera.latitude.toFixed(5)},{" "}
                    {camera.longitude.toFixed(5)}
                  </p>
                </div>

                <div className="mt-3">
                  <span
                    className={`rounded-full px-2 py-1 text-xs font-medium ${
                      camera.is_active
                        ? "bg-green-100 text-green-700"
                        : "bg-red-100 text-red-700"
                    }`}
                  >
                    {camera.is_active
                      ? "● System Online"
                      : "● Offline"}
                  </span>
                </div>
              </div>
            </Popup>
          </Marker>
        ))}

        {trajectoryLines.map(({ trajectory, points }) => (
          <Polyline
            key={trajectory.id}
            positions={points}
            pathOptions={{
              color: "#2563eb",
              weight: 5,
              opacity: 0.8,
            }}
          >
            <Popup>
              <div className="min-w-[220px]">
                <h3 className="text-base font-bold">
                  Vehicle Trajectory
                </h3>

                <p className="mt-2 text-sm">
                  <strong>Plate:</strong>{" "}
                  {trajectory.plate_number}
                </p>

                <p className="text-sm">
                  <strong>Route:</strong>{" "}
                  {trajectory.route}
                </p>

                <p className="text-sm">
                  <strong>Distance:</strong>{" "}
                  {trajectory.distance_km?.toFixed(2)} km
                </p>

                <p className="text-sm">
                  <strong>Average Speed:</strong>{" "}
                  {trajectory.average_speed_kmh?.toFixed(2)} km/h
                </p>

                <p className="text-sm">
                  <strong>Direction:</strong>{" "}
                  {trajectory.direction}
                </p>
              </div>
            </Popup>
          </Polyline>
        ))}
      </MapContainer>
    </div>
  );
}