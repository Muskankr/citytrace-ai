"use client";

import { useEffect, useState } from "react";
import { getCameras } from "@/lib/api";

export default function CamerasPage() {
  const [cameras, setCameras] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadCameras() {
      try {
        const data = await getCameras();
        setCameras(data);
      } catch (error) {
        console.error("Camera API Error:", error);
      } finally {
        setLoading(false);
      }
    }

    loadCameras();
  }, []);

  const activeCameras = cameras.filter(
    (camera) => camera.is_active
  ).length;

  const offlineCameras = cameras.length - activeCameras;

  return (
    <main className="min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-black">
          Camera Network
        </h1>

        <p className="mt-1 text-sm text-gray-500">
          Monitor all connected traffic cameras across the city.
        </p>
      </div>

      {/* Summary */}
      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
          <p className="text-sm text-gray-500">
            Total Cameras
          </p>

          <p className="mt-2 text-3xl font-bold text-black">
            {cameras.length}
          </p>
        </div>

        <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
          <p className="text-sm text-gray-500">
            Active Cameras
          </p>

          <p className="mt-2 text-3xl font-bold text-green-600">
            {activeCameras}
          </p>
        </div>

        <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
          <p className="text-sm text-gray-500">
            Offline Cameras
          </p>

          <p className="mt-2 text-3xl font-bold text-red-600">
            {offlineCameras}
          </p>
        </div>
      </div>

      {/* Camera Grid */}
      <div className="mt-8">
        <h2 className="mb-4 text-lg font-semibold text-black">
          Connected Cameras
        </h2>

        {loading ? (
          <div className="rounded-xl border border-gray-200 bg-white p-8 text-center">
            <p className="text-sm text-gray-500">
              Loading camera network...
            </p>
          </div>
        ) : cameras.length === 0 ? (
          <div className="rounded-xl border border-gray-200 bg-white p-8 text-center">
            <p className="text-sm text-gray-500">
              No cameras available.
            </p>
          </div>
        ) : (
          <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
            {cameras.map((camera) => (
              <div
                key={camera.camera_id}
                className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm transition hover:shadow-md"
              >
                {/* Camera ID + Status */}
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-medium uppercase tracking-wider text-gray-400">
                      Camera
                    </p>

                    <h3 className="mt-1 text-lg font-bold text-black">
                      {camera.camera_id}
                    </h3>
                  </div>

                  <span
                    className={`rounded-full px-3 py-1 text-xs font-semibold ${
                      camera.is_active
                        ? "bg-green-100 text-green-700"
                        : "bg-red-100 text-red-700"
                    }`}
                  >
                    {camera.is_active ? "ONLINE" : "OFFLINE"}
                  </span>
                </div>

                {/* Camera Details */}
                <div className="mt-5 space-y-3 border-t border-gray-100 pt-4">
                  <div>
                    <p className="text-xs text-gray-400">
                      Location
                    </p>

                    <p className="mt-1 text-sm font-medium text-gray-800">
                      {camera.name}
                    </p>
                  </div>

                  <div>
                    <p className="text-xs text-gray-400">
                      Road
                    </p>

                    <p className="mt-1 text-sm text-gray-600">
                      {camera.road_name || "N/A"}
                    </p>
                  </div>

                  <div className="flex justify-between">
                    <div>
                      <p className="text-xs text-gray-400">
                        Direction
                      </p>

                      <p className="mt-1 text-sm text-gray-600">
                        {camera.direction || "N/A"}
                      </p>
                    </div>

                    <div className="text-right">
                      <p className="text-xs text-gray-400">
                        Coordinates
                      </p>

                      <p className="mt-1 text-xs text-gray-500">
                        {camera.latitude},{" "}
                        {camera.longitude}
                      </p>
                    </div>
                  </div>
                </div>

                {/* AI Status */}
                <div className="mt-5 flex items-center gap-2 rounded-lg bg-gray-50 px-3 py-2">
                  <span
                    className={`h-2 w-2 rounded-full ${
                      camera.is_active
                        ? "bg-green-500"
                        : "bg-red-500"
                    }`}
                  />

                  <span className="text-xs font-medium text-gray-600">
                    {camera.is_active
                      ? "AI Engine Connected"
                      : "Camera Offline"}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}