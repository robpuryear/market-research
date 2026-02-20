"use client";
import { use } from "react";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { ReportViewer } from "@/components/reports/ReportViewer";
import { DownloadButton } from "@/components/reports/DownloadButton";
import { GenerateReportButton } from "@/components/reports/GenerateReportButton";
import Link from "next/link";

interface Props {
  params: Promise<{ ticker: string }>;
}

function ResearchContent({ ticker }: { ticker: string }) {
  const searchParams = useSearchParams();
  const id = searchParams.get("id");

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link href="/reports" className="text-gray-500 hover:text-gray-700 text-sm">← Reports</Link>
          <h1 className="text-lg font-bold text-gray-800 font-mono">Deep Research: {ticker}</h1>
        </div>
        <div className="flex items-center gap-3">
          <GenerateReportButton type="research" ticker={ticker} label="Regenerate" />
          {id && <DownloadButton reportId={id} filename={`${ticker.toLowerCase()}-research.html`} />}
        </div>
      </div>
      {id ? (
        <ReportViewer reportId={id} />
      ) : (
        <div className="text-gray-500 text-sm p-12 text-center bg-white border border-gray-300 rounded-lg">
          No report selected. Generate one or select from the Reports page.
        </div>
      )}
    </div>
  );
}

export default function ResearchPage({ params }: Props) {
  const { ticker } = use(params);
  return (
    <Suspense fallback={<div className="p-6 text-gray-500">Loading...</div>}>
      <ResearchContent ticker={ticker.toUpperCase()} />
    </Suspense>
  );
}
