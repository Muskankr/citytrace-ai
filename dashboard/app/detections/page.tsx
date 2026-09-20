"use client";

import { useEffect, useMemo, useState } from "react";
import { getDetections } from "@/lib/api";

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

export default function DetectionsPage() {
  const [detections, setDetections] = useState<Detection[]>([]);
  const [search, setSearch] = useState("");
  const [camera, setCamera] = useState("ALL");
  const [status, setStatus] = useState("ALL");
  const [vehicleType, setVehicleType] = useState("ALL");
  const [loading, setLoading] = useState(true);

  async function loadDetections() {
    try {
      const data = await getDetections();
      setDetections(data);
    } catch (error) {
      console.error("Failed to load detections:", error);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDetections();

    const interval = setInterval(loadDetections, 5000);

    return () => clearInterval(interval);
  }, []);

  const cameras = useMemo(
    () =>
      Array.from(
        new Set(detections.map((d) => d.camera_id).filter(Boolean))
      ),
    [detections]
  );

  const filteredDetections = useMemo(() => {
    return detections.filter((detection) => {
      const searchValue = search.toLowerCase().trim();

      const matchesSearch =
        !searchValue ||
        detection.plate_number
          ?.toLowerCase()
          .includes(searchValue) ||
        detection.track_id.toString().includes(searchValue);

      const matchesCamera =
        camera === "ALL" || detection.camera_id === camera;

      const matchesStatus =
        status === "ALL" ||
        detection.plate_status?.toUpperCase() === status;

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
  }, [detections, search, camera, status, vehicleType]);

  function confidence(value: number | null) {
    if (value === null || value === undefined) return "—";
    return `${Math.round(value * 100)}%`;
  }

  function statusStyle(status: string | null) {
    switch (status?.toUpperCase()) {
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

  return (
    <div className="min-h-screen bg-gray-50 p-8">

      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3">

          <h1 className="text-3xl font-bold text-gray-900">
            Live Detections
          </h1>

          <span className="flex items-center gap-1.5 rounded-full bg-green-100 px-3 py-1 text-xs font-semibold text-green-700">
            <span className="h-2 w-2 animate-pulse rounded-full bg-green-500" />
            LIVE
          </span>

        </div>

        <p className="mt-2 text-sm text-gray-500">
          Search and investigate vehicle detections across city cameras.
        </p>
      </div>

      {/* Filters */}
      <div className="mb-6 rounded-xl border border-gray-200 bg-white p-5 shadow-sm">

        <div className="grid gap-4 md:grid-cols-4">

          {/* Search */}
          <div className="md:col-span-1">

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
                onChange={(e) => setSearch(e.target.value)}
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
              onChange={(e) => setCamera(e.target.value)}
              className="w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-gray-900 outline-none focus:border-gray-400"
            >
              <option value="ALL">All Cameras</option>

              {cameras.map((cam) => (
                <option key={cam} value={cam}>
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
              onChange={(e) => setStatus(e.target.value)}
              className="w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-gray-900 outline-none focus:border-gray-400"
            >
              <option value="ALL">All Statuses</option>
              <option value="VALID">Valid</option>
              <option value="POSSIBLE">Possible</option>
              <option value="UNREADABLE">Unreadable</option>
            </select>

          </div>

          {/* Vehicle */}
          <div>

            <label className="mb-2 block text-xs font-semibold uppercase tracking-wide text-gray-700">
              Vehicle Type
            </label>

            <select
              value={vehicleType}
              onChange={(e) => setVehicleType(e.target.value)}
              className="w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-gray-900 outline-none focus:border-gray-400"
            >
              <option value="ALL">All Vehicles</option>
              <option value="car">Car</option>
              <option value="motorcycle">Motorcycle</option>
              <option value="bus">Bus</option>
              <option value="truck">Truck</option>
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

                {filteredDetections.map((detection) => (

                  <tr
                    key={detection.id}
                    className="transition hover:bg-gray-50"
                  >

                    {/* Plate */}
                    <td className="px-5 py-4">

                      <span className="font-mono text-sm font-semibold text-gray-900">
                        {detection.plate_number || "UNKNOWN"}
                      </span>

                    </td>

                    {/* Camera */}
                    <td className="px-5 py-4">

                      <span className="rounded-md bg-gray-100 px-2 py-1 text-xs font-medium text-gray-700">
                        {detection.camera_id}
                      </span>

                    </td>

                    {/* Vehicle */}
                    <td className="px-5 py-4 text-sm capitalize text-gray-700">
                      {detection.vehicle_type || "—"}
                    </td>

                    {/* Track ID */}
                    <td className="px-5 py-4 text-sm text-gray-600">
                      #{detection.track_id}
                    </td>

                    {/* OCR */}
                    <td className="px-5 py-4 text-sm font-medium text-gray-700">
                      {confidence(detection.ocr_confidence)}
                    </td>

                    {/* Status */}
                    <td className="px-5 py-4">

                      <span
                        className={`rounded-full px-2.5 py-1 text-xs font-semibold ${statusStyle(
                          detection.plate_status
                        )}`}
                      >
                        {detection.plate_status || "UNKNOWN"}
                      </span>

                    </td>

                    {/* Direction */}
                    <td className="px-5 py-4 text-sm text-gray-600">
                      {detection.direction || "—"}
                    </td>

                  </tr>

                ))}

              </tbody>

            </table>

          </div>

        )}

      </div>

    </div>
  );
}