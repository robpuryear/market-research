"use client";
import { useScheduler } from "@/hooks/useScheduler";
import { formatDateTime } from "@/lib/formatters";

export function StatusBar() {
  const { data: jobs } = useScheduler();

  return (
    <footer className="h-8 bg-gray-50 border-t border-gray-300 flex items-center px-6 gap-6 overflow-x-auto">
      <span className="text-gray-500 text-xs font-mono flex-shrink-0">SCHEDULER:</span>
      {!jobs && <span className="text-gray-500 text-xs">connecting...</span>}
      {jobs?.map((job) => (
        <div key={job.id} className="flex items-center gap-2 flex-shrink-0">
          <span className="w-1.5 h-1.5 rounded-full bg-green-500 inline-block" />
          <span className="text-gray-500 text-xs font-mono">{job.name}</span>
          {job.next_run && (
            <span className="text-gray-500 text-xs">
              → {formatDateTime(job.next_run)}
            </span>
          )}
        </div>
      ))}
    </footer>
  );
}
