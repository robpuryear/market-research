import { getReportDownloadUrl } from "@/lib/api";

interface DownloadButtonProps {
  reportId: string;
  filename?: string;
}

export function DownloadButton({ reportId, filename }: DownloadButtonProps) {
  return (
    <a
      href={getReportDownloadUrl(reportId)}
      download={filename}
      className="inline-flex items-center gap-2 bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm px-4 py-2 rounded border border-gray-300 transition-colors"
    >
      ↓ Download HTML
    </a>
  );
}
