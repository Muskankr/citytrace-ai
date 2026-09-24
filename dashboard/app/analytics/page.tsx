"use client";

import { useEffect, useMemo, useState } from "react";
import { getAnalytics, getODMatrix } from "@/lib/api";
import ODMatrix from "@/components/ODMatrix";
import TrafficCharts from "@/components/TrafficCharts";

export default function AnalyticsPage() {
  const [analytics, setAnalytics] = useState<any[]>([]);
  const [odMatrix, setOdMatrix] =
    useState<Record<string, Record<string, number>>>({});

  const [loading, setLoading] = useState(true);
  const [odLoading, setOdLoading] = useState(true);

  useEffect(() => {
    async function loadAnalytics() {
      try {
        const data = await getAnalytics();
        setAnalytics(data);
      } catch (error) {
        console.error("Analytics API Error:", error);
      } finally {
        setLoading(false);
      }
    }

    async function loadODMatrix() {
      try {
        const data = await getODMatrix();
        setOdMatrix(data);
      } catch (error) {
        console.error("OD Matrix API Error:", error);
      } finally {
        setOdLoading(false);
      }
    }

    loadAnalytics();
    loadODMatrix();
  }, []);

  /*
   * Keep only the latest analytics record for each camera.
   *
   * The backend may contain historical TrafficAnalytics
   * records for the same camera. For the dashboard we want
   * the current/latest state of each camera only.
   */
  const latestAnalytics = useMemo(() => {
    const latestByCamera = new Map<string, any>();

    for (const item of analytics) {
      const cameraId = item.camera_id;

      if (!cameraId) {
        continue;
      }

      const existing = latestByCamera.get(cameraId);

      if (!existing) {
        latestByCamera.set(cameraId, item);
        continue;
      }

      const existingTime = existing.timestamp
        ? new Date(existing.timestamp).getTime()
        : 0;

      const currentTime = item.timestamp
        ? new Date(item.timestamp).getTime()
        : 0;

      if (currentTime >= existingTime) {
        latestByCamera.set(cameraId, item);
      }
    }

    return Array.from(latestByCamera.values()).sort((a, b) =>
      String(b.camera_id).localeCompare(String(a.camera_id))
    );
  }, [analytics]);

  /*
   * Overall statistics are calculated from the latest
   * record of each camera, not historical duplicates.
   */
  const totalVehicles = latestAnalytics.reduce(
    (sum, item) => sum + (item.vehicle_count || 0),
    0
  );

  const totalCars = latestAnalytics.reduce(
    (sum, item) => sum + (item.car_count || 0),
    0
  );

  const totalMotorcycles = latestAnalytics.reduce(
    (sum, item) => sum + (item.motorcycle_count || 0),
    0
  );

  const totalBuses = latestAnalytics.reduce(
    (sum, item) => sum + (item.bus_count || 0),
    0
  );

  const totalTrucks = latestAnalytics.reduce(
    (sum, item) => sum + (item.truck_count || 0),
    0
  );

  const averageDensity =
    latestAnalytics.length > 0
      ? latestAnalytics.reduce(
          (sum, item) => sum + (item.traffic_density || 0),
          0
        ) / latestAnalytics.length
      : 0;

  function getCongestionStyle(level: string) {
    const value = level?.toLowerCase();

    if (value === "high" || value === "critical") {
      return "bg-red-100 text-red-700";
    }

    if (value === "medium" || value === "moderate") {
      return "bg-yellow-100 text-yellow-700";
    }

    return "bg-green-100 text-green-700";
  }

  return (
    <main className="min-h-screen bg-gray-50 p-6">

      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-black">
          Traffic Analytics
        </h1>

        <p className="mt-1 text-sm text-gray-500">
          City-wide traffic density, congestion and
          origin-destination analysis.
        </p>
      </div>

      {/* Overall Statistics */}
      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">

        <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
          <p className="text-sm text-gray-500">
            Total Vehicles
          </p>

          <p className="mt-2 text-3xl font-bold text-black">
            {totalVehicles}
          </p>
        </div>

        <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
          <p className="text-sm text-gray-500">
            Cars
          </p>

          <p className="mt-2 text-3xl font-bold text-blue-600">
            {totalCars}
          </p>
        </div>

        <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
          <p className="text-sm text-gray-500">
            Motorcycles
          </p>

          <p className="mt-2 text-3xl font-bold text-purple-600">
            {totalMotorcycles}
          </p>
        </div>

        <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
          <p className="text-sm text-gray-500">
            Avg. Traffic Density
          </p>

          <p className="mt-2 text-3xl font-bold text-orange-600">
            {averageDensity.toFixed(1)}
          </p>
        </div>

      </div>

      {/* Vehicle Type Summary */}
      <div className="mt-6 rounded-xl border border-gray-200 bg-white p-6 shadow-sm">

        <h2 className="text-lg font-semibold text-black">
          Vehicle Classification
        </h2>

        <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">

          <div className="rounded-lg bg-gray-50 p-4">
            <p className="text-xs text-gray-400">
              Cars
            </p>

            <p className="mt-1 text-xl font-bold text-black">
              {totalCars}
            </p>
          </div>

          <div className="rounded-lg bg-gray-50 p-4">
            <p className="text-xs text-gray-400">
              Motorcycles
            </p>

            <p className="mt-1 text-xl font-bold text-black">
              {totalMotorcycles}
            </p>
          </div>

          <div className="rounded-lg bg-gray-50 p-4">
            <p className="text-xs text-gray-400">
              Buses
            </p>

            <p className="mt-1 text-xl font-bold text-black">
              {totalBuses}
            </p>
          </div>

          <div className="rounded-lg bg-gray-50 p-4">
            <p className="text-xs text-gray-400">
              Trucks
            </p>

            <p className="mt-1 text-xl font-bold text-black">
              {totalTrucks}
            </p>
          </div>

        </div>
      </div>


            {/* Traffic Flow Trend */}
      <div className="mt-8">
        <TrafficCharts analytics={analytics} />
      </div>

      {/* Origin-Destination Analytics */}
      <div className="mt-8">

        {odLoading ? (
          <div className="rounded-xl border border-gray-200 bg-white p-10 text-center">
            <p className="text-sm text-gray-500">
              Loading origin-destination analytics...
            </p>
          </div>
        ) : (
          <ODMatrix data={odMatrix} />
        )}

      </div>

      {/* Camera Analytics */}
      <div className="mt-8">

        <h2 className="mb-4 text-lg font-semibold text-black">
          Camera-wise Traffic Analysis
        </h2>

        {loading ? (

          <div className="rounded-xl border border-gray-200 bg-white p-10 text-center">
            <p className="text-sm text-gray-500">
              Loading traffic analytics...
            </p>
          </div>

        ) : latestAnalytics.length === 0 ? (

          <div className="rounded-xl border border-gray-200 bg-white p-10 text-center">
            <p className="text-sm text-gray-500">
              No traffic analytics available.
            </p>
          </div>

        ) : (

          <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">

            {latestAnalytics.map((item) => (

              <div
                key={item.camera_id}
                className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm transition hover:shadow-md"
              >

                {/* Camera + Congestion */}
                <div className="flex items-center justify-between">

                  <div>
                    <p className="text-xs uppercase tracking-wider text-gray-400">
                      Camera
                    </p>

                    <h3 className="mt-1 text-lg font-bold text-black">
                      {item.camera_id}
                    </h3>
                  </div>

                  <span
                    className={`rounded-full px-3 py-1 text-xs font-semibold ${getCongestionStyle(
                      item.congestion_level
                    )}`}
                  >
                    {item.congestion_level || "UNKNOWN"}
                  </span>

                </div>

                {/* Vehicle Count */}
                <div className="mt-6 rounded-lg bg-gray-950 p-5">

                  <p className="text-xs uppercase tracking-wider text-gray-500">
                    Vehicles Detected
                  </p>

                  <p className="mt-1 text-3xl font-bold text-white">
                    {item.vehicle_count || 0}
                  </p>

                </div>

                {/* Vehicle Types */}
                <div className="mt-5 grid grid-cols-2 gap-3">

                  <div className="rounded-lg bg-gray-50 p-3">
                    <p className="text-xs text-gray-400">
                      Cars
                    </p>

                    <p className="mt-1 font-semibold text-black">
                      {item.car_count || 0}
                    </p>
                  </div>

                  <div className="rounded-lg bg-gray-50 p-3">
                    <p className="text-xs text-gray-400">
                      Motorcycles
                    </p>

                    <p className="mt-1 font-semibold text-black">
                      {item.motorcycle_count || 0}
                    </p>
                  </div>

                  <div className="rounded-lg bg-gray-50 p-3">
                    <p className="text-xs text-gray-400">
                      Buses
                    </p>

                    <p className="mt-1 font-semibold text-black">
                      {item.bus_count || 0}
                    </p>
                  </div>

                  <div className="rounded-lg bg-gray-50 p-3">
                    <p className="text-xs text-gray-400">
                      Trucks
                    </p>

                    <p className="mt-1 font-semibold text-black">
                      {item.truck_count || 0}
                    </p>
                  </div>

                </div>

                {/* Density + Flow */}
                <div className="mt-5 border-t border-gray-100 pt-4">

                  <div className="flex justify-between">

                    <div>
                      <p className="text-xs text-gray-400">
                        Traffic Density
                      </p>

                      <p className="mt-1 font-semibold text-black">
                        {item.traffic_density ?? 0}
                      </p>
                    </div>

                    <div className="text-right">

                      <p className="text-xs text-gray-400">
                        Avg. Speed
                      </p>

                      <p className="mt-1 font-semibold text-black">
                        {item.average_speed
                          ? `${item.average_speed.toFixed(1)} km/h`
                          : "N/A"}
                      </p>

                    </div>

                  </div>

                  <div className="mt-4 flex justify-between text-xs">

                    <span className="text-green-600">
                      Incoming: {item.incoming_count || 0}
                    </span>

                    <span className="text-blue-600">
                      Outgoing: {item.outgoing_count || 0}
                    </span>

                  </div>

                </div>

              </div>

            ))}

          </div>

        )}

      </div>

    </main>
  );
}