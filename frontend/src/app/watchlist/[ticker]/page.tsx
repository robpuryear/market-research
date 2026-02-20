"use client";
import { use } from "react";
import Link from "next/link";
import { StockDetailPanel } from "@/components/watchlist/StockDetailPanel";
import { IVAnalyticsPanel } from "@/components/watchlist/IVAnalyticsPanel";
import { OptionsPanel } from "@/components/market/OptionsPanel";
import { GenerateReportButton } from "@/components/reports/GenerateReportButton";

interface Props {
  params: Promise<{ ticker: string }>;
}

export default function StockDetailPage({ params }: Props) {
  const { ticker } = use(params);

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Link href="/watchlist" className="text-gray-500 hover:text-gray-700 text-sm">
            ← Watchlist
          </Link>
          <h1 className="text-lg font-bold text-blue-600 font-mono">{ticker.toUpperCase()}</h1>
        </div>
        <GenerateReportButton
          type="research"
          ticker={ticker.toUpperCase()}
          label={`Generate ${ticker.toUpperCase()} Report`}
        />
      </div>
      <div className="space-y-6">
        <IVAnalyticsPanel ticker={ticker.toUpperCase()} />
        <OptionsPanel ticker={ticker.toUpperCase()} />
        <StockDetailPanel ticker={ticker.toUpperCase()} />
      </div>
    </div>
  );
}
