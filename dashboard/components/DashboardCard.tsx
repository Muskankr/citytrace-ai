interface DashboardCardProps {
  title: string;
  children: React.ReactNode;
}

export default function DashboardCard({
  title,
  children,
}: DashboardCardProps) {
  return (
    <div className="rounded-xl border border-[#263442] bg-[#17212b] p-4 shadow-sm sm:p-5">
      <h3 className="mb-4 text-base font-semibold text-[#f1f5f9] sm:text-lg">
        {title}
      </h3>

      {children}
    </div>
  );
}