"use client";

import dynamic from "next/dynamic";

const TrafficMapClient = dynamic(
  () => import("./TrafficMapClient"),
  {
    ssr: false,
    loading: () => (
      <div className="flex h-[500px] items-center justify-center rounded-2xl bg-slate-100">
        Loading GIS traffic map...
      </div>
    ),
  }
);

interface TrafficMapProps {
  heatmapData?: any[];
  cameras?: any[];
  trajectories?: any[];
}

export default function TrafficMap({
  heatmapData = [],
  cameras = [],
  trajectories = [],
}: TrafficMapProps) {
  return (
    <TrafficMapClient
      heatmapData={heatmapData}
      cameras={cameras}
      trajectories={trajectories}
    />
  );
}