type SystemStatusProps = {
  cameraCount: number;
  activeCameraCount: number;
};

export default function SystemStatus({
  cameraCount,
  activeCameraCount,
}: SystemStatusProps) {
  const services = [
    {
      name: "AI Engine",
      status: "ONLINE",
    },
    {
      name: "Database",
      status: "CONNECTED",
    },
    {
      name: "Vehicle Tracker",
      status: "RUNNING",
    },
    {
      name: "ANPR Engine",
      status: "RUNNING",
    },
  ];

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
      <div className="mb-5 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">
            System Status
          </h2>

          <p className="mt-1 text-sm text-gray-500">
            CityAI engine health and service status
          </p>
        </div>

        <span className="flex items-center gap-2 rounded-full bg-green-100 px-3 py-1.5 text-xs font-semibold text-green-700">
          <span className="h-2 w-2 animate-pulse rounded-full bg-green-500" />
          OPERATIONAL
        </span>
      </div>

      <div className="grid gap-3 md:grid-cols-3 lg:grid-cols-6">
        {services.map((service) => (
          <div
            key={service.name}
            className="rounded-lg border border-gray-100 bg-gray-50 p-4"
          >
            <div className="mb-2 flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-green-500" />

              <span className="text-xs font-medium text-gray-500">
                {service.name}
              </span>
            </div>

            <p className="text-sm font-semibold text-gray-900">
              {service.status}
            </p>
          </div>
        ))}

        <div className="rounded-lg border border-gray-100 bg-gray-50 p-4">
          <p className="mb-2 text-xs font-medium text-gray-500">
            Cameras
          </p>

          <p className="text-sm font-semibold text-gray-900">
            {activeCameraCount} / {cameraCount} ACTIVE
          </p>
        </div>

        <div className="rounded-lg border border-gray-100 bg-gray-50 p-4">
          <p className="mb-2 text-xs font-medium text-gray-500">
            Data Stream
          </p>

          <p className="text-sm font-semibold text-gray-900">
            LIVE
          </p>
        </div>
      </div>
    </div>
  );
}