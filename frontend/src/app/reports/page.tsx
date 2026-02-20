"use client";
import { useReports } from "@/hooks/useReports";
import { ReportCard } from "@/components/reports/ReportCard";
import { GenerateReportButton } from "@/components/reports/GenerateReportButton";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import { WATCHLIST_TICKERS } from "@/lib/constants";

export default function ReportsPage() {
  const { data: reports, isLoading } = useReports();

  const sorted = reports ? [...reports].sort(
    (a, b) => new Date(b.generated_at).getTime() - new Date(a.generated_at).getTime()
  ) : [];

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <h1 className="text-lg font-bold text-gray-800 font-mono tracking-wide">▣ Reports</h1>

      {/* Generate buttons */}
      <div className="bg-white border border-gray-300 rounded-lg p-4 space-y-3">
        <div className="text-sm font-semibold text-purple-700 uppercase tracking-widest">Generate Reports</div>
        <div className="flex flex-wrap gap-3">
          <GenerateReportButton type="daily" label="Daily Market Report" />
          <GenerateReportButton type="analytics" label="Advanced Analytics" />
          {WATCHLIST_TICKERS.map((t) => (
            <GenerateReportButton key={t} type="research" ticker={t} label={`${t} Research`} />
          ))}
        </div>
      </div>

      {/* Report list */}
      {isLoading && <LoadingSpinner />}
      {!isLoading && sorted.length === 0 && (
        <div className="text-gray-500 text-sm p-8 text-center">
          No reports generated yet. Click a button above to generate one.
        </div>
      )}
      {sorted.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {sorted.map((r) => (
            <ReportCard key={r.id} report={r} />
          ))}
        </div>
      )}
    </div>
  );
}
