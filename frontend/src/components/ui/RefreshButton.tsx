"use client";
import { useState } from "react";
import { refreshCache } from "@/lib/api";

export function RefreshButton() {
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  async function handleRefresh() {
    setLoading(true);
    setMsg(null);
    try {
      const result = await refreshCache();
      setMsg(result.message);
      setTimeout(() => setMsg(null), 3000);
    } catch {
      setMsg("Error refreshing cache");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex items-center gap-2">
      <button
        onClick={handleRefresh}
        disabled={loading}
        className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-1.5 rounded border border-gray-300 transition-colors disabled:opacity-50"
      >
        {loading ? "Refreshing..." : "⟳ Refresh Cache"}
      </button>
      {msg && <span className="text-xs text-green-600">{msg}</span>}
    </div>
  );
}
