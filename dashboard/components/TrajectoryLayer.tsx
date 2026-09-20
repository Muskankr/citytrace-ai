"use client";

import { CircleMarker, Polyline, Popup } from "react-leaflet";

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
          .map((cameraId) => cameraMap.get(cameraId))
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
          <div key={`trajectory-group-${trajectory.id}`}>
            {/* Route line */}
            {positions.length >= 2 && (
              <Polyline
                key={`trajectory-line-${trajectory.id}`}
                positions={positions}
                pathOptions={{
                  weight: 5,
                  opacity: 0.85,
                }}
              >
                <Popup>
                  <div className="text-sm">
                    <strong>
                      Vehicle Trajectory
                    </strong>

                    <div className="mt-2">
                      <strong>Plate:</strong>{" "}
                      {trajectory.plate_number}
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
                      <strong>Average Speed:</strong>{" "}
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
                  </div>
                </Popup>
              </Polyline>
            )}

            {/* Camera points */}
            {routeCameras.map(
              (camera, index) => (
                <CircleMarker
                  key={`trajectory-${trajectory.id}-camera-${camera.camera_id}-${index}`}
                  center={[
                    camera.latitude,
                    camera.longitude,
                  ]}
                  radius={8}
                  pathOptions={{
                    weight: 2,
                    fillOpacity: 0.9,
                  }}
                >
                  <Popup>
                    <div className="text-sm">
                      <strong>
                        {camera.name}
                      </strong>

                      <div className="mt-1">
                        Camera ID:{" "}
                        {camera.camera_id}
                      </div>

                      <div>
                        Route position:{" "}
                        {index + 1}
                      </div>

                      <div>
                        Vehicle:{" "}
                        {trajectory.plate_number}
                      </div>
                    </div>
                  </Popup>
                </CircleMarker>
              )
            )}
          </div>
        );
      })}
    </>
  );
}