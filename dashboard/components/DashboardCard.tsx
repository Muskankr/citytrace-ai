interface DashboardCardProps {
  title: string;
  children: React.ReactNode;
}

export default function DashboardCard({
  title,
  children,
}: DashboardCardProps) {
  return (
    <div className="rounded-xl border border-[#263442] bg-[#17212b] p-5 shadow-sm">

      <h3 className="mb-4 text-lg font-semibold text-[#f1f5f9]">
        {title}
      </h3>

      {children}

    </div>
  );
}