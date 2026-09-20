"use client";

import {
  Circle,
  CircleMarker,
  Popup,
} from "react-leaflet";

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

type TrafficHeatmapProps = {
  data: HeatmapItem[];
};

export default function TrafficHeatmap({
  data,
}: TrafficHeatmapProps) {
  return (
    <>
      {data.map((item) => {
        const intensity = Math.max(
          0.15,
          Math.min(item.heat_intensity, 1)
        );

        const radius = 25 + intensity * 25;

        return (
          <div key={item.camera_id}>
            {/* Traffic intensity area */}
            <Circle
              center={[item.latitude, item.longitude]}
              radius={radius}
              pathOptions={{
                fillOpacity: intensity * 0.35,
                weight: 1,
              }}
            />

            {/* Camera / bottleneck marker */}
            <CircleMarker
              center={[item.latitude, item.longitude]}
              radius={item.bottleneck ? 10 : 7}
              pathOptions={{
                fillOpacity: 0.9,
                weight: 2,
              }}
            >
              <Popup>
                <div className="min-w-[220px]">
                  <h3 className="mb-2 text-base font-bold">
                    {item.camera_id}
                  </h3>

                  <p className="text-sm">
                    <b>Road:</b> {item.road_name}
                  </p>

                  <p className="text-sm">
                    <b>Direction:</b> {item.direction}
                  </p>

                  <p className="text-sm">
                    <b>Vehicles:</b> {item.vehicle_count}
                  </p>

                  <p className="text-sm">
                    <b>Density:</b> {item.traffic_density}
                  </p>

                  <p className="text-sm">
                    <b>Average Speed:</b>{" "}
                    {item.average_speed} km/h
                  </p>

                  <p className="text-sm">
                    <b>Congestion:</b>{" "}
                    {item.congestion_level}
                  </p>

                  <p className="text-sm">
                    <b>Congestion Score:</b>{" "}
                    {item.congestion_score}/100
                  </p>

                  <p className="text-sm">
                    <b>Incoming:</b> {item.incoming_count}
                  </p>

                  <p className="text-sm">
                    <b>Outgoing:</b> {item.outgoing_count}
                  </p>

                  {item.bottleneck && (
                    <div className="mt-2 rounded-lg border border-red-300 bg-red-50 p-2 text-sm font-bold text-red-700">
                      ⚠ BOTTLENECK DETECTED
                    </div>
                  )}
                </div>
              </Popup>
            </CircleMarker>
          </div>
        );
      })}
    </>
  );
}