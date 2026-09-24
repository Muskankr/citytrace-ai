"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  getDetections,
  getTrajectories,
} from "@/lib/api";

type Detection = {
  id: number;
  track_id: number;
  vehicle_type: string;
  plate_number: string | null;
  ocr_confidence: number | null;
  plate_valid: boolean;
  plate_status: string | null;
  camera_id: string;
  latitude: number | null;
  longitude: number | null;
  direction: string | null;
  timestamp: string | null;
  frame_number: number | null;
  vehicle_confidence: number | null;
  plate_detection_confidence: number | null;
};

type Trajectory = {
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
};

export default function DetectionsPage() {
  const router = useRouter();

  const [detections, setDetections] = useState<Detection[]>([]);
  const [trajectories, setTrajectories] = useState<Trajectory[]>([]);

  const [search, setSearch] = useState("");
  const [camera, setCamera] = useState("ALL");
  const [status, setStatus] = useState("ALL");
  const [vehicleType, setVehicleType] = useState("ALL");

  const [loading, setLoading] = useState(true);

  // Selected detection for investigation drawer
  const [selectedDetection, setSelectedDetection] =
    useState<Detection | null>(null);

  async function loadData() {
    try {
      const [detectionData, trajectoryData] =
        await Promise.all([
          getDetections(),
          getTrajectories(),
        ]);

      setDetections(detectionData);
      setTrajectories(trajectoryData);
    } catch (error) {
      console.error(
        "Failed to load detection/trajectory data:",
        error
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();

    const interval = setInterval(
      loadData,
      5000
    );

    return () => clearInterval(interval);
  }, []);

  const cameras = useMemo(
    () =>
      Array.from(
        new Set(
          detections
            .map((d) => d.camera_id)
            .filter(Boolean)
        )
      ),
    [detections]
  );

  const filteredDetections = useMemo(() => {
    return detections.filter((detection) => {
      const searchValue =
        search.toLowerCase().trim();

      const matchesSearch =
        !searchValue ||
        detection.plate_number
          ?.toLowerCase()
          .includes(searchValue) ||
        detection.track_id
          .toString()
          .includes(searchValue);

      const matchesCamera =
        camera === "ALL" ||
        detection.camera_id === camera;

      const matchesStatus =
        status === "ALL" ||
        detection.plate_status?.toUpperCase() ===
          status;

      const matchesVehicle =
        vehicleType === "ALL" ||
        detection.vehicle_type?.toLowerCase() ===
          vehicleType.toLowerCase();

      return (
        matchesSearch &&
        matchesCamera &&
        matchesStatus &&
        matchesVehicle
      );
    });
  }, [
    detections,
    search,
    camera,
    status,
    vehicleType,
  ]);

  function confidence(
    value: number | null
  ) {
    if (
      value === null ||
      value === undefined
    ) {
      return "—";
    }

    return `${Math.round(value * 100)}%`;
  }

  function statusStyle(
    value: string | null
  ) {
    switch (value?.toUpperCase()) {
      case "VALID":
        return "bg-green-100 text-green-700";

      case "HIGH CONFIDENCE":
        return "bg-green-100 text-green-700";

      case "POSSIBLE":
        return "bg-yellow-100 text-yellow-700";

      case "UNREADABLE":
        return "bg-red-100 text-red-700";

      default:
        return "bg-gray-100 text-gray-600";
    }
  }

  /*
   * Check whether a trajectory exists for
   * the selected detection's Track ID.
   */
  const selectedTrajectory = useMemo(() => {
    if (!selectedDetection) {
      return null;
    }

    return (
      trajectories.find(
        (trajectory) =>
          trajectory.track_id ===
          selectedDetection.track_id
      ) ?? null
    );
  }, [
    selectedDetection,
    trajectories,
  ]);

  function openTrajectory() {
    if (!selectedDetection) {
      return;
    }

    const trackId =
      selectedDetection.track_id;

    router.push(
      `/trajectories?track_id=${encodeURIComponent(
        trackId
      )}`
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">

      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3">
          <h1 className="text-3xl font-bold text-gray-900">
            ANPR Detections
          </h1>

          <span className="rounded-full bg-blue-100 px-3 py-1 text-xs font-semibold text-blue-700">
            REPLAY DATA
          </span>
        </div>

        <p className="mt-1 text-xs text-gray-400">
          VALID indicates that the recognized plate
          matches the configured format validation rules.
          Recognition accuracy is evaluated separately
          against manually verified ground truth.
        </p>
      </div>

      {/* Filters */}
      <div className="mb-6 rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
        <div className="grid gap-4 md:grid-cols-4">

          {/* Search */}
          <div>
            <label className="mb-2 block text-xs font-semibold uppercase tracking-wide text-gray-700">
              Search Plate / Track ID
            </label>

            <div className="relative">
              <span className="pointer-events-none absolute left-3 top-2.5 text-gray-500">
                🔎
              </span>

              <input
                type="text"
                placeholder="HR26AB1234..."
                value={search}
                onChange={(e) =>
                  setSearch(e.target.value)
                }
                className="w-full rounded-lg border border-gray-200 bg-gray-50 py-2 pl-9 pr-3 text-sm text-gray-900 outline-none transition placeholder:text-gray-500 focus:border-gray-400 focus:bg-white"
              />
            </div>
          </div>

          {/* Camera */}
          <div>
            <label className="mb-2 block text-xs font-semibold uppercase tracking-wide text-gray-700">
              Camera
            </label>

            <select
              value={camera}
              onChange={(e) =>
                setCamera(e.target.value)
              }
              className="w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-gray-900 outline-none focus:border-gray-400"
            >
              <option value="ALL">
                All Cameras
              </option>

              {cameras.map((cam) => (
                <option
                  key={cam}
                  value={cam}
                >
                  {cam}
                </option>
              ))}
            </select>
          </div>

          {/* Status */}
          <div>
            <label className="mb-2 block text-xs font-semibold uppercase tracking-wide text-gray-700">
              Plate Status
            </label>

            <select
              value={status}
              onChange={(e) =>
                setStatus(e.target.value)
              }
              className="w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-gray-900 outline-none focus:border-gray-400"
            >
              <option value="ALL">
                All Statuses
              </option>
              <option value="VALID">
                Valid
              </option>
              <option value="POSSIBLE">
                Possible
              </option>
              <option value="UNREADABLE">
                Unreadable
              </option>
            </select>
          </div>

          {/* Vehicle */}
          <div>
            <label className="mb-2 block text-xs font-semibold uppercase tracking-wide text-gray-700">
              Vehicle Type
            </label>

            <select
              value={vehicleType}
              onChange={(e) =>
                setVehicleType(e.target.value)
              }
              className="w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-gray-900 outline-none focus:border-gray-400"
            >
              <option value="ALL">
                All Vehicles
              </option>
              <option value="car">
                Car
              </option>
              <option value="motorcycle">
                Motorcycle
              </option>
              <option value="bus">
                Bus
              </option>
              <option value="truck">
                Truck
              </option>
            </select>
          </div>
        </div>

        {/* Result count */}
        <div className="mt-4 flex items-center justify-between border-t border-gray-100 pt-4">
          <p className="text-sm text-gray-500">
            Showing{" "}
            <span className="font-semibold text-gray-900">
              {filteredDetections.length}
            </span>{" "}
            of{" "}
            <span className="font-semibold text-gray-900">
              {detections.length}
            </span>{" "}
            detections
          </p>

          <button
            onClick={() => {
              setSearch("");
              setCamera("ALL");
              setStatus("ALL");
              setVehicleType("ALL");
            }}
            className="text-sm font-medium text-gray-500 transition hover:text-gray-900"
          >
            Clear filters
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
        {loading ? (
          <div className="flex h-48 items-center justify-center">
            <div className="text-sm text-gray-500">
              Loading detections...
            </div>
          </div>
        ) : filteredDetections.length === 0 ? (
          <div className="flex h-48 flex-col items-center justify-center">
            <div className="mb-2 text-3xl">
              🔍
            </div>

            <p className="font-medium text-gray-900">
              No detections found
            </p>

            <p className="mt-1 text-sm text-gray-500">
              Try changing your filters or search term.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead className="border-b border-gray-200 bg-gray-50">
                <tr>
                  <th className="px-5 py-4 text-xs font-semibold uppercase tracking-wide text-gray-500">
                    Plate
                  </th>

                  <th className="px-5 py-4 text-xs font-semibold uppercase tracking-wide text-gray-500">
                    Camera
                  </th>

                  <th className="px-5 py-4 text-xs font-semibold uppercase tracking-wide text-gray-500">
                    Vehicle
                  </th>

                  <th className="px-5 py-4 text-xs font-semibold uppercase tracking-wide text-gray-500">
                    Track ID
                  </th>

                  <th className="px-5 py-4 text-xs font-semibold uppercase tracking-wide text-gray-500">
                    OCR
                  </th>

                  <th className="px-5 py-4 text-xs font-semibold uppercase tracking-wide text-gray-500">
                    Status
                  </th>

                  <th className="px-5 py-4 text-xs font-semibold uppercase tracking-wide text-gray-500">
                    Direction
                  </th>
                </tr>
              </thead>

              <tbody className="divide-y divide-gray-100">
                {filteredDetections.map(
                  (detection) => (
                    <tr
                      key={detection.id}
                      onClick={() =>
                        setSelectedDetection(
                          detection
                        )
                      }
                      className="cursor-pointer transition hover:bg-gray-50"
                    >
                      <td className="px-5 py-4">
                        <span className="font-mono text-sm font-semibold text-gray-900">
                          {detection.plate_number ||
                            "UNKNOWN"}
                        </span>
                      </td>

                      <td className="px-5 py-4">
                        <span className="rounded-md bg-gray-100 px-2 py-1 text-xs font-medium text-gray-700">
                          {detection.camera_id}
                        </span>
                      </td>

                      <td className="px-5 py-4 text-sm capitalize text-gray-700">
                        {detection.vehicle_type ||
                          "—"}
                      </td>

                      <td className="px-5 py-4 text-sm text-gray-600">
                        #{detection.track_id}
                      </td>

                      <td className="px-5 py-4 text-sm font-medium text-gray-700">
                        {confidence(
                          detection.ocr_confidence
                        )}
                      </td>

                      <td className="px-5 py-4">
                        <span
                          className={`rounded-full px-2.5 py-1 text-xs font-semibold ${statusStyle(
                            detection.plate_status
                          )}`}
                        >
                          {detection.plate_status ||
                            "UNKNOWN"}
                        </span>
                      </td>

                      <td className="px-5 py-4 text-sm text-gray-600">
                        {detection.direction ||
                          "—"}
                      </td>
                    </tr>
                  )
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ========================================================= */}
      {/* Detection Details Drawer */}
      {/* ========================================================= */}

      {selectedDetection && (
        <div className="fixed inset-0 z-50 flex justify-end">

          {/* Backdrop */}
          <button
            type="button"
            aria-label="Close detection details"
            onClick={() =>
              setSelectedDetection(null)
            }
            className="absolute inset-0 cursor-default bg-black/30"
          />

          {/* Drawer */}
          <div className="relative h-full w-full max-w-md overflow-y-auto bg-white p-6 shadow-2xl">

            {/* Drawer Header */}
            <div className="mb-6 flex items-start justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">
                  Detection Details
                </p>

                <h2 className="mt-1 font-mono text-2xl font-bold text-gray-900">
                  {selectedDetection.plate_number ||
                    "UNKNOWN"}
                </h2>

                <p className="mt-1 text-sm text-gray-500">
                  Track #{selectedDetection.track_id}
                </p>
              </div>

              <button
                type="button"
                onClick={() =>
                  setSelectedDetection(null)
                }
                className="rounded-lg px-3 py-2 text-2xl leading-none text-gray-400 transition hover:bg-gray-100 hover:text-gray-700"
                aria-label="Close"
              >
                ×
              </button>
            </div>

            {/* Recognition */}
            <div className="mb-6 rounded-xl border border-gray-200 bg-gray-50 p-4">
              <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-gray-500">
                Recognition
              </p>

              <div className="grid grid-cols-2 gap-4">

                <div>
                  <p className="text-xs text-gray-500">
                    OCR Confidence
                  </p>

                  <p className="mt-1 text-lg font-semibold text-gray-900">
                    {confidence(
                      selectedDetection.ocr_confidence
                    )}
                  </p>
                </div>

                <div>
                  <p className="text-xs text-gray-500">
                    Plate Detection
                  </p>

                  <p className="mt-1 text-lg font-semibold text-gray-900">
                    {confidence(
                      selectedDetection.plate_detection_confidence
                    )}
                  </p>
                </div>

                <div>
                  <p className="text-xs text-gray-500">
                    Vehicle Detection
                  </p>

                  <p className="mt-1 text-lg font-semibold text-gray-900">
                    {confidence(
                      selectedDetection.vehicle_confidence
                    )}
                  </p>
                </div>

                <div>
                  <p className="text-xs text-gray-500">
                    Plate Status
                  </p>

                  <span
                    className={`mt-1 inline-block rounded-full px-2.5 py-1 text-xs font-semibold ${statusStyle(
                      selectedDetection.plate_status
                    )}`}
                  >
                    {selectedDetection.plate_status ||
                      "UNKNOWN"}
                  </span>
                </div>
              </div>
            </div>

            {/* Detection Information */}
            <div className="mb-6">
              <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-gray-500">
                Detection Information
              </p>

              <div className="divide-y divide-gray-100 rounded-xl border border-gray-200">

                <div className="flex justify-between px-4 py-3">
                  <span className="text-sm text-gray-500">
                    Camera
                  </span>

                  <span className="text-sm font-semibold text-gray-900">
                    {selectedDetection.camera_id}
                  </span>
                </div>

                <div className="flex justify-between px-4 py-3">
                  <span className="text-sm text-gray-500">
                    Vehicle
                  </span>

                  <span className="text-sm font-semibold capitalize text-gray-900">
                    {selectedDetection.vehicle_type ||
                      "—"}
                  </span>
                </div>

                <div className="flex justify-between px-4 py-3">
                  <span className="text-sm text-gray-500">
                    Track ID
                  </span>

                  <span className="text-sm font-semibold text-gray-900">
                    #{selectedDetection.track_id}
                  </span>
                </div>

                <div className="flex justify-between px-4 py-3">
                  <span className="text-sm text-gray-500">
                    Direction
                  </span>

                  <span className="text-sm font-semibold text-gray-900">
                    {selectedDetection.direction ||
                      "—"}
                  </span>
                </div>

                <div className="flex justify-between px-4 py-3">
                  <span className="text-sm text-gray-500">
                    Frame
                  </span>

                  <span className="text-sm font-semibold text-gray-900">
                    {selectedDetection.frame_number ??
                      "—"}
                  </span>
                </div>

                <div className="flex justify-between gap-4 px-4 py-3">
                  <span className="text-sm text-gray-500">
                    Timestamp
                  </span>

                  <span className="text-right text-sm font-semibold text-gray-900">
                    {selectedDetection.timestamp
                      ? new Date(
                          selectedDetection.timestamp
                        ).toLocaleString()
                      : "—"}
                  </span>
                </div>
              </div>
            </div>

            {/* Location */}
            <div>
              <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-gray-500">
                Location
              </p>

              <div className="rounded-xl border border-gray-200 bg-gray-50 p-4">
                <p className="text-sm text-gray-500">
                  Coordinates
                </p>

                <p className="mt-1 font-mono text-sm font-semibold text-gray-900">
                  {selectedDetection.latitude !==
                    null &&
                  selectedDetection.longitude !==
                    null
                    ? `${selectedDetection.latitude.toFixed(
                        6
                      )}, ${selectedDetection.longitude.toFixed(
                        6
                      )}`
                    : "Location unavailable"}
                </p>
              </div>
            </div>

            {/* ================================================= */}
            {/* Trajectory Investigation */}
            {/* ================================================= */}
            <div className="mt-6 rounded-xl border border-gray-200 bg-white p-4">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">
                    Vehicle Trajectory
                  </p>

                  <p className="mt-1 text-sm font-semibold text-gray-900">
                    Track #{selectedDetection.track_id}
                  </p>

                  <p className="mt-1 text-xs leading-5 text-gray-500">
                    Follow this vehicle across the
                    multi-camera network and inspect
                    its complete route.
                  </p>
                </div>

                {selectedTrajectory && (
                  <span className="shrink-0 rounded-full bg-green-100 px-2.5 py-1 text-xs font-semibold text-green-700">
                    AVAILABLE
                  </span>
                )}
              </div>

              {selectedTrajectory ? (
                <div className="mt-4">

                  {/* Route preview */}
                  {selectedTrajectory.route && (
                    <div className="mb-3 rounded-lg bg-gray-50 p-3">
                      <p className="text-xs text-gray-500">
                        Route
                      </p>

                      <p className="mt-1 text-sm font-semibold text-gray-900">
                        {selectedTrajectory.route}
                      </p>
                    </div>
                  )}

                  {/* View button */}
                  <button
                    type="button"
                    onClick={openTrajectory}
                    className="w-full rounded-lg bg-gray-900 px-4 py-3 text-sm font-semibold text-white transition hover:bg-gray-800"
                  >
                    View Full Trajectory →
                  </button>
                </div>
              ) : (
                <div className="mt-4 rounded-lg border border-gray-200 bg-gray-50 p-3">
                  <p className="text-sm font-medium text-gray-700">
                    No trajectory currently available
                  </p>

                  <p className="mt-1 text-xs leading-5 text-gray-500">
                    This track has a detection record,
                    but a completed multi-camera
                    trajectory has not been created for
                    it yet.
                  </p>
                </div>
              )}
            </div>

            {/* Validation Note */}
            <div className="mt-6 rounded-xl border border-blue-100 bg-blue-50 p-4">
              <p className="text-xs font-semibold text-blue-800">
                Validation note
              </p>

              <p className="mt-1 text-xs leading-5 text-blue-700">
                VALID indicates that the recognized
                plate matches the configured format
                validation rules. It does not by itself
                establish ground-truth recognition
                accuracy.
              </p>
            </div>

          </div>
        </div>
      )}
    </div>
  );
}