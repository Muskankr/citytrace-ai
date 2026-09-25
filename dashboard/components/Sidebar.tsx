"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const menuItems = [
  { name: "Dashboard", href: "/", icon: "▣" },
  { name: "Cameras", href: "/cameras", icon: "◉" },
  { name: "Video Processing", href: "/video", icon: "▶" },
  { name: "Live Detections", href: "/detections", icon: "◈" },
  { name: "Trajectories", href: "/trajectories", icon: "↗" },
  { name: "Traffic Analytics", href: "/analytics", icon: "▥" },
  { name: "Alerts", href: "/alerts", icon: "⚠" },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed inset-y-0 left-0 z-50 flex w-16 flex-col border-r border-[#263442] bg-[#111a23] md:w-64">
      {/* Logo */}
      <div className="flex h-20 shrink-0 items-center border-b border-[#263442] px-2 md:px-6">
        <div className="w-full text-center md:text-left">
          <h1 className="text-sm font-bold tracking-tight text-[#f1f5f9] md:text-xl">
            <span className="md:hidden">CT</span>
            <span className="hidden md:inline">CityTraceAI</span>
          </h1>

          <p className="hidden text-xs text-[#81909e] md:block">
            Traffic Intelligence
          </p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-2 py-6 md:px-3">
        <p className="mb-3 hidden px-3 text-xs font-semibold uppercase tracking-wider text-[#657585] md:block">
          Navigation
        </p>

        <div className="space-y-1">
          {menuItems.map((item) => {
            const isActive =
              item.href === "/"
                ? pathname === "/"
                : pathname.startsWith(item.href);

            return (
              <Link
                key={item.href}
                href={item.href}
                title={item.name}
                className={`flex items-center justify-center gap-3 rounded-lg px-2 py-3 text-sm font-medium transition md:justify-start md:px-4 ${
                  isActive
                    ? "bg-[#26384a] text-white"
                    : "text-[#9aa8b5] hover:bg-[#1a2732] hover:text-[#e7edf2]"
                }`}
              >
                <span className="w-5 shrink-0 text-center text-base">
                  {item.icon}
                </span>

                <span className="hidden md:inline">
                  {item.name}
                </span>
              </Link>
            );
          })}
        </div>
      </nav>

      {/* System Status */}
      <div className="shrink-0 border-t border-[#263442] p-2 md:p-4">
        <div className="rounded-lg border border-[#263442] bg-[#17212b] p-2 md:p-3">
          <div className="flex items-center justify-center gap-2 md:justify-start">
            <span className="h-2.5 w-2.5 shrink-0 rounded-full bg-green-500" />

            <span className="hidden text-sm font-medium text-[#e7edf2] md:inline">
              System Online
            </span>
          </div>

          <p className="mt-1 hidden text-xs text-[#81909e] md:block">
            AI Engine connected
          </p>
        </div>
      </div>
    </aside>
  );
}