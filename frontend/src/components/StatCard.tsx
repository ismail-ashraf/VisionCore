import type { LucideIcon } from "lucide-react";

type StatCardProps = {
  title: string;
  value: string;
  subtitle: string;
  icon: LucideIcon;
  iconColor: string;
};

export default function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  iconColor,
}: StatCardProps) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-[#111a2b] p-5">
      <div className="mb-5 flex items-center justify-between">
        <p className="text-sm text-slate-400">{title}</p>
        <div className={`rounded-lg bg-slate-800/70 p-2 ${iconColor}`}>
          <Icon size={19} />
        </div>
      </div>

      <h3 className="text-3xl font-bold tracking-tight text-white">{value}</h3>
      <p className="mt-2 text-xs text-slate-500">{subtitle}</p>
    </div>
  );
}