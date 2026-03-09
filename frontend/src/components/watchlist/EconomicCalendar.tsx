"use client";
import { useEconomicCalendar } from "@/hooks/useAnalytics";
import { InfoIcon } from "@/components/ui/Tooltip";
import { TOOLTIPS } from "@/lib/tooltips";
import type { EconomicEvent } from "@/lib/types";

const EVENT_STYLES: Record<string, { dot: string; label: string }> = {
  cpi:  { dot: "bg-orange-400", label: "CPI" },
  fomc: { dot: "bg-red-500",    label: "FOMC" },
  jobs: { dot: "bg-emerald-500", label: "Jobs" },
};

function DayChip({ days }: { days: number }) {
  const bg =
    days === 0 ? "bg-red-100 text-red-700" :
    days <= 3  ? "bg-orange-100 text-orange-700" :
    days <= 7  ? "bg-yellow-100 text-yellow-700" :
                 "bg-gray-100 text-gray-600";
  const label = days === 0 ? "Today" : days === 1 ? "Tomorrow" : `${days}d`;
  return (
    <span className={`text-xs px-2 py-0.5 rounded font-mono font-semibold ${bg}`}>
      {label}
    </span>
  );
}

function EventRow({ event }: { event: EconomicEvent }) {
  const style = EVENT_STYLES[event.event_type] ?? { dot: "bg-blue-400", label: event.event_type.toUpperCase() };
  const formatted = new Date(event.date + "T00:00:00").toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });

  return (
    <div className="flex items-center justify-between py-1.5 border-b border-gray-100 last:border-0">
      <div className="flex items-center gap-2">
        <span className={`w-2 h-2 rounded-full flex-shrink-0 ${style.dot}`} />
        <span className="text-sm font-bold font-mono text-gray-800">{event.name}</span>
        <span className="text-xs text-gray-500">{formatted}</span>
      </div>
      <DayChip days={event.days_until} />
    </div>
  );
}

export function EconomicCalendar() {
  const { data, error, isLoading } = useEconomicCalendar();

  if (isLoading) {
    return (
      <div className="bg-white border border-gray-300 rounded-lg p-4">
        <div className="text-xs text-gray-400 font-mono animate-pulse">Loading economic calendar…</div>
      </div>
    );
  }

  if (error || !data || data.length === 0) {
    return null;
  }

  // Show next 6 events
  const upcoming = data.slice(0, 6);

  return (
    <div className="bg-white border border-gray-300 rounded-lg overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
        <div>
          <div className="text-sm font-semibold text-gray-700 font-mono flex items-center gap-1">
            Macro Calendar <InfoIcon tooltip={TOOLTIPS.macroCalendar} />
          </div>
          <div className="text-xs text-gray-500 mt-0.5">CPI · FOMC · Jobs Report</div>
        </div>
        <div className="flex items-center gap-3 text-xs text-gray-400 font-mono">
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-orange-400 inline-block" />CPI</span>
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-500 inline-block" />FOMC</span>
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" />Jobs</span>
        </div>
      </div>
      <div className="p-4">
        {upcoming.map((e) => (
          <EventRow key={`${e.event_type}-${e.date}`} event={e} />
        ))}
      </div>
    </div>
  );
}
