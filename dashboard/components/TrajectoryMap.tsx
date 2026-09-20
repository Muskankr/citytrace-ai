"use client";

import { useEffect, useRef } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

interface CameraPoint {
  camera_id: string;
  name: string;
  latitude: number;
  longitude: number;
  road_name: string;
}

interface TrajectoryMapProps {
  cameras: CameraPoint[];
}

export default function TrajectoryMap({
  cameras,
}: TrajectoryMapProps) {
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<L.Map | null>(null);

  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (mapRef.current) {
      mapRef.current.remove();
      mapRef.current = null;
    }

    if (cameras.length === 0) {
      return;
    }

    const map = L.map(mapContainerRef.current);

    mapRef.current = map;

    L.tileLayer(
      "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
      {
        attribution: "&copy; OpenStreetMap contributors",
      }
    ).addTo(map);

    const points: L.LatLngExpression[] = [];

    cameras.forEach((camera, index) => {
      const position: L.LatLngExpression = [
        camera.latitude,
        camera.longitude,
      ];

      points.push(position);

      const marker = L.marker(position).addTo(map);

      marker.bindPopup(`
        <div style="min-width: 190px; font-family: Arial, sans-serif;">
          <strong>${camera.camera_id}</strong>
          <br />
          ${camera.name}
          <br />
          <small>${camera.road_name}</small>
          <br />
          <small>
            Route position: ${index + 1}
          </small>
        </div>
      `);
    });

    if (points.length >= 2) {
      L.polyline(points, {
        weight: 5,
        opacity: 0.8,
      }).addTo(map);
    }

    if (points.length === 1) {
      map.setView(points[0], 15);
    } else {
      map.fitBounds(L.latLngBounds(points), {
        padding: [40, 40],
      });
    }

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, [cameras]);

  return (
    <div
      ref={mapContainerRef}
      className="h-[450px] w-full overflow-hidden rounded-lg"
    />
  );
}