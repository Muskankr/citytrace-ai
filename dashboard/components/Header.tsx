export default function Header() {
  return (
    <header className="flex items-center justify-between border-b border-[#263442] bg-[#111a23] px-6 py-4">

      <div>
        <h2 className="text-xl font-semibold text-[#f1f5f9]">
          City Traffic Intelligence
        </h2>

        <p className="text-sm text-[#81909e]">
          Multi-camera ANPR & Urban Traffic Analytics
        </p>
      </div>

      <div className="flex items-center gap-2 rounded-full border border-[#263442] bg-[#17212b] px-3 py-1.5">

        <span className="h-2 w-2 rounded-full bg-green-500" />

        <span className="text-sm text-[#b8c3cc]">
          System Online
        </span>

      </div>

    </header>
  );
}