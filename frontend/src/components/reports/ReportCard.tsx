"use client";
import { useState } from "react";
import Link from "next/link";
import { getReportDownloadUrl, deleteReport } from "@/lib/api";
import { formatDateTime } from "@/lib/formatters";
import type { ReportMeta } from "@/lib/types";
import { Badge } from "@/components/ui/Badge";
import { mutate } from "swr";

interface ReportCardProps {
  report: ReportMeta;
}

const TYPE_LABELS = {
  daily: "Daily Market",
  analytics: "Advanced Analytics",
  research: "Deep Research",
  scanner: "Market Scanner",
};

export function ReportCard({ report }: ReportCardProps) {
  const [isDeleting, setIsDeleting] = useState(false);

  const viewHref =
    report.type === "research" && report.ticker
      ? `/reports/research/${report.ticker}?id=${report.id}`
      : report.type === "analytics"
        ? `/reports/analytics?id=${report.id}`
        : report.type === "scanner"
          ? `/reports/scanner?id=${report.id}`
          : `/reports/daily?id=${report.id}`;

  const handleDelete = async () => {
    if (!confirm(`Delete report "${report.title}"?`)) return;
    setIsDeleting(true);
    try {
      await deleteReport(report.id);
      // Refresh the reports list
      mutate("reports");
    } catch {
      alert("Failed to delete report");
      setIsDeleting(false);
    }
  };

  if (isDeleting) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 opacity-50">
        <div className="text-sm text-gray-500 text-center">Deleting...</div>
      </div>
    );
  }

  return (
    <div className="bg-white border border-gray-300 rounded-lg p-4 hover:border-gray-300 transition-colors">
      <div className="flex items-start justify-between mb-2">
        <Badge variant="default">{TYPE_LABELS[report.type]}</Badge>
        {report.ticker && (
          <span className="text-blue-600 font-mono font-bold text-sm">{report.ticker}</span>
        )}
      </div>
      <div className="text-sm text-gray-800 mt-2 leading-tight">{report.title}</div>
      <div className="text-xs text-gray-500 mt-2">
        {formatDateTime(report.generated_at)}
        {report.file_size_kb && ` · ${report.file_size_kb}KB`}
      </div>
      <div className="flex gap-2 mt-3">
        <Link
          href={viewHref}
          className="flex-1 text-center text-xs bg-blue-50 hover:bg-blue-100 text-blue-700 px-3 py-1.5 rounded border border-blue-200 transition-colors"
        >
          View
        </Link>
        <a
          href={getReportDownloadUrl(report.id)}
          download
          className="flex-1 text-center text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-1.5 rounded border border-gray-300 transition-colors"
        >
          Download
        </a>
        <button
          onClick={handleDelete}
          className="text-xs bg-red-50 hover:bg-red-100 text-red-700 px-3 py-1.5 rounded border border-red-200 transition-colors"
          title="Delete report"
        >
          🗑️
        </button>
      </div>
    </div>
  );
}
