interface StatCardProps {
  title: string;
  value: string | number;
  description: string;
}

export default function StatCard({
  title,
  value,
  description,
}: StatCardProps) {
  return (
    <div className="rounded-xl border border-[#263442] bg-[#17212b] p-5 shadow-sm">

      <p className="text-sm text-[#81909e]">
        {title}
      </p>

      <h2 className="mt-2 text-3xl font-bold text-[#f1f5f9]">
        {value}
      </h2>

      <p className="mt-2 text-sm text-[#81909e]">
        {description}
      </p>

    </div>
  );
}