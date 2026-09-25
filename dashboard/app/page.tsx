"use client";

import { useEffect, useState } from "react";

import Header from "@/components/Header";
import StatCard from "@/components/StatCard";
import DashboardCard from "@/components/DashboardCard";
import TrafficMap from "@/components/TrafficMap";
import TrafficCharts from "@/components/TrafficCharts";
import SystemStatus from "@/components/SystemStatus";
import DemoMode from "@/components/DemoMode";

import {
  getCameras,
  getDetections,
  getTrajectories,
  getAnalytics,
  getAlerts,
  getTrafficHeatmap,
} from "@/lib/api";

export default function Home() {
  const [latestProcessing, setLatestProcessing] =
    useState<{
      job_id: string;
      camera_code: string;
      filename: string;
    } | null>(null);
  const [cameras, setCameras] = useState<any[]>([]);
  const [detections, setDetections] = useState<any[]>([]);
  const [trajectories, setTrajectories] = useState<any[]>([]);
  const [analytics, setAnalytics] = useState<any[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [heatmapData, setHeatmapData] = useState<any[]>([]);



    useEffect(() => {
    const stored =
      sessionStorage.getItem(
        "citytrace_latest_processing"
      );

    if (!stored) return;

    try {
      setLatestProcessing(
        JSON.parse(stored)
      );
    } catch {
      sessionStorage.removeItem(
        "citytrace_latest_processing"
      );
    }
  }, []);


  useEffect(() => {
    let mounted = true;

    async function loadData() {
      try {
        const [
          cameraData,
          detectionData,
          trajectoryData,
          analyticsData,
          alertData,
          heatmapResult,
        ] = await Promise.all([
          getCameras(),
          getDetections(),
          getTrajectories(),
          getAnalytics(),
          getAlerts(),
          getTrafficHeatmap(),
        ]);

        if (!mounted) return;

        setCameras(cameraData);
        setDetections(detectionData);
        setTrajectories(trajectoryData);
        setAnalytics(analyticsData);
        setAlerts(alertData);
        setHeatmapData(heatmapResult);
      } catch (error) {
        console.error("API Error:", error);
      }
    }

    loadData();

    const interval = setInterval(loadData, 5000);

    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  /* =========================
     DASHBOARD CALCULATIONS
  ========================= */

  const configuredCameras = cameras.length;

const activeCameras = cameras.filter(
  (camera) => camera.is_active
).length;

 
  const totalVehicles = detections.length;

  
  const validPlates = detections.filter(
    (detection) => detection.plate_valid
  ).length;


const validatedPlateRecords = validPlates;

const offlineBenchmark = {
  exactMatches: 12,
  totalSamples: 12,
};

const offlineBenchmarkRate =
  (offlineBenchmark.exactMatches /
    offlineBenchmark.totalSamples) *
  100;

 
  const activeAlerts = alerts.filter(
    (alert) => !alert.is_resolved
  ).length;

 
  const bottlenecks = heatmapData.filter(
    (item) => item.bottleneck
  ).length;

 
  const trackedTrajectories = trajectories.length;

 
  const latestByCamera = new Map<string, any>();

  analytics.forEach((item) => {
    const existing = latestByCamera.get(item.camera_id);

    if (!existing || item.id > existing.id) {
      latestByCamera.set(item.camera_id, item);
    }
  });

  const latestAnalytics = Array.from(
    latestByCamera.values()
  ).sort((a, b) =>
    String(a.camera_id).localeCompare(
      String(b.camera_id)
    )
  );


  const averageSpeed =
    latestAnalytics.length > 0
      ? latestAnalytics.reduce(
          (sum, item) =>
            sum + (Number(item.average_speed) || 0),
          0
        ) / latestAnalytics.length
      : 0;

  const criticalCameras = heatmapData.filter(
    (item) =>
      String(item.congestion_level).toUpperCase() ===
      "CRITICAL"
  ).length;

  const highTrafficCameras = heatmapData.filter(
    (item) =>
      String(item.congestion_level).toUpperCase() ===
      "HIGH"
  ).length;

  /* =========================
     UI
  ========================= */

  return (
    <main className="min-h-screen bg-gray-50">
      <Header />

      <div className="px-4 py-5 sm:p-6">

        {/* =========================
            OVERVIEW
        ========================= */}

        <div className="mb-8">
          <div className="flex flex-wrap items-center gap-3">

            <h1 className="text-xl font-bold text-black sm:text-2xl">
              City Traffic Intelligence Dashboard
            </h1>

            <span className="flex items-center gap-1.5 rounded-full bg-green-100 px-2.5 py-1 text-xs font-medium text-green-700">
              <span className="h-2 w-2 animate-pulse rounded-full bg-green-500" />
              PROTOTYPE MONITORING
            </span>

          </div>

          <p className="mt-2 text-sm text-slate-500">
  Multi-camera ANPR, vehicle trajectory tracking,
  GIS intelligence and urban traffic analytics.
</p>
        </div>

        {/* =========================
            DEMO ENVIRONMENT
        ========================= */}

        <DemoMode />

                {latestProcessing && (
          <div className="mb-6 rounded-2xl border border-green-200 bg-green-50 p-5 shadow-sm">

            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">

              <div className="flex items-start gap-3">

                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-green-100 text-green-700">
                  ✓
                </div>

                <div>

                  <p className="text-sm font-semibold text-green-800">
                    Latest AI Processing Completed
                  </p>

                  <p className="mt-1 text-sm text-green-700">
                    {latestProcessing.filename}
                  </p>

                  <p className="mt-1 text-xs text-green-600">
                    Camera: {latestProcessing.camera_code}
                  </p>

                </div>

              </div>

              <button
                type="button"
                onClick={() => {
  sessionStorage.removeItem("citytrace_latest_processing");
  setLatestProcessing(null);
}}
                className="text-xs font-medium text-green-700 hover:text-green-900"
              >
                Dismiss ×
              </button>

            </div>

          </div>
        )}

        {/* =========================
            MAIN STATISTICS
        ========================= */}

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">

          <StatCard
  title="Configured Cameras"
  value={configuredCameras}
  description="Camera nodes in prototype network"
/>

          <StatCard
            title="Detection Records"
            value={totalVehicles}
            description="Recorded vehicle detections"
          />

          <StatCard
  title="Validated Plate Records"
  value={validPlates}
  description="Records passing plate-format validation"
/>

          <StatCard
            title="Active Alerts"
            value={activeAlerts}
            description="Unresolved security alerts"
          />

        </div>

        {/* =========================
            INTELLIGENCE SUMMARY
        ========================= */}

        {/* =========================
    ANPR PERFORMANCE
========================= */}

<div className="mt-6 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">

  <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">

    <div>
      <h2 className="text-lg font-semibold text-black">
        ANPR Intelligence
      </h2>

      <p className="mt-1 text-sm text-slate-500">
        ANPR validation and offline recognition benchmark.
      </p>
    </div>

    <span className="rounded-full bg-green-50 px-3 py-1 text-xs font-semibold text-green-700">
  OFFLINE TEST SET
</span>

  </div>

  <div className="mt-5 grid gap-4 sm:grid-cols-3">

    {/* DETECTION COVERAGE */}

    <div className="rounded-xl border border-slate-200 bg-slate-50 p-5">

      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
        Vehicle Detections
      </p>

      <p className="mt-2 text-3xl font-bold text-slate-900">
        {totalVehicles}
      </p>

      <p className="mt-2 text-xs text-slate-500">
        Recorded vehicle observations in the current dataset.
      </p>

    </div>


    {/* VALIDATED PLATES */}

    <div className="rounded-xl border border-slate-200 bg-slate-50 p-5">

      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
        Validated Plates
      </p>

      <p className="mt-2 text-3xl font-bold text-green-600">
        {validatedPlateRecords}
      </p>

      <p className="mt-2 text-xs text-slate-500">
        Plate records passing configured format validation.
      </p>

    </div>


    {/* OFFLINE BENCHMARK */}

    <div className="rounded-xl border border-green-200 bg-green-50 p-5">

      <p className="text-xs font-medium uppercase tracking-wide text-green-700">
        Offline Exact-Match Benchmark
      </p>

      <p className="mt-2 text-3xl font-bold text-green-700">
        {offlineBenchmarkRate.toFixed(0)}%
      </p>

      <p className="mt-2 text-xs text-green-700">
        {offlineBenchmark.exactMatches}/
        {offlineBenchmark.totalSamples} manually verified samples.
      </p>

    </div>

  </div>


  {/* BENCHMARK NOTE */}

  <div className="mt-4 rounded-lg border border-green-100 bg-green-50 p-4">

    <p className="text-xs leading-5 text-green-800">

      <span className="font-semibold">
        Evaluation:
      </span>{" "}
      The current offline benchmark achieved{" "}
      <span className="font-semibold">
        {offlineBenchmark.exactMatches}/
        {offlineBenchmark.totalSamples} exact matches
      </span>{" "}
      on the manually verified test set.

    </p>

    <p className="mt-1 text-xs leading-5 text-green-700">
      This benchmark result is specific to the current test set and
      should not be interpreted as city-wide real-world accuracy.
    </p>

  </div>

</div>

        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">

          {/* Traffic Bottlenecks */}

          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">

            <p className="text-sm text-slate-500">
              Traffic Bottlenecks
            </p>

            <p className="mt-2 text-3xl font-bold text-red-600">
              {bottlenecks}
            </p>

            <p className="mt-1 text-xs text-slate-500">
              Locations requiring attention
            </p>

          </div>

          {/* Tracked Trajectories */}

          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">

            <p className="text-sm text-slate-500">
              Tracked Trajectories
            </p>

            <p className="mt-2 text-3xl font-bold text-blue-600">
              {trackedTrajectories}
            </p>

            <p className="mt-1 text-xs text-slate-500">
              Multi-camera vehicle trajectories
            </p>

          </div>

          {/* Average Speed */}

          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">

            <p className="text-sm text-slate-500">
              Average Speed
            </p>

            <p className="mt-2 text-3xl font-bold text-slate-800">
              {averageSpeed.toFixed(1)}
            </p>

            <p className="mt-1 text-xs text-slate-500">
              km/h across monitored cameras
            </p>

          </div>

          {/* Critical Cameras */}

          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">

            <p className="text-sm text-slate-500">
              Critical Cameras
            </p>

            <p className="mt-2 text-3xl font-bold text-orange-600">
              {criticalCameras}
            </p>

            <p className="mt-1 text-xs text-slate-500">
              {highTrafficCameras} additional high-traffic locations
            </p>

          </div>

        </div>

        {/* =========================
            TRAFFIC MAP
        ========================= */}

        <div className="mt-6">

          <DashboardCard title="City Traffic Intelligence Map">

            <div className="mb-4 flex flex-wrap items-center justify-between gap-4">

              <p className="text-sm text-slate-500">
                GIS visualization of congestion,
                bottlenecks and vehicle trajectories.
              </p>

              {/* Legend */}

              <div className="flex flex-wrap items-center gap-3 text-xs">

                <span className="flex items-center gap-1">
                  <span className="h-3 w-3 rounded-full bg-green-500" />
                  LOW
                </span>

                <span className="flex items-center gap-1">
                  <span className="h-3 w-3 rounded-full bg-yellow-400" />
                  MEDIUM
                </span>

                <span className="flex items-center gap-1">
                  <span className="h-3 w-3 rounded-full bg-orange-500" />
                  HIGH
                </span>

                <span className="flex items-center gap-1">
                  <span className="h-3 w-3 rounded-full bg-red-600" />
                  CRITICAL
                </span>

                <span className="flex items-center gap-1">
                  <span className="h-3 w-3 rounded-full bg-blue-600" />
                  TRAJECTORY
                </span>

              </div>

            </div>

            <TrafficMap
              heatmapData={heatmapData}
              cameras={cameras}
              trajectories={trajectories}
            />

          </DashboardCard>

        </div>

        {/* =========================
            ANALYTICS CHARTS
        ========================= */}

        <div className="mt-6">
          <TrafficCharts analytics={analytics} />
        </div>

        {/* =========================
            MAIN GRID
        ========================= */}

        <div className="mt-6 grid gap-6 lg:grid-cols-2">

          {/* Camera Network */}

          <DashboardCard title="Multi-Camera Network">

            <div className="space-y-3">

              {cameras.map((camera) => (

                <div
                  key={camera.camera_id}
                 className="flex flex-col gap-2 rounded-lg bg-slate-950 p-3 sm:flex-row sm:items-center sm:justify-between"
                >

                  <div>

                    <p className="font-medium text-white">
                      {camera.camera_id}
                    </p>

                    <p className="text-xs text-slate-500">
                      {camera.name}
                    </p>

                  </div>

                  <span
                    className={
                      camera.is_active
                        ? "text-xs text-green-400"
                        : "text-xs text-red-400"
                    }
                  >
                    {camera.source_type === "REPLAY"
    ? "REPLAY"
    : "SIMULATED"}
                  </span>

                </div>

              ))}

              {cameras.length === 0 && (
                <p className="text-sm text-slate-500">
                  No cameras available.
                </p>
              )}

            </div>

          </DashboardCard>

          {/* Latest Detections */}

          <DashboardCard title="Latest Detections">

            <div className="space-y-3">

              {detections.slice(0, 6).map((detection) => (

                <div
                  key={detection.id}
                  className="flex flex-col gap-2 rounded-lg bg-slate-950 p-3 sm:flex-row sm:items-center sm:justify-between"
                >

                  <div>

                    <p className="font-mono font-medium text-white">
                      {detection.plate_number || "UNKNOWN"}
                    </p>

                    <p className="text-xs text-slate-500">
                      {detection.camera_id} •{" "}
                      {detection.vehicle_type}
                    </p>

                  </div>

                  <span
                    className={
                      detection.plate_valid
                        ? "text-xs text-green-400"
                        : "text-xs text-yellow-400"
                    }
                  >
                    {detection.plate_valid
  ? "VALIDATED"
  : "REVIEW"}
                  </span>

                </div>

              ))}

              {detections.length === 0 && (
                <p className="text-sm text-slate-500">
                  No detections available.
                </p>
              )}

            </div>

          </DashboardCard>

          {/* Vehicle Trajectories */}

          <DashboardCard title="Vehicle Trajectories">

            {trajectories.length === 0 ? (

              <p className="text-sm text-slate-500">
                No trajectories available.
              </p>

            ) : (

              <div className="space-y-3">

                {trajectories.map((trajectory) => (

                  <div
                    key={trajectory.id}
                    className="rounded-lg bg-slate-950 p-4"
                  >

                    <div className="flex justify-between">

                      <span className="font-mono font-semibold text-white">
                        {trajectory.plate_number}
                      </span>

                      <span className="text-xs text-green-400">
                        {trajectory.completed
                          ? "COMPLETED"
                          : "ACTIVE"}
                      </span>

                    </div>

                    <p className="mt-2 text-sm text-slate-400">
                      {trajectory.route}
                    </p>

                    <p className="mt-1 text-xs text-slate-500">
                      Distance:{" "}
                      {trajectory.distance_km?.toFixed(2)} km
                    </p>

                    <p className="mt-1 text-xs text-slate-500">
                      Average Speed:{" "}
                      {trajectory.average_speed_kmh?.toFixed(2)} km/h
                    </p>

                  </div>

                ))}

              </div>

            )}

          </DashboardCard>

          {/* Traffic Analytics */}

          <DashboardCard title="Traffic Analytics">

            {latestAnalytics.length === 0 ? (

              <p className="text-sm text-slate-500">
                No analytics available.
              </p>

            ) : (

              <div className="space-y-3">

                {latestAnalytics.map((item) => (

                  <div
                    key={item.id}
                    className="flex items-center justify-between rounded-lg bg-slate-950 p-4"
                  >

                    <div>

                      <p className="font-medium text-white">
                        {item.camera_id}
                      </p>

                      <p className="text-xs text-slate-500">
                        Vehicles: {item.vehicle_count}
                      </p>

                    </div>

                    <span
                      className={
                        String(item.congestion_level).toUpperCase() ===
                        "CRITICAL"
                          ? "text-sm font-semibold text-red-400"
                          : String(item.congestion_level).toUpperCase() ===
                            "HIGH"
                          ? "text-sm font-semibold text-orange-400"
                          : String(item.congestion_level).toUpperCase() ===
                            "MEDIUM"
                          ? "text-sm font-semibold text-yellow-400"
                          : "text-sm font-semibold text-green-400"
                      }
                    >
                      {String(
                        item.congestion_level || "LOW"
                      ).toUpperCase()}
                    </span>

                  </div>

                ))}

              </div>

            )}

          </DashboardCard>

        </div>

        {/* =========================
            SECURITY ALERTS
        ========================= */}

        <div className="mt-6">

          <DashboardCard title="Security & Route Alerts">

            {alerts.length === 0 ? (

              <div className="flex items-center gap-2">

                <span className="text-green-500">
                  ✓
                </span>

                <p className="text-sm text-green-600">
                  No security alerts detected.
                </p>

              </div>

            ) : (

              <div className="space-y-3">

                {alerts.map((alert) => (

                  <div
                    key={alert.id}
                    className="rounded-lg border border-red-900 bg-red-950/30 p-4"
                  >

                    <div className="flex justify-between">

                      <span className="font-semibold text-red-400">
                        {alert.alert_type}
                      </span>

                      <span className="text-xs text-red-300">
                        {alert.severity}
                      </span>

                    </div>

                    <p className="mt-2 text-sm text-slate-300">
                      {alert.message}
                    </p>

                    <p className="mt-1 text-xs text-slate-500">
                      Camera: {alert.camera_id}
                    </p>

                  </div>

                ))}

              </div>

            )}

          </DashboardCard>

          {/* System Status */}

          <div className="mt-6">

            <SystemStatus
              cameraCount={cameras.length}
              activeCameraCount={activeCameras}
            />

          </div>

        </div>

      </div>
    </main>
  );
}