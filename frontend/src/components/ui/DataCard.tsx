import { ReactNode } from "react";
import { clsx } from "clsx";

interface DataCardProps {
  label: string;
  value: ReactNode;
  sub?: ReactNode;
  className?: string;
}

export function DataCard({ label, value, sub, className }: DataCardProps) {
  return (
    <div className={clsx("bg-white border border-gray-300 rounded-lg p-4", className)}>
      <div className="text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">{label}</div>
      <div className="text-2xl font-bold text-gray-900 font-mono">{value}</div>
      {sub && <div className="text-xs text-gray-500 mt-1">{sub}</div>}
    </div>
  );
}
