export default function Header() {
  return (
    <header className="flex flex-col gap-3 border-b border-[#263442] bg-[#111a23] px-4 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6">
      <div className="min-w-0">
        <h2 className="text-lg font-semibold text-[#f1f5f9] sm:text-xl">
          City Traffic Intelligence
        </h2>

        <p className="text-xs text-[#81909e] sm:text-sm">
          Multi-camera ANPR & Urban Traffic Analytics
        </p>
      </div>

      <div className="flex w-fit items-center gap-2 rounded-full border border-[#263442] bg-[#17212b] px-3 py-1.5">
        <span className="h-2 w-2 shrink-0 rounded-full bg-green-500" />

        <span className="text-xs text-[#b8c3cc] sm:text-sm">
          System Online
        </span>
      </div>
    </header>
  );
}