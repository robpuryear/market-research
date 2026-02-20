"use client";
import { getReportViewUrl } from "@/lib/api";

interface ReportViewerProps {
  reportId: string;
}

export function ReportViewer({ reportId }: ReportViewerProps) {
  const src = getReportViewUrl(reportId);
  return (
    <div className="w-full h-[80vh] bg-white rounded-lg border border-gray-300 overflow-hidden">
      <iframe
        src={src}
        className="w-full h-full"
        sandbox="allow-scripts allow-same-origin"
        title="Market Intelligence Report"
      />
    </div>
  );
}
