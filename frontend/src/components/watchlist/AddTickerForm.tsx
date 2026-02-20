"use client";
import { useState } from "react";
import { addToWatchlist } from "@/lib/api";
import { mutate } from "swr";

export function AddTickerForm() {
  const [ticker, setTicker] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ticker.trim()) return;

    setIsLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const result = await addToWatchlist(ticker.trim().toUpperCase());
      setSuccess(`Added ${result.ticker} to watchlist`);
      setTicker("");
      // Refresh the watchlist
      mutate("watchlist");
      // Clear success message after 3 seconds
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      if (err.message.includes("409")) {
        setError("Ticker already in watchlist");
      } else if (err.message.includes("404")) {
        setError("Ticker not found - please enter a valid stock symbol");
      } else {
        setError(err.message || "Failed to add ticker");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-white border border-gray-300 rounded-lg p-4">
      <h3 className="text-sm font-semibold text-gray-900 mb-3">Add Stock to Watchlist</h3>
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={ticker}
          onChange={(e) => setTicker(e.target.value.toUpperCase())}
          placeholder="Enter ticker (e.g., AAPL)"
          className="flex-1 px-3 py-2 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={isLoading}
          maxLength={10}
        />
        <button
          type="submit"
          disabled={isLoading || !ticker.trim()}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white text-sm font-medium rounded transition-colors"
        >
          {isLoading ? "Adding..." : "Add"}
        </button>
      </form>
      {error && (
        <div className="mt-2 text-xs text-red-600 bg-red-50 border border-red-200 rounded px-3 py-2">
          {error}
        </div>
      )}
      {success && (
        <div className="mt-2 text-xs text-green-600 bg-green-50 border border-green-200 rounded px-3 py-2">
          {success}
        </div>
      )}
    </div>
  );
}
