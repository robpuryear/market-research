"use client";
import { useStockDetail } from "@/hooks/useWatchlist";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import { ChangeText } from "@/components/ui/Badge";
import { formatCurrency, formatPct, formatDate } from "@/lib/formatters";
import { InfoIcon } from "@/components/ui/Tooltip";
import { TOOLTIPS } from "@/lib/tooltips";

function MetricCard({ label, value, tooltip }: { label: string; value: string; tooltip?: string }) {
  return (
    <div className="bg-white border border-gray-300 rounded p-3">
      <div className="text-xs text-gray-500 uppercase tracking-wide mb-1 flex items-center gap-1">
        {label}
        {tooltip && <InfoIcon tooltip={tooltip} />}
      </div>
      <div className="text-sm font-bold text-gray-800 font-mono">{value}</div>
    </div>
  );
}

export function StockDetailPanel({ ticker }: { ticker: string }) {
  const { data, isLoading, error } = useStockDetail(ticker);

  if (isLoading) return <LoadingSpinner />;
  if (error) return <div className="text-red-600 text-sm p-4">{error.message}</div>;
  if (!data) return null;

  const upside = data.price_target && data.price
    ? ((data.price_target / data.price - 1) * 100)
    : null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white border border-gray-300 rounded-lg p-6">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-xl font-bold text-gray-900 font-mono">{data.company_name}</h2>
            <div className="text-gray-500 text-sm mt-1">{data.sector} · {data.industry}</div>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold text-gray-900 font-mono">${data.price.toFixed(2)}</div>
            <ChangeText value={data.change_pct} />
          </div>
        </div>
      </div>

      {/* Fundamentals grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <MetricCard label="Market Cap" value={formatCurrency(data.market_cap)} tooltip={TOOLTIPS.marketCap} />
        <MetricCard label="P/E Ratio" value={data.pe_ratio?.toFixed(1) ?? "—"} tooltip={TOOLTIPS.pe} />
        <MetricCard label="Forward P/E" value={data.forward_pe?.toFixed(1) ?? "—"} tooltip={TOOLTIPS.pe} />
        <MetricCard label="P/B Ratio" value={data.pb_ratio?.toFixed(2) ?? "—"} />
        <MetricCard label="Debt/Equity" value={data.debt_to_equity?.toFixed(1) ?? "—"} />
        <MetricCard label="Rev Growth" value={data.revenue_growth != null ? formatPct(data.revenue_growth * 100) : "—"} />
        <MetricCard label="Short Interest" value={data.short_interest_pct != null ? `${(data.short_interest_pct * 100).toFixed(1)}%` : "—"} tooltip={TOOLTIPS.shortInterest} />
        <MetricCard label="Institutional" value={data.institutional_ownership_pct != null ? `${(data.institutional_ownership_pct * 100).toFixed(1)}%` : "—"} />
      </div>

      {/* Analyst */}
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-white border border-gray-300 rounded-lg p-4">
          <div className="text-xs text-gray-500 uppercase tracking-wide mb-2 flex items-center gap-1">
            Consensus Rating <InfoIcon tooltip={TOOLTIPS.analystRating} />
          </div>
          <div className="text-lg font-bold text-gray-800">{data.analyst_rating || "—"}</div>
        </div>
        <div className="bg-white border border-gray-300 rounded-lg p-4">
          <div className="text-xs text-gray-500 uppercase tracking-wide mb-2">Price Target</div>
          <div className="text-lg font-bold text-gray-800">{data.price_target ? `$${data.price_target.toFixed(2)}` : "—"}</div>
          {upside != null && (
            <div className={`text-xs mt-1 ${upside >= 0 ? "text-green-600" : "text-red-600"}`}>
              {upside >= 0 ? "+" : ""}{upside.toFixed(1)}% upside
            </div>
          )}
        </div>
        <div className="bg-white border border-gray-300 rounded-lg p-4">
          <div className="text-xs text-gray-500 uppercase tracking-wide mb-2 flex items-center gap-1">
            Next Earnings <InfoIcon tooltip={TOOLTIPS.earningsDate} />
          </div>
          <div className="text-lg font-bold text-gray-800">{formatDate(data.earnings_date)}</div>
        </div>
      </div>

      {/* Financial Health */}
      <div className="bg-white border border-gray-300 rounded-lg p-5">
        <div className="text-xs font-semibold text-gray-700 uppercase tracking-widest mb-3">Financial Health</div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <MetricCard label="Profit Margin" value={data.profit_margin != null ? `${(data.profit_margin * 100).toFixed(1)}%` : "—"} />
          <MetricCard label="Return on Equity" value={data.return_on_equity != null ? `${(data.return_on_equity * 100).toFixed(1)}%` : "—"} />
          <MetricCard label="Return on Assets" value={data.return_on_assets != null ? `${(data.return_on_assets * 100).toFixed(1)}%` : "—"} />
          <MetricCard label="Dividend Yield" value={data.dividend_yield != null ? `${(data.dividend_yield * 100).toFixed(2)}%` : "—"} />
          <MetricCard label="Free Cash Flow" value={formatCurrency(data.free_cash_flow)} />
          <MetricCard label="52W High" value={data.week_52_high != null ? `$${data.week_52_high.toFixed(2)}` : "—"} />
          <MetricCard label="52W Low" value={data.week_52_low != null ? `$${data.week_52_low.toFixed(2)}` : "—"} />
          <MetricCard
            label="52W Position"
            value={data.week_52_high && data.week_52_low && data.price
              ? `${(((data.price - data.week_52_low) / (data.week_52_high - data.week_52_low)) * 100).toFixed(0)}%`
              : "—"}
          />
        </div>
      </div>

      {/* Earnings History */}
      {data.earnings_history && data.earnings_history.length > 0 && (
        <div className="bg-white border border-gray-300 rounded-lg p-4">
          <div className="text-xs text-gray-500 uppercase tracking-wide mb-3">Earnings History (Last 8 Quarters)</div>
          <table className="w-full text-xs font-mono">
            <thead>
              <tr className="text-gray-500 border-b border-gray-300">
                <th className="text-left pb-2">Date</th>
                <th className="text-right pb-2">EPS Est.</th>
                <th className="text-right pb-2">EPS Actual</th>
                <th className="text-right pb-2">Surprise</th>
              </tr>
            </thead>
            <tbody>
              {data.earnings_history.map((e, i) => {
                const surprisePct = e.surprise_pct != null ? e.surprise_pct * 100 : null;
                const surpriseColor = surprisePct == null ? "text-gray-500" : surprisePct > 0 ? "text-green-600" : "text-red-600";
                return (
                  <tr key={i} className="border-b border-gray-300">
                    <td className="py-1.5 text-gray-500">{e.date}</td>
                    <td className="py-1.5 text-right text-gray-500">{e.eps_estimate != null ? `$${e.eps_estimate.toFixed(2)}` : "—"}</td>
                    <td className="py-1.5 text-right text-gray-700">{e.eps_actual != null ? `$${e.eps_actual.toFixed(2)}` : "—"}</td>
                    <td className={`py-1.5 text-right font-bold ${surpriseColor}`}>
                      {surprisePct != null ? `${surprisePct >= 0 ? "+" : ""}${surprisePct.toFixed(1)}%` : "—"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Insider transactions */}
      {data.insider_transactions && data.insider_transactions.length > 0 && (
        <div className="bg-white border border-gray-300 rounded-lg p-4">
          <div className="text-xs text-gray-500 uppercase tracking-wide mb-3">Recent Insider Transactions</div>
          <table className="w-full text-xs font-mono">
            <thead>
              <tr className="text-gray-500 border-b border-gray-300">
                <th className="text-left pb-2">Insider</th>
                <th className="text-left pb-2">Transaction</th>
                <th className="text-right pb-2">Shares</th>
                <th className="text-right pb-2">Value</th>
                <th className="text-right pb-2">Date</th>
              </tr>
            </thead>
            <tbody>
              {data.insider_transactions.map((t, i) => {
                const isBuy = t.transaction.toLowerCase().includes("buy") || t.transaction.toLowerCase().includes("purchase");
                return (
                  <tr key={i} className="border-b border-gray-300">
                    <td className="py-1.5 text-gray-700">{t.name}</td>
                    <td className={`py-1.5 ${isBuy ? "text-green-600" : "text-red-600"}`}>{t.transaction}</td>
                    <td className="py-1.5 text-right text-gray-500">{t.shares.toLocaleString()}</td>
                    <td className="py-1.5 text-right text-gray-500">{formatCurrency(t.value)}</td>
                    <td className="py-1.5 text-right text-gray-500">{t.date}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Unusual options */}
      {data.unusual_options && data.unusual_options.length > 0 && (
        <div className="bg-white border border-gray-300 rounded-lg p-4">
          <div className="text-xs text-gray-500 uppercase tracking-wide mb-3">Unusual Options Flow</div>
          <table className="w-full text-xs font-mono">
            <thead>
              <tr className="text-gray-500 border-b border-gray-300">
                <th className="text-left pb-2">Type</th>
                <th className="text-right pb-2">Strike</th>
                <th className="text-right pb-2">Expiry</th>
                <th className="text-right pb-2">Volume</th>
                <th className="text-right pb-2">OI</th>
                <th className="text-right pb-2">Ratio</th>
                <th className="text-right pb-2">Premium</th>
              </tr>
            </thead>
            <tbody>
              {data.unusual_options.map((f, i) => (
                <tr key={i} className="border-b border-gray-300">
                  <td className={`py-1.5 font-bold ${f.option_type === "call" ? "text-green-600" : "text-red-600"}`}>
                    {f.option_type.toUpperCase()}
                  </td>
                  <td className="py-1.5 text-right text-gray-700">${f.strike.toFixed(2)}</td>
                  <td className="py-1.5 text-right text-gray-500">{f.expiry}</td>
                  <td className="py-1.5 text-right text-gray-500">{f.volume.toLocaleString()}</td>
                  <td className="py-1.5 text-right text-gray-500">{f.open_interest.toLocaleString()}</td>
                  <td className="py-1.5 text-right text-amber-600">{f.volume_oi_ratio.toFixed(1)}x</td>
                  <td className="py-1.5 text-right text-green-600">
                    {f.premium_total >= 1e6 ? `$${(f.premium_total / 1e6).toFixed(2)}M` : `$${(f.premium_total / 1000).toFixed(1)}K`}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
