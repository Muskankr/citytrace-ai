"use client";

import dynamic from "next/dynamic";
import { useEffect, useMemo, useState } from "react";
import DashboardCard from "@/components/DashboardCard";
import {
  getTrajectories,
  getCameras,
} from "@/lib/api";

const TrajectoryMapClient = dynamic(
  () => import("@/components/TrajectoryMapClient"),
  {
    ssr: false,
    loading: () => (
      <div className="flex h-[450px] items-center justify-center rounded-lg bg-gray-100">
        <p className="text-sm text-gray-500">
          Loading GIS trajectory map...
        </p>
      </div>
    ),
  }
);

interface Trajectory {
  id: number;
  plate_number: string;
  track_id: number;
  start_camera_id: string | null;
  end_camera_id: string | null;
  start_time: string | null;
  end_time: string | null;
  route: string | null;
  distance_km: number | null;
  average_speed_kmh: number | null;
  direction: string | null;
  completed: boolean;
}

interface Camera {
  id: number;
  camera_id: string;
  name: string;
  latitude: number;
  longitude: number;
  road_name: string;
  direction: string;
  location?: string | null;
  is_active: boolean;
}

export default function TrajectoriesPage() {
  const [trajectories, setTrajectories] = useState<Trajectory[]>([]);
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<Trajectory | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [urlTrackId, setUrlTrackId] = useState<number | null>(null);

  /*
   * Get track_id from the URL.
   *
   * Example:
   * /trajectories?track_id=777
   */
  const getTrackIdFromUrl = () => {
    if (typeof window === "undefined") {
      return null;
    }

    const params = new URLSearchParams(
      window.location.search
    );

    const value = params.get("track_id");

    if (!value) {
      return null;
    }

    const trackId = Number(value);

    return Number.isFinite(trackId)
      ? trackId
      : null;
  };

  async function loadData() {
    try {
      setError("");

      const [trajectoryData, cameraData] =
        await Promise.all([
          getTrajectories(),
          getCameras(),
        ]);

      setTrajectories(trajectoryData);
      setCameras(cameraData);

      /*
       * If a track_id was supplied in the URL,
       * automatically select that trajectory.
       */
      const requestedTrackId =
        getTrackIdFromUrl();

      setSelected((current) => {
        if (requestedTrackId !== null) {
          const requestedTrajectory =
            trajectoryData.find(
              (trajectory: Trajectory) =>
                trajectory.track_id ===
                requestedTrackId
            );

          if (requestedTrajectory) {
            return requestedTrajectory;
          }
        }

        /*
         * Keep the currently selected trajectory
         * when the dashboard refreshes.
         */
        if (current) {
          const updatedSelected =
            trajectoryData.find(
              (trajectory: Trajectory) =>
                trajectory.id === current.id
            );

          return updatedSelected ?? current;
        }

        /*
         * Default to the first trajectory.
         */
        return trajectoryData.length > 0
          ? trajectoryData[0]
          : null;
      });
    } catch (err) {
      console.error(err);
      setError(
        "Unable to load trajectory data."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
  setUrlTrackId(getTrackIdFromUrl());

  loadData();

  const interval = setInterval(
    loadData,
    5000
  );

  return () =>
    clearInterval(interval);
}, []);

  /*
   * Search trajectories by:
   * - plate
   * - track ID
   * - camera
   * - route
   * - direction
   */
  const filteredTrajectories = useMemo(() => {
    const query =
      search.trim().toLowerCase();

    if (!query) {
      return trajectories;
    }

    return trajectories.filter(
      (trajectory) =>
        [
          trajectory.plate_number,
          trajectory.track_id.toString(),
          trajectory.start_camera_id,
          trajectory.end_camera_id,
          trajectory.route,
          trajectory.direction,
        ]
          .filter(Boolean)
          .some((value) =>
            String(value)
              .toLowerCase()
              .includes(query)
          )
    );
  }, [trajectories, search]);

  function formatTime(
    value: string | null
  ) {
    if (!value) {
      return "—";
    }

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
      return value;
    }

    return date.toLocaleString();
  }

  /*
   * Convert:
   *
   * CAM001 → CAM006 → CAM002
   *
   * into:
   *
   * ["CAM001", "CAM006", "CAM002"]
   */
  const selectedRouteIds = useMemo(() => {
    if (!selected?.route) {
      return [];
    }

    return selected.route
      .split("→")
      .map((cameraId) =>
        cameraId.trim()
      )
      .filter(Boolean);
  }, [selected]);

  /*
   * Find actual camera objects for the GIS map.
   */
  const selectedRouteCameras =
    useMemo(() => {
      if (
        selectedRouteIds.length === 0
      ) {
        return [];
      }

      return selectedRouteIds
        .map((cameraId) =>
          cameras.find(
            (camera) =>
              camera.camera_id ===
              cameraId
          )
        )
        .filter(
          (camera): camera is Camera =>
            Boolean(camera)
        );
    }, [
      selectedRouteIds,
      cameras,
    ]);

  /*
   * Route fallback helpers.
   *
   * Useful for demo trajectories such as:
   *
   * HR26AN7777
   * CAM001 → CAM006 → CAM002
   *
   * where start_camera_id and end_camera_id
   * are intentionally null.
   */
  const selectedStartCamera =
    selected?.start_camera_id ??
    selectedRouteIds[0] ??
    null;

  const selectedEndCamera =
    selected?.end_camera_id ??
    selectedRouteIds[
      selectedRouteIds.length - 1
    ] ??
    null;

  /*
   * Number of unique cameras represented
   * in the trajectory data.
   */
  const connectedCameraCount =
    useMemo(() => {
      const cameraIds =
        trajectories.flatMap(
          (trajectory) =>
            trajectory.route
              ? trajectory.route
                  .split("→")
                  .map((camera) =>
                    camera.trim()
                  )
                  .filter(Boolean)
              : []
        );

      return new Set(cameraIds).size;
    }, [trajectories]);

  return (
    <main className="min-h-screen bg-gray-50 p-8">

      {/* Header */}
      <div className="mb-8">
        <p className="text-sm font-medium uppercase tracking-wider text-blue-600">
          Multi-Camera Intelligence
        </p>

        <h1 className="mt-1 text-3xl font-bold text-gray-900">
          Vehicle Trajectories
        </h1>

        <p className="mt-2 text-gray-600">
          Track a vehicle across distributed city
          cameras and analyze its complete route.
        </p>
      </div>

      {/* Search */}
      <div className="mb-6 rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
        <label className="mb-2 block text-sm font-medium text-gray-700">
          Search vehicle / camera / route
        </label>

        <div className="flex gap-3">
          <input
            type="text"
            value={search}
            onChange={(e) =>
              setSearch(e.target.value)
            }
            placeholder="Example: HR26AB1234, Track 95, or CAM001"
            className="w-full rounded-lg border border-gray-300 px-4 py-3 text-gray-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
          />

          {search && (
            <button
              onClick={() =>
                setSearch("")
              }
              className="rounded-lg border border-gray-300 bg-white px-5 py-3 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Clear
            </button>
          )}
        </div>

        {/* URL-selected track indicator */}
        {urlTrackId !== null && (
  <div className="mt-3 rounded-lg border border-blue-100 bg-blue-50 px-4 py-3 text-sm text-blue-700">
    Showing trajectory for Track #
    {urlTrackId}
  </div>
)}
      </div>

      {/* Loading / Error */}
      {loading ? (
        <div className="rounded-xl border border-gray-200 bg-white p-10 text-center text-gray-600">
          Loading trajectory data...
        </div>
      ) : error ? (
        <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-red-700">
          {error}
        </div>
      ) : (
        <>
          {/* Summary */}
          <div className="mb-6 grid gap-5 md:grid-cols-3">

            <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
              <p className="text-sm text-gray-500">
                Total Trajectories
              </p>

              <p className="mt-2 text-3xl font-bold text-gray-900">
                {trajectories.length}
              </p>
            </div>

            <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
              <p className="text-sm text-gray-500">
                Completed Routes
              </p>

              <p className="mt-2 text-3xl font-bold text-gray-900">
                {
                  trajectories.filter(
                    (trajectory) =>
                      trajectory.completed
                  ).length
                }
              </p>
            </div>

            <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
              <p className="text-sm text-gray-500">
                Cameras Connected
              </p>

              <p className="mt-2 text-3xl font-bold text-gray-900">
                {connectedCameraCount}
              </p>
            </div>

          </div>

          {/* Main Layout */}
          <div className="grid gap-6 lg:grid-cols-5">

            {/* LEFT */}
            <div className="lg:col-span-2">
              <DashboardCard title="Detected Routes">

                {filteredTrajectories.length ===
                0 ? (
                  <div className="py-8 text-center text-gray-500">
                    No trajectories found.
                  </div>
                ) : (
                  <div className="space-y-3">

                    {filteredTrajectories.map(
                      (trajectory) => {
                        const isSelected =
                          selected?.id ===
                          trajectory.id;

                        return (
                          <button
                            key={
                              trajectory.id
                            }
                            onClick={() =>
                              setSelected(
                                trajectory
                              )
                            }
                            className={`w-full rounded-xl border p-4 text-left transition ${
                              isSelected
                                ? "border-blue-500 bg-blue-50"
                                : "border-gray-200 bg-white hover:border-blue-300 hover:bg-gray-50"
                            }`}
                          >

                            {/* Plate + Status */}
                            <div className="flex items-center justify-between">

                              <span className="font-bold text-gray-900">
                                {
                                  trajectory.plate_number
                                }
                              </span>

                              <span
                                className={`rounded-full px-2.5 py-1 text-xs font-medium ${
                                  trajectory.completed
                                    ? "bg-green-100 text-green-700"
                                    : "bg-yellow-100 text-yellow-700"
                                }`}
                              >
                                {trajectory.completed
                                  ? "Completed"
                                  : "Active"}
                              </span>

                            </div>

                            {/* FULL ROUTE */}
                            <div className="mt-3 rounded-lg bg-gray-50 px-3 py-2">

                              <p className="text-xs font-medium uppercase tracking-wide text-gray-400">
                                Camera Route
                              </p>

                              <p className="mt-1 text-sm font-semibold text-gray-700">
                                {trajectory.route ??
                                  "Route unavailable"}
                              </p>

                            </div>

                            {/* Track */}
                            <div className="mt-3 text-xs text-gray-500">
                              Track ID:{" "}
                              <span className="font-semibold text-gray-700">
                                #
                                {
                                  trajectory.track_id
                                }
                              </span>
                            </div>

                          </button>
                        );
                      }
                    )}

                  </div>
                )}

              </DashboardCard>
            </div>

            {/* RIGHT */}
            <div className="lg:col-span-3">
              <DashboardCard title="Trajectory Details">

                {!selected ? (
                  <div className="py-12 text-center text-gray-500">
                    Select a vehicle route to view
                    details.
                  </div>
                ) : (
                  <div>

                    {/* Plate */}
                    <div className="mb-6 flex items-center justify-between">

                      <div>
                        <p className="text-sm text-gray-500">
                          Vehicle Plate
                        </p>

                        <h2 className="mt-1 text-3xl font-bold tracking-wider text-gray-900">
                          {
                            selected.plate_number
                          }
                        </h2>
                      </div>

                      <div
                        className={`rounded-lg px-4 py-2 text-sm font-semibold ${
                          selected.completed
                            ? "bg-green-100 text-green-700"
                            : "bg-yellow-100 text-yellow-700"
                        }`}
                      >
                        {selected.completed
                          ? "Route Completed"
                          : "Currently Tracked"}
                      </div>

                    </div>

                    {/* Route */}
                    <div className="rounded-xl border border-gray-200 bg-gray-50 p-5">

                      <p className="mb-4 text-sm font-semibold text-gray-700">
                        Camera Route
                      </p>

                      {selectedRouteIds.length >
                      0 ? (
                        <div className="flex flex-wrap items-center gap-3">

                          {selectedRouteIds.map(
                            (
                              camera,
                              index
                            ) => (
                              <div
                                key={`${camera}-${index}`}
                                className="flex items-center gap-3"
                              >

                                <div className="rounded-lg border border-blue-200 bg-white px-4 py-3 shadow-sm">

                                  <p className="text-xs text-gray-500">
                                    Camera
                                  </p>

                                  <p className="font-bold text-blue-700">
                                    {camera}
                                  </p>

                                </div>

                                {index <
                                  selectedRouteIds.length -
                                    1 && (
                                  <span className="text-xl font-bold text-blue-500">
                                    →
                                  </span>
                                )}

                              </div>
                            )
                          )}

                        </div>
                      ) : (
                        <p className="text-sm text-gray-500">
                          Route unavailable.
                        </p>
                      )}

                    </div>

                    {/* Metrics */}
                    <div className="mt-5 grid gap-4 sm:grid-cols-2">

                      <div className="rounded-lg border border-gray-200 bg-white p-4">
                        <p className="text-sm text-gray-500">
                          Distance
                        </p>

                        <p className="mt-1 text-xl font-bold text-gray-900">
                          {selected.distance_km !==
                          null
                            ? selected.distance_km.toFixed(
                                2
                              )
                            : "—"}{" "}
                          km
                        </p>
                      </div>

                      <div className="rounded-lg border border-gray-200 bg-white p-4">
                        <p className="text-sm text-gray-500">
                          Average Speed
                        </p>

                        <p className="mt-1 text-xl font-bold text-gray-900">
                          {selected.average_speed_kmh !==
                          null
                            ? selected.average_speed_kmh.toFixed(
                                2
                              )
                            : "—"}{" "}
                          km/h
                        </p>
                      </div>

                      <div className="rounded-lg border border-gray-200 bg-white p-4">
                        <p className="text-sm text-gray-500">
                          Direction
                        </p>

                        <p className="mt-1 text-xl font-bold text-gray-900">
                          {selected.direction ??
                            "—"}
                        </p>
                      </div>

                      <div className="rounded-lg border border-gray-200 bg-white p-4">
                        <p className="text-sm text-gray-500">
                          Track ID
                        </p>

                        <p className="mt-1 text-xl font-bold text-gray-900">
                          #
                          {
                            selected.track_id
                          }
                        </p>
                      </div>

                    </div>

                    {/* GIS MAP */}
                    <div className="mt-6 rounded-xl border border-gray-200 bg-white p-5">

                      <div className="mb-4">
                        <h3 className="text-lg font-semibold text-gray-900">
                          GIS Trajectory Map
                        </h3>

                        <p className="mt-1 text-sm text-gray-500">
                          Camera-to-camera vehicle route
                          visualization
                        </p>
                      </div>

                      {selectedRouteCameras.length >
                      0 ? (
                        <TrajectoryMapClient
                          cameras={
                            selectedRouteCameras
                          }
                        />
                      ) : (
                        <div className="flex h-[450px] items-center justify-center rounded-lg bg-gray-100">

                          <div className="text-center">
                            <p className="font-medium text-gray-700">
                              Camera coordinates unavailable
                            </p>

                            <p className="mt-1 text-sm text-gray-500">
                              No matching camera locations
                              found for this route.
                            </p>
                          </div>

                        </div>
                      )}

                    </div>

                    {/* Timeline */}
                    <div className="mt-6">

                      <p className="mb-4 text-sm font-semibold text-gray-700">
                        Journey Timeline
                      </p>

                      <div className="relative ml-3 border-l-2 border-blue-200 pl-6">

                        {/* START */}
                        <div className="relative mb-6">

                          <span className="absolute -left-[34px] top-1 h-4 w-4 rounded-full border-4 border-white bg-blue-500" />

                          <p className="font-semibold text-gray-900">
                            Journey Started
                          </p>

                          <p className="text-sm text-gray-500">
                            {selectedStartCamera ??
                              "Camera unavailable"}
                          </p>

                          <p className="mt-1 text-xs text-gray-400">
                            {formatTime(
                              selected.start_time
                            )}
                          </p>

                        </div>

                        {/* END */}
                        <div className="relative">

                          <span className="absolute -left-[34px] top-1 h-4 w-4 rounded-full border-4 border-white bg-green-500" />

                          <p className="font-semibold text-gray-900">
                            Journey Ended
                          </p>

                          <p className="text-sm text-gray-500">
                            {selectedEndCamera ??
                              "Camera unavailable"}
                          </p>

                          <p className="mt-1 text-xs text-gray-400">
                            {formatTime(
                              selected.end_time
                            )}
                          </p>

                        </div>

                      </div>
                    </div>

                  </div>
                )}

              </DashboardCard>
            </div>

          </div>
        </>
      )}
    </main>
  );
}