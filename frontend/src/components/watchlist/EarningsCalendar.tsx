"use client";
import { useEarningsCalendar } from "@/hooks/useAnalytics";
import type { EarningsCalendarEntry } from "@/lib/types";

function groupEntries(entries: EarningsCalendarEntry[]) {
  const thisWeek: EarningsCalendarEntry[] = [];
  const nextWeek: EarningsCalendarEntry[] = [];
  const later: EarningsCalendarEntry[] = [];

  for (const e of entries) {
    if (e.days_until <= 7) {
      thisWeek.push(e);
    } else if (e.days_until <= 14) {
      nextWeek.push(e);
    } else {
      later.push(e);
    }
  }

  return { thisWeek, nextWeek, later };
}

function DayChip({ days }: { days: number }) {
  const bg =
    days === 0
      ? "bg-red-100 text-red-700"
      : days <= 3
      ? "bg-orange-100 text-orange-700"
      : days <= 7
      ? "bg-yellow-100 text-yellow-700"
      : "bg-gray-100 text-gray-600";

  const label = days === 0 ? "Today" : days === 1 ? "Tomorrow" : `${days}d`;

  return (
    <span className={`text-xs px-2 py-0.5 rounded font-mono font-semibold ${bg}`}>
      {label}
    </span>
  );
}

function EarningsRow({ entry }: { entry: EarningsCalendarEntry }) {
  return (
    <div className="flex items-center justify-between py-1.5 border-b border-gray-100 last:border-0">
      <div className="flex items-center gap-2">
        <span className="text-sm font-bold font-mono text-blue-700">{entry.ticker}</span>
        <span className="text-xs text-gray-500">
          {new Date(entry.earnings_date + "T00:00:00").toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
          })}
        </span>
      </div>
      <DayChip days={entry.days_until} />
    </div>
  );
}

function Section({ title, entries }: { title: string; entries: EarningsCalendarEntry[] }) {
  if (entries.length === 0) return null;
  return (
    <div className="mb-4 last:mb-0">
      <div className="text-xs font-semibold text-purple-700 uppercase tracking-widest mb-2">{title}</div>
      <div>
        {entries.map((e) => (
          <EarningsRow key={e.ticker} entry={e} />
        ))}
      </div>
    </div>
  );
}

export function EarningsCalendar() {
  const { data, error, isLoading } = useEarningsCalendar();

  if (isLoading) {
    return (
      <div className="bg-white border border-gray-300 rounded-lg p-4">
        <div className="text-xs text-gray-400 font-mono">Loading earnings calendar…</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white border border-gray-300 rounded-lg p-4">
        <div className="text-xs text-red-400 font-mono">Failed to load earnings calendar</div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="bg-white border border-gray-300 rounded-lg p-4">
        <div className="text-xs text-gray-400 font-mono text-center py-2">
          No upcoming earnings in the next 60 days
        </div>
      </div>
    );
  }

  const { thisWeek, nextWeek, later } = groupEntries(data);

  return (
    <div className="bg-white border border-gray-300 rounded-lg overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-200">
        <div className="text-sm font-semibold text-gray-700 font-mono">Earnings Calendar</div>
        <div className="text-xs text-gray-500 mt-0.5">{data.length} upcoming · next 60 days</div>
      </div>
      <div className="p-4">
        <Section title="This Week" entries={thisWeek} />
        <Section title="Next Week" entries={nextWeek} />
        <Section title="Later" entries={later} />
      </div>
    </div>
  );
}
