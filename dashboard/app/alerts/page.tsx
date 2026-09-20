"use client";

import { useEffect, useMemo, useState } from "react";
import { getAlerts } from "@/lib/api";

interface Alert {
  id: number;
  plate_number: string | null;
  camera_id: string | null;
  timestamp: string;
  alert_type: string;
  severity: string;
  message: string;
  latitude: number | null;
  longitude: number | null;
  is_resolved: boolean;
}

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  const [search, setSearch] =
    useState("");

  const [severityFilter, setSeverityFilter] =
    useState("ALL");

  const [statusFilter, setStatusFilter] =
    useState("ACTIVE");

  async function loadAlerts() {
    try {
      setError("");

      const data = await getAlerts();

      setAlerts(data);
    } catch (error) {
      console.error(
        "Alerts API Error:",
        error
      );

      setError(
        "Unable to load security alerts."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAlerts();

    const interval = setInterval(
      loadAlerts,
      5000
    );

    return () =>
      clearInterval(interval);
  }, []);

  /* =========================
     SUMMARY
  ========================= */

  const activeAlerts = alerts.filter(
    (alert) => !alert.is_resolved
  );

  const resolvedAlerts = alerts.filter(
    (alert) => alert.is_resolved
  );

  const highAlerts = activeAlerts.filter(
    (alert) =>
      alert.severity?.toUpperCase() ===
      "HIGH"
  );

  const mediumAlerts = activeAlerts.filter(
    (alert) =>
      alert.severity?.toUpperCase() ===
      "MEDIUM"
  );

  /* =========================
     FILTERED ALERTS
  ========================= */

  const filteredAlerts = useMemo(() => {
    const query =
      search.trim().toLowerCase();

    return alerts.filter((alert) => {
      const matchesSearch =
        !query ||
        [
          alert.plate_number,
          alert.camera_id,
          alert.alert_type,
          alert.severity,
          alert.message,
        ]
          .filter(Boolean)
          .some((value) =>
            String(value)
              .toLowerCase()
              .includes(query)
          );

      const matchesSeverity =
        severityFilter === "ALL" ||
        alert.severity?.toUpperCase() ===
          severityFilter;

      const matchesStatus =
        statusFilter === "ALL" ||
        (statusFilter === "ACTIVE" &&
          !alert.is_resolved) ||
        (statusFilter === "RESOLVED" &&
          alert.is_resolved);

      return (
        matchesSearch &&
        matchesSeverity &&
        matchesStatus
      );
    });
  }, [
    alerts,
    search,
    severityFilter,
    statusFilter,
  ]);

  /* =========================
     HELPERS
  ========================= */

  function getSeverityStyle(
    severity: string
  ) {
    const value =
      severity?.toUpperCase();

    if (value === "CRITICAL") {
      return "bg-red-100 text-red-700 border-red-200";
    }

    if (value === "HIGH") {
      return "bg-orange-100 text-orange-700 border-orange-200";
    }

    if (value === "MEDIUM") {
      return "bg-yellow-100 text-yellow-700 border-yellow-200";
    }

    if (value === "LOW") {
      return "bg-blue-100 text-blue-700 border-blue-200";
    }

    return "bg-gray-100 text-gray-700 border-gray-200";
  }

  function formatAlertType(
    alertType: string
  ) {
    if (!alertType) {
      return "Unknown Alert";
    }

    return alertType
      .replaceAll("_", " ")
      .replace(/\b\w/g, (char) =>
        char.toUpperCase()
      );
  }

  function formatTime(
    timestamp: string
  ) {
    if (!timestamp) {
      return "N/A";
    }

    const date =
      new Date(timestamp);

    if (
      Number.isNaN(
        date.getTime()
      )
    ) {
      return timestamp;
    }

    return date.toLocaleString();
  }

  /* =========================
     UI
  ========================= */

  return (
    <main className="min-h-screen bg-gray-50 p-6 md:p-8">

      {/* HEADER */}

      <div className="mb-8">

        <p className="text-sm font-medium uppercase tracking-wider text-red-600">
          Security & Intelligence
        </p>

        <h1 className="mt-1 text-3xl font-bold text-gray-900">
          Alert Intelligence
        </h1>

        <p className="mt-2 text-gray-600">
          Monitor blacklisted vehicles,
          suspicious activity and
          route intelligence alerts
          across the camera network.
        </p>

      </div>


      {/* ERROR */}

      {error && (
        <div className="mb-6 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}


      {/* SUMMARY CARDS */}

      <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">

        {/* TOTAL */}

        <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">

          <p className="text-sm text-gray-500">
            Total Alerts
          </p>

          <p className="mt-2 text-3xl font-bold text-gray-900">
            {alerts.length}
          </p>

          <p className="mt-2 text-xs text-gray-400">
            All recorded alerts
          </p>

        </div>


        {/* ACTIVE */}

        <div className="rounded-xl border border-red-200 bg-red-50 p-5 shadow-sm">

          <p className="text-sm text-red-600">
            Active Alerts
          </p>

          <p className="mt-2 text-3xl font-bold text-red-700">
            {activeAlerts.length}
          </p>

          <p className="mt-2 text-xs text-red-500">
            Requiring attention
          </p>

        </div>


        {/* HIGH */}

        <div className="rounded-xl border border-orange-200 bg-orange-50 p-5 shadow-sm">

          <p className="text-sm text-orange-600">
            High Severity
          </p>

          <p className="mt-2 text-3xl font-bold text-orange-700">
            {highAlerts.length}
          </p>

          <p className="mt-2 text-xs text-orange-600">
            Immediate attention
          </p>

        </div>


        {/* RESOLVED */}

        <div className="rounded-xl border border-green-200 bg-green-50 p-5 shadow-sm">

          <p className="text-sm text-green-600">
            Resolved Alerts
          </p>

          <p className="mt-2 text-3xl font-bold text-green-700">
            {resolvedAlerts.length}
          </p>

          <p className="mt-2 text-xs text-green-600">
            Successfully handled
          </p>

        </div>

      </div>


      {/* FILTER PANEL */}

      <div className="mb-6 rounded-xl border border-gray-200 bg-white p-5 shadow-sm">

        <div className="grid gap-4 md:grid-cols-3">

          {/* SEARCH */}

          <div>

            <label className="mb-2 block text-sm font-medium text-gray-700">
              Search Alerts
            </label>

            <input
              type="text"
              value={search}
              onChange={(e) =>
                setSearch(
                  e.target.value
                )
              }
              placeholder="Plate, camera or alert..."
              className="w-full rounded-lg border border-gray-300 px-4 py-3 text-gray-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            />

          </div>


          {/* SEVERITY */}

          <div>

            <label className="mb-2 block text-sm font-medium text-gray-700">
              Severity
            </label>

            <select
              value={severityFilter}
              onChange={(e) =>
                setSeverityFilter(
                  e.target.value
                )
              }
              className="w-full rounded-lg border border-gray-300 bg-white px-4 py-3 text-gray-900 outline-none focus:border-blue-500"
            >

              <option value="ALL">
                All Severities
              </option>

              <option value="CRITICAL">
                Critical
              </option>

              <option value="HIGH">
                High
              </option>

              <option value="MEDIUM">
                Medium
              </option>

              <option value="LOW">
                Low
              </option>

            </select>

          </div>


          {/* STATUS */}

          <div>

            <label className="mb-2 block text-sm font-medium text-gray-700">
              Status
            </label>

            <select
              value={statusFilter}
              onChange={(e) =>
                setStatusFilter(
                  e.target.value
                )
              }
              className="w-full rounded-lg border border-gray-300 bg-white px-4 py-3 text-gray-900 outline-none focus:border-blue-500"
            >

              <option value="ACTIVE">
                Active
              </option>

              <option value="ALL">
                All Alerts
              </option>

              <option value="RESOLVED">
                Resolved
              </option>

            </select>

          </div>

        </div>


        {/* FILTER INFO */}

        <div className="mt-4 flex flex-wrap items-center justify-between gap-3">

          <p className="text-xs text-gray-500">
            Showing{" "}
            <span className="font-semibold text-gray-700">
              {filteredAlerts.length}
            </span>{" "}
            alerts
          </p>


          {(search ||
            severityFilter !== "ALL" ||
            statusFilter !== "ACTIVE") && (

            <button
              onClick={() => {
                setSearch("");
                setSeverityFilter("ALL");
                setStatusFilter("ACTIVE");
              }}
              className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-xs font-medium text-gray-700 hover:bg-gray-50"
            >
              Clear Filters
            </button>

          )}

        </div>

      </div>


      {/* ALERT MONITORING */}

      <div>

        <h2 className="mb-4 text-lg font-semibold text-gray-900">
          Alert Monitoring
        </h2>


        {loading ? (

          <div className="rounded-xl border border-gray-200 bg-white p-10 text-center shadow-sm">

            <p className="text-sm text-gray-500">
              Loading security alerts...
            </p>

          </div>

        ) : filteredAlerts.length === 0 ? (

          <div className="rounded-xl border border-gray-200 bg-white p-12 text-center shadow-sm">

            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-green-100 text-2xl text-green-600">
              ✓
            </div>

            <h2 className="mt-4 text-xl font-semibold text-gray-900">
              No Alerts Found
            </h2>

            <p className="mt-2 text-sm text-gray-500">
              No security alerts match
              the current filters.
            </p>

            <div className="mx-auto mt-5 max-w-md rounded-lg bg-gray-50 p-3">

              <p className="text-xs text-gray-500">
                AI alert engine is monitoring
                vehicle detections, blacklisted
                plates and suspicious routes.
              </p>

            </div>

          </div>

        ) : (

          <div className="space-y-4">

            {filteredAlerts.map(
              (alert) => (

                <div
                  key={alert.id}
                  className={`rounded-xl border bg-white p-6 shadow-sm ${
                    alert.is_resolved
                      ? "border-gray-200"
                      : alert.severity?.toUpperCase() ===
                        "HIGH"
                      ? "border-red-300"
                      : "border-orange-200"
                  }`}
                >

                  {/* ALERT HEADER */}

                  <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">

                    <div>

                      <div className="flex flex-wrap items-center gap-2">

                        {!alert.is_resolved && (
                          <span className="h-2.5 w-2.5 rounded-full bg-red-500" />
                        )}

                        <h2 className="font-bold text-gray-900">
                          {formatAlertType(
                            alert.alert_type
                          )}
                        </h2>

                      </div>


                      <p className="mt-2 font-mono text-xl font-bold tracking-wide text-gray-800">
                        {alert.plate_number ||
                          "UNKNOWN"}
                      </p>

                    </div>


                    <div className="flex flex-wrap gap-2">

                      <span
                        className={`rounded-full border px-3 py-1 text-xs font-semibold ${getSeverityStyle(
                          alert.severity
                        )}`}
                      >
                        {alert.severity ||
                          "UNKNOWN"}
                      </span>


                      <span
                        className={`rounded-full px-3 py-1 text-xs font-semibold ${
                          alert.is_resolved
                            ? "bg-green-100 text-green-700"
                            : "bg-red-100 text-red-700"
                        }`}
                      >
                        {alert.is_resolved
                          ? "RESOLVED"
                          : "ACTIVE"}
                      </span>

                    </div>

                  </div>


                  {/* MESSAGE */}

                  <div
                    className={`mt-5 rounded-lg p-4 ${
                      alert.is_resolved
                        ? "bg-gray-50"
                        : "bg-red-50"
                    }`}
                  >

                    <p
                      className={`text-sm ${
                        alert.is_resolved
                          ? "text-gray-700"
                          : "text-red-800"
                      }`}
                    >
                      {alert.message}
                    </p>

                  </div>


                  {/* DETAILS */}

                  <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">

                    {/* CAMERA */}

                    <div className="rounded-lg border border-gray-200 p-4">

                      <p className="text-xs uppercase tracking-wide text-gray-400">
                        Camera
                      </p>

                      <p className="mt-1 text-sm font-semibold text-gray-900">
                        {alert.camera_id ||
                          "N/A"}
                      </p>

                    </div>


                    {/* TYPE */}

                    <div className="rounded-lg border border-gray-200 p-4">

                      <p className="text-xs uppercase tracking-wide text-gray-400">
                        Alert Type
                      </p>

                      <p className="mt-1 text-sm font-semibold text-gray-900">
                        {formatAlertType(
                          alert.alert_type
                        )}
                      </p>

                    </div>


                    {/* TIME */}

                    <div className="rounded-lg border border-gray-200 p-4">

                      <p className="text-xs uppercase tracking-wide text-gray-400">
                        Detected At
                      </p>

                      <p className="mt-1 text-sm text-gray-700">
                        {formatTime(
                          alert.timestamp
                        )}
                      </p>

                    </div>


                    {/* LOCATION */}

                    <div className="rounded-lg border border-gray-200 p-4">

                      <p className="text-xs uppercase tracking-wide text-gray-400">
                        Location
                      </p>

                      <p className="mt-1 text-sm font-medium text-gray-900">

                        {alert.latitude !==
                          null &&
                        alert.longitude !==
                          null
                          ? `${alert.latitude.toFixed(
                              4
                            )}, ${alert.longitude.toFixed(
                              4
                            )}`
                          : "N/A"}

                      </p>

                    </div>

                  </div>

                </div>

              )
            )}

          </div>

        )}

      </div>

    </main>
  );
}