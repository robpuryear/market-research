"use client";
import { useState } from "react";
import { generateReport, fetchJobStatus } from "@/lib/api";
import { useReports } from "@/hooks/useReports";

interface GenerateButtonProps {
  type: "daily" | "analytics" | "research";
  ticker?: string;
  label?: string;
}

export function GenerateReportButton({ type, ticker, label }: GenerateButtonProps) {
  const [status, setStatus] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const { mutate } = useReports();

  async function handleGenerate() {
    setLoading(true);
    setStatus("Starting...");
    try {
      const { job_id } = await generateReport(type, ticker);
      setStatus("Running...");

      // Poll for completion
      const poll = async () => {
        const jobStatus = await fetchJobStatus(job_id);
        if (jobStatus.status === "complete") {
          setStatus("Complete ✓");
          setLoading(false);
          mutate(); // refresh reports list
          setTimeout(() => setStatus(null), 4000);
        } else if (jobStatus.status === "error") {
          setStatus(`Error: ${jobStatus.error}`);
          setLoading(false);
        } else {
          setTimeout(poll, 2000);
        }
      };
      setTimeout(poll, 2000);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Unknown error";
      setStatus(`Error: ${msg}`);
      setLoading(false);
    }
  }

  return (
    <div className="flex items-center gap-3">
      <button
        onClick={handleGenerate}
        disabled={loading}
        className="text-sm bg-purple-100/40 hover:bg-purple-100/60 text-purple-700 px-4 py-2 rounded border border-purple-800/50 transition-colors disabled:opacity-50"
      >
        {loading ? "Generating..." : (label || `Generate ${type}`)}
      </button>
      {status && <span className="text-xs text-gray-500">{status}</span>}
    </div>
  );
}
