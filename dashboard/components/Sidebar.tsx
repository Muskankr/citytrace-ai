"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const menuItems = [
  {
    name: "Dashboard",
    href: "/",
    icon: "▣",
  },
  {
    name: "Cameras",
    href: "/cameras",
    icon: "◉",
  },
  {
    name: "Video Processing",
    href: "/video",
    icon: "▶",
  },
  {
    name: "Live Detections",
    href: "/detections",
    icon: "◈",
  },
  {
    name: "Trajectories",
    href: "/trajectories",
    icon: "↗",
  },
  {
    name: "Traffic Analytics",
    href: "/analytics",
    icon: "▥",
  },
  {
    name: "Alerts",
    href: "/alerts",
    icon: "⚠",
  },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed inset-y-0 left-0 z-50 flex w-64 flex-col border-r border-[#263442] bg-[#111a23]">

      {/* Logo */}

      <div className="flex h-20 shrink-0 items-center border-b border-[#263442] px-6">
        <div>

          <h1 className="text-xl font-bold tracking-tight text-[#f1f5f9]">
            CityTraceAI
          </h1>

          <p className="text-xs text-[#81909e]">
            Traffic Intelligence
          </p>

        </div>
      </div>


      {/* Navigation */}

      <nav className="flex-1 overflow-y-auto px-3 py-6">

        <p className="mb-3 px-3 text-xs font-semibold uppercase tracking-wider text-[#657585]">
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
                className={`flex items-center gap-3 rounded-lg px-4 py-3 text-sm font-medium transition ${
                  isActive
                    ? "bg-[#26384a] text-white"
                    : "text-[#9aa8b5] hover:bg-[#1a2732] hover:text-[#e7edf2]"
                }`}
              >

                <span className="w-5 text-center text-base">
                  {item.icon}
                </span>

                <span>
                  {item.name}
                </span>

              </Link>
            );

          })}

        </div>

      </nav>


      {/* System Status */}

      <div className="shrink-0 border-t border-[#263442] p-4">

        <div className="rounded-lg border border-[#263442] bg-[#17212b] p-3">

          <div className="flex items-center gap-2">

            <span className="h-2.5 w-2.5 rounded-full bg-green-500" />

            <span className="text-sm font-medium text-[#e7edf2]">
              System Online
            </span>

          </div>

          <p className="mt-1 text-xs text-[#81909e]">
            AI Engine connected
          </p>

        </div>

      </div>

    </aside>
  );
}