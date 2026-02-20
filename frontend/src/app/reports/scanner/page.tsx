"use client";
import { useSearchParams } from "next/navigation";
import { getReportViewUrl } from "@/lib/api";
import Link from "next/link";

export default function ScannerReportPage() {
  const searchParams = useSearchParams();
  const reportId = searchParams.get("id");

  if (!reportId) {
    return (
      <div className="p-6">
        <div className="text-red-600">Error: No report ID provided</div>
        <Link href="/reports" className="text-blue-600 hover:underline mt-4 inline-block">
          ← Back to Reports
        </Link>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col">
      <div className="bg-white border-b border-gray-300 px-6 py-3 flex items-center justify-between">
        <h1 className="text-sm font-semibold text-gray-800">Market Scanner Report</h1>
        <Link
          href="/reports"
          className="text-sm text-blue-600 hover:text-blue-800 transition-colors"
        >
          ← Back to Reports
        </Link>
      </div>
      <iframe
        src={getReportViewUrl(reportId)}
        className="flex-1 w-full border-0"
        title="Scanner Report"
      />
    </div>
  );
}
