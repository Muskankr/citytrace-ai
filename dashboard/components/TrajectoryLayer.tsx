"use client";

import {
  CircleMarker,
  Marker,
  Polyline,
  Popup,
} from "react-leaflet";
import L from "leaflet";

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

type TrajectoryLayerProps = {
  cameras?: Camera[];
  trajectories?: Trajectory[];
};

function createSequenceIcon(
  number: number,
  type: "start" | "middle" | "end"
) {
  const background =
    type === "start"
      ? "#16a34a"
      : type === "end"
        ? "#dc2626"
        : "#2563eb";

  return L.divIcon({
    className: "trajectory-sequence-icon",
    html: `
      <div
        style="
          width:32px;
          height:32px;
          border-radius:9999px;
          background:${background};
          color:white;
          display:flex;
          align-items:center;
          justify-content:center;
          font-weight:700;
          font-size:13px;
          border:3px solid white;
          box-shadow:0 2px 8px rgba(0,0,0,0.35);
        "
      >
        ${number}
      </div>
    `,
    iconSize: [32, 32],
    iconAnchor: [16, 16],
  });
}

function createArrowIcon(
  rotation: number
) {
  return L.divIcon({
    className: "trajectory-arrow-icon",
    html: `
      <div
        style="
          width:28px;
          height:28px;
          display:flex;
          align-items:center;
          justify-content:center;
          transform:rotate(${rotation}deg);
          font-size:24px;
          font-weight:900;
          color:#1d4ed8;
          text-shadow:
            0 1px 2px white,
            1px 0 2px white,
            0 -1px 2px white,
            -1px 0 2px white;
        "
      >
        ➜
      </div>
    `,
    iconSize: [28, 28],
    iconAnchor: [14, 14],
  });
}

function calculateBearing(
  from: [number, number],
  to: [number, number]
) {
  const lat1 = (from[0] * Math.PI) / 180;
  const lat2 = (to[0] * Math.PI) / 180;

  const deltaLon =
    ((to[1] - from[1]) * Math.PI) / 180;

  const y =
    Math.sin(deltaLon) * Math.cos(lat2);

  const x =
    Math.cos(lat1) * Math.sin(lat2) -
    Math.sin(lat1) *
      Math.cos(lat2) *
      Math.cos(deltaLon);

  const bearing =
    (Math.atan2(y, x) * 180) / Math.PI;

  return (bearing + 360) % 360;
}

export default function TrajectoryLayer({
  cameras = [],
  trajectories = [],
}: TrajectoryLayerProps) {
  const cameraMap = new Map(
    cameras.map((camera) => [
      camera.camera_id,
      camera,
    ])
  );

  return (
    <>
      {trajectories.map((trajectory) => {
        if (!trajectory.route) {
          return null;
        }

        const routeIds = trajectory.route
          .split("→")
          .map((id) => id.trim())
          .filter(Boolean);

        const routeCameras = routeIds
          .map((cameraId) =>
            cameraMap.get(cameraId)
          )
          .filter(
            (camera): camera is Camera =>
              Boolean(camera)
          );

        if (routeCameras.length === 0) {
          return null;
        }

        const positions = routeCameras.map(
          (camera) =>
            [
              camera.latitude,
              camera.longitude,
            ] as [number, number]
        );

        return (
          <div
            key={`trajectory-group-${trajectory.id}`}
          >
            {/* =========================
                MAIN TRAJECTORY LINE
            ========================== */}
            {positions.length >= 2 && (
              <Polyline
                positions={positions}
                pathOptions={{
                  weight: 7,
                  opacity: 0.8,
                }}
              >
                <Popup>
                  <div className="text-sm">
                    <strong>
                      Vehicle Trajectory
                    </strong>

                    <div className="mt-2">
                      <strong>Plate:</strong>{" "}
                      {trajectory.plate_number ||
                        "—"}
                    </div>

                    <div>
                      <strong>Route:</strong>{" "}
                      {trajectory.route}
                    </div>

                    <div>
                      <strong>Distance:</strong>{" "}
                      {trajectory.distance_km != null
                        ? `${trajectory.distance_km.toFixed(
                            2
                          )} km`
                        : "—"}
                    </div>

                    <div>
                      <strong>
                        Average Speed:
                      </strong>{" "}
                      {trajectory.average_speed_kmh !=
                      null
                        ? `${trajectory.average_speed_kmh.toFixed(
                            2
                          )} km/h`
                        : "—"}
                    </div>

                    <div>
                      <strong>Direction:</strong>{" "}
                      {trajectory.direction || "—"}
                    </div>

                    <div>
                      <strong>Status:</strong>{" "}
                      {trajectory.completed
                        ? "Completed"
                        : "Active"}
                    </div>
                  </div>
                </Popup>
              </Polyline>
            )}

            {/* =========================
                DIRECTION ARROWS
            ========================== */}
            {positions.length >= 2 &&
              positions
                .slice(0, -1)
                .map((position, index) => {
                  const nextPosition =
                    positions[index + 1];

                  const midpoint: [
                    number,
                    number
                  ] = [
                    (position[0] +
                      nextPosition[0]) /
                      2,
                    (position[1] +
                      nextPosition[1]) /
                      2,
                  ];

                  const bearing =
                    calculateBearing(
                      position,
                      nextPosition
                    );

                  return (
                    <Marker
                      key={`trajectory-arrow-${trajectory.id}-${index}`}
                      position={midpoint}
                      icon={createArrowIcon(
                        bearing
                      )}
                      interactive={false}
                    />
                  );
                })}

            {/* =========================
                CAMERA SEQUENCE
            ========================== */}
            {routeCameras.map(
              (camera, index) => {
                const isStart = index === 0;
                const isEnd =
                  index ===
                  routeCameras.length - 1;

                const markerType =
                  isStart
                    ? "start"
                    : isEnd
                      ? "end"
                      : "middle";

                return (
                  <Marker
                    key={`trajectory-sequence-${trajectory.id}-${camera.camera_id}-${index}`}
                    position={[
                      camera.latitude,
                      camera.longitude,
                    ]}
                    icon={createSequenceIcon(
                      index + 1,
                      markerType
                    )}
                  >
                    <Popup>
                      <div className="min-w-[190px] text-sm">
                        <div className="font-bold text-gray-900">
                          {camera.name}
                        </div>

                        <div className="mt-1">
                          <strong>
                            Camera:
                          </strong>{" "}
                          {camera.camera_id}
                        </div>

                        <div>
                          <strong>
                            Route position:
                          </strong>{" "}
                          {index + 1} of{" "}
                          {routeCameras.length}
                        </div>

                        <div>
                          <strong>
                            Vehicle:
                          </strong>{" "}
                          {trajectory.plate_number ||
                            "—"}
                        </div>

                        <div className="mt-2">
                          <strong>Status:</strong>{" "}
                          {isStart
                            ? "Journey Start"
                            : isEnd
                              ? "Journey End"
                              : "Transit Camera"}
                        </div>

                        {trajectory.direction && (
                          <div>
                            <strong>
                              Direction:
                            </strong>{" "}
                            {trajectory.direction}
                          </div>
                        )}
                      </div>
                    </Popup>
                  </Marker>
                );
              }
            )}

            {/* =========================
                CAMERA POINTS
                Extra visual layer
            ========================== */}
            {routeCameras.map(
              (camera, index) => (
                <CircleMarker
                  key={`trajectory-point-${trajectory.id}-${camera.camera_id}-${index}`}
                  center={[
                    camera.latitude,
                    camera.longitude,
                  ]}
                  radius={5}
                  pathOptions={{
                    weight: 2,
                    fillOpacity: 1,
                  }}
                  interactive={false}
                />
              )
            )}
          </div>
        );
      })}
    </>
  );
}