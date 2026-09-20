"use client";

type ODMatrixProps = {
  data: Record<string, Record<string, number>>;
};

export default function ODMatrix({ data }: ODMatrixProps) {
  const cameras = Array.from(
    new Set([
      ...Object.keys(data),
      ...Object.values(data).flatMap((destinations) =>
        Object.keys(destinations)
      ),
    ])
  ).sort();

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="mb-6">
        <h2 className="text-xl font-bold text-slate-900">
          Origin-Destination Matrix
        </h2>

        <p className="mt-1 text-sm text-slate-500">
          Vehicle movement between camera locations
        </p>
      </div>

      {cameras.length === 0 ? (
        <div className="rounded-xl bg-slate-50 p-8 text-center">
          <p className="text-sm text-slate-500">
            No completed trajectories available.
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full border-collapse">
            <thead>
              <tr>
                <th className="border border-slate-200 bg-slate-50 px-5 py-4 text-left text-sm font-semibold text-slate-700">
                  Origin ↓ / Destination →
                </th>

                {cameras.map((camera) => (
                  <th
                    key={camera}
                    className="border border-slate-200 bg-slate-50 px-5 py-4 text-center text-sm font-semibold text-slate-700"
                  >
                    {camera}
                  </th>
                ))}
              </tr>
            </thead>

            <tbody>
              {cameras.map((origin) => (
                <tr key={origin}>
                  <th className="border border-slate-200 bg-slate-50 px-5 py-4 text-left text-sm font-semibold text-slate-700">
                    {origin}
                  </th>

                  {cameras.map((destination) => {
                    const count =
                      data[origin]?.[destination] ?? 0;

                    return (
                      <td
                        key={`${origin}-${destination}`}
                        className={`border border-slate-200 px-5 py-4 text-center text-sm ${
                          count > 0
                            ? "font-bold text-blue-700"
                            : "text-slate-400"
                        }`}
                      >
                        {count}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}