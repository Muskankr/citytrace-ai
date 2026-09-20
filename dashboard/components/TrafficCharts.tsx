"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";

type AnalyticsItem = {
  id: number;
  camera_id: string;
  vehicle_count: number;
  car_count: number;
  motorcycle_count: number;
  bus_count: number;
  truck_count: number;
  traffic_density: number;
  average_speed: number;
  congestion_level: string;
  incoming_count: number;
  outgoing_count: number;
};

type TrafficChartsProps = {
  analytics: AnalyticsItem[];
};

const PIE_COLORS = [
  "#5b8def",
  "#5fa8a8",
  "#d3a84c",
  "#8b9aaa",
];

export default function TrafficCharts({
  analytics,
}: TrafficChartsProps) {

  if (!analytics || analytics.length === 0) {
    return (
      <div className="rounded-xl border border-[#263442] bg-[#17212b] p-6">
        <p className="text-sm text-[#81909e]">
          No traffic analytics available.
        </p>
      </div>
    );
  }

  /*
   * Keep only the latest analytics record
   * for each camera.
   *
   * This prevents old/demo analytics records
   * from appearing multiple times.
   */
  const latestByCamera = new Map<string, AnalyticsItem>();

  analytics.forEach((item) => {
    const existing = latestByCamera.get(item.camera_id);

    if (!existing || item.id > existing.id) {
      latestByCamera.set(item.camera_id, item);
    }
  });

  const latestAnalytics = Array.from(
    latestByCamera.values()
  ).sort((a, b) =>
    a.camera_id.localeCompare(b.camera_id)
  );

  /*
   * -----------------------------
   * Vehicle count by camera
   * -----------------------------
   */

  const cameraData = latestAnalytics.map((item) => ({
    camera: item.camera_id,
    vehicles: Number(item.vehicle_count || 0),
  }));

  /*
   * -----------------------------
   * Vehicle type distribution
   * -----------------------------
   */

  const vehicleTypes = [
    {
      name: "Cars",
      value: latestAnalytics.reduce(
        (sum, item) =>
          sum + Number(item.car_count || 0),
        0
      ),
    },
    {
      name: "Motorcycles",
      value: latestAnalytics.reduce(
        (sum, item) =>
          sum + Number(item.motorcycle_count || 0),
        0
      ),
    },
    {
      name: "Buses",
      value: latestAnalytics.reduce(
        (sum, item) =>
          sum + Number(item.bus_count || 0),
        0
      ),
    },
    {
      name: "Trucks",
      value: latestAnalytics.reduce(
        (sum, item) =>
          sum + Number(item.truck_count || 0),
        0
      ),
    },
  ].filter((item) => item.value > 0);

  /*
   * -----------------------------
   * Congestion
   * -----------------------------
   */

  const congestionData = latestAnalytics.map((item) => {

    const level = String(
      item.congestion_level || "LOW"
    ).toUpperCase();

    let congestion = 1;

    if (level === "MEDIUM") {
      congestion = 2;
    } else if (
      level === "HIGH" ||
      level === "CRITICAL"
    ) {
      congestion = 3;
    }

    return {
      camera: item.camera_id,
      congestion,
      level,
    };
  });

  function getCongestionColor(level: string) {

    switch (level) {

      case "CRITICAL":
        return "#d45b5b";

      case "HIGH":
        return "#d45b5b";

      case "MEDIUM":
        return "#d3a84c";

      default:
        return "#5b8def";
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-2">

      {/* VEHICLE COUNT */}

      <div className="rounded-xl border border-[#263442] bg-[#17212b] p-6">

        <div className="mb-5">

          <h3 className="text-base font-semibold text-[#f1f5f9]">
            Vehicle Count by Camera
          </h3>

          <p className="mt-1 text-xs text-[#81909e]">
            Latest aggregated vehicle count for each camera
          </p>

        </div>

        <div className="h-[300px]">

          <ResponsiveContainer
            width="100%"
            height="100%"
          >

            <BarChart
              data={cameraData}
              margin={{
                top: 5,
                right: 10,
                left: 0,
                bottom: 5,
              }}
            >

              <CartesianGrid
                stroke="#2a3947"
                strokeDasharray="3 3"
                vertical={false}
              />

              <XAxis
                dataKey="camera"
                tick={{
                  fill: "#91a0ad",
                  fontSize: 12,
                }}
                axisLine={{
                  stroke: "#334454",
                }}
                tickLine={false}
              />

              <YAxis
                allowDecimals={false}
                tick={{
                  fill: "#91a0ad",
                  fontSize: 12,
                }}
                axisLine={false}
                tickLine={false}
              />

              <Tooltip
                cursor={{
                  fill: "rgba(91, 141, 239, 0.08)",
                }}
                contentStyle={{
                  backgroundColor: "#111a23",
                  border: "1px solid #334454",
                  borderRadius: "8px",
                  color: "#f1f5f9",
                }}
              />

              <Bar
                dataKey="vehicles"
                name="Vehicles"
                fill="#5b8def"
                radius={[5, 5, 0, 0]}
              />

            </BarChart>

          </ResponsiveContainer>

        </div>

      </div>


      {/* VEHICLE CLASSIFICATION */}

      <div className="rounded-xl border border-[#263442] bg-[#17212b] p-6">

        <div className="mb-5">

          <h3 className="text-base font-semibold text-[#f1f5f9]">
            Vehicle Classification
          </h3>

          <p className="mt-1 text-xs text-[#81909e]">
            Latest vehicle classification across the camera network
          </p>

        </div>

        <div className="h-[300px]">

          {vehicleTypes.length === 0 ? (

            <div className="flex h-full items-center justify-center">

              <p className="text-sm text-[#81909e]">
                No vehicle classification data.
              </p>

            </div>

          ) : (

            <ResponsiveContainer
              width="100%"
              height="100%"
            >

              <PieChart>

                <Pie
                  data={vehicleTypes}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  innerRadius={55}
                  paddingAngle={2}
                  label
                  labelLine={false}
                >

                  {vehicleTypes.map(
                    (item, index) => (
                      <Cell
                        key={`${item.name}-${index}`}
                        fill={
                          PIE_COLORS[
                            index %
                            PIE_COLORS.length
                          ]
                        }
                        stroke="#17212b"
                        strokeWidth={2}
                      />
                    )
                  )}

                </Pie>

                <Tooltip
                  contentStyle={{
                    backgroundColor: "#111a23",
                    border: "1px solid #334454",
                    borderRadius: "8px",
                    color: "#f1f5f9",
                  }}
                />

                <Legend
                  wrapperStyle={{
                    color: "#b8c3cc",
                    fontSize: "12px",
                  }}
                />

              </PieChart>

            </ResponsiveContainer>

          )}

        </div>

      </div>


      {/* TRAFFIC CONGESTION */}

      <div className="rounded-xl border border-[#263442] bg-[#17212b] p-6 lg:col-span-2">

        <div className="mb-5">

          <h3 className="text-base font-semibold text-[#f1f5f9]">
            Traffic Congestion
          </h3>

          <p className="mt-1 text-xs text-[#81909e]">
            Latest congestion level for each monitored camera
          </p>

        </div>

        <div className="h-[300px]">

          <ResponsiveContainer
            width="100%"
            height="100%"
          >

            <BarChart
              data={congestionData}
              margin={{
                top: 5,
                right: 10,
                left: 10,
                bottom: 5,
              }}
            >

              <CartesianGrid
                stroke="#2a3947"
                strokeDasharray="3 3"
                vertical={false}
              />

              <XAxis
                dataKey="camera"
                tick={{
                  fill: "#91a0ad",
                  fontSize: 12,
                }}
                axisLine={{
                  stroke: "#334454",
                }}
                tickLine={false}
              />

              <YAxis
                domain={[0, 3]}
                ticks={[1, 2, 3]}
                tickFormatter={(value) => {

                  if (value === 3) {
                    return "HIGH";
                  }

                  if (value === 2) {
                    return "MEDIUM";
                  }

                  return "LOW";
                }}
                tick={{
                  fill: "#91a0ad",
                  fontSize: 11,
                }}
                axisLine={false}
                tickLine={false}
              />

              <Tooltip
                cursor={{
                  fill: "rgba(91, 141, 239, 0.08)",
                }}
                contentStyle={{
                  backgroundColor: "#111a23",
                  border: "1px solid #334454",
                  borderRadius: "8px",
                  color: "#f1f5f9",
                }}
                formatter={(value, name, props) => {

                  if (
                    name === "Congestion Level"
                  ) {

                    return [
                      props.payload.level,
                      "Congestion",
                    ];

                  }

                  return [value, name];

                }}
              />

              <Bar
                dataKey="congestion"
                name="Congestion Level"
                radius={[5, 5, 0, 0]}
              >

                {congestionData.map(
                  (item, index) => (

                    <Cell
                      key={`${item.camera}-${index}`}
                      fill={getCongestionColor(
                        item.level
                      )}
                    />

                  )
                )}

              </Bar>

            </BarChart>

          </ResponsiveContainer>

        </div>

      </div>

    </div>
  );
}