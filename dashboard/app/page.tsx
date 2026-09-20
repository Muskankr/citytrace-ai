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
  const [cameras, setCameras] = useState<any[]>([]);
  const [detections, setDetections] = useState<any[]>([]);
  const [trajectories, setTrajectories] = useState<any[]>([]);
  const [analytics, setAnalytics] = useState<any[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [heatmapData, setHeatmapData] = useState<any[]>([]);

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

  const activeCameras = cameras.filter(
    (camera) => camera.is_active
  ).length;

  /*
   * Every detection returned by the API
   * represents a recorded vehicle detection.
   */
  const totalVehicles = detections.length;

  /*
   * Count validated ANPR detection records.
   */
  const validPlates = detections.filter(
    (detection) => detection.plate_valid
  ).length;

  /*
   * Only unresolved alerts are active.
   */
  const activeAlerts = alerts.filter(
    (alert) => !alert.is_resolved
  ).length;

  /*
   * Heatmap already represents monitored camera
   * locations, so bottlenecks are counted from it.
   */
  const bottlenecks = heatmapData.filter(
    (item) => item.bottleneck
  ).length;

  /*
   * Total tracked trajectories.
   *
   * We intentionally do NOT call this "active"
   * because completed trajectories are still useful
   * evidence of multi-camera tracking.
   */
  const trackedTrajectories = trajectories.length;

  /*
   * ------------------------------------------------
   * LATEST ANALYTICS RECORD PER CAMERA
   * ------------------------------------------------
   *
   * Prevent duplicate CAM001/CAM002/CAM004 entries
   * when multiple analytics snapshots exist.
   */
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

  /*
   * Average speed across the latest snapshot
   * from each monitored camera.
   */
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

      <div className="p-6">

        {/* =========================
            OVERVIEW
        ========================= */}

        <div className="mb-8">
          <div className="flex flex-wrap items-center gap-3">

            <h1 className="text-2xl font-bold text-black">
              City Traffic Intelligence Dashboard
            </h1>

            <span className="flex items-center gap-1.5 rounded-full bg-green-100 px-2.5 py-1 text-xs font-medium text-green-700">
              <span className="h-2 w-2 animate-pulse rounded-full bg-green-500" />
              LIVE
            </span>

          </div>

          <p className="mt-2 text-sm text-slate-500">
            Real-time multi-camera ANPR, vehicle trajectory
            tracking and urban traffic analytics.
          </p>
        </div>

        {/* =========================
            DEMO ENVIRONMENT
        ========================= */}

        <DemoMode />

        {/* =========================
            MAIN STATISTICS
        ========================= */}

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">

          <StatCard
            title="Active Cameras"
            value={activeCameras}
            description="Connected city cameras"
          />

          <StatCard
            title="Detection Records"
            value={totalVehicles}
            description="Recorded vehicle detections"
          />

          <StatCard
            title="Valid ANPR Plates"
            value={validPlates}
            description="Validated ANPR detection records"
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
                Live GIS visualization of congestion,
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

          <DashboardCard title="Camera Network">

            <div className="space-y-3">

              {cameras.map((camera) => (

                <div
                  key={camera.camera_id}
                  className="flex items-center justify-between rounded-lg bg-slate-950 p-3"
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
                    {camera.is_active
                      ? "ONLINE"
                      : "OFFLINE"}
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
                  className="flex items-center justify-between rounded-lg bg-slate-950 p-3"
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
                      ? "VALID"
                      : "UNREADABLE"}
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