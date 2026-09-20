export default function DemoMode() {
  return (
    <div className="mb-6 flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50 p-4">
      <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-amber-100 text-sm">
        🧪
      </div>

      <div>
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-semibold text-amber-900">
            DEMO ENVIRONMENT
          </h3>

          <span className="rounded-full bg-amber-200 px-2 py-0.5 text-[10px] font-bold text-amber-800">
            PROTOTYPE
          </span>
        </div>

        <p className="mt-1 text-xs leading-5 text-amber-800">
          Camera feeds, GPS coordinates and selected detection records
          are simulated for prototype demonstration.
        </p>
      </div>
    </div>
  );
}