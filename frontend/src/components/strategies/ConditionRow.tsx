"use client";

import type { Condition, IndicatorCondition, PricePatternCondition } from "@/lib/types";

interface ConditionRowProps {
  condition: Condition;
  onChange: (condition: Condition) => void;
  onRemove: () => void;
  showRemove: boolean;
}

export function ConditionRow({ condition, onChange, onRemove, showRemove }: ConditionRowProps) {
  const isIndicator = "indicator" in condition;

  // Type guard
  const indicatorCond = isIndicator ? (condition as IndicatorCondition) : null;
  const patternCond = !isIndicator ? (condition as PricePatternCondition) : null;

  const handleIndicatorChange = (field: keyof IndicatorCondition, value: string | number | undefined) => {
    if (!indicatorCond) return;
    onChange({ ...indicatorCond, [field]: value });
  };

  const handlePatternChange = (field: keyof PricePatternCondition, value: string | undefined) => {
    if (!patternCond) return;
    onChange({ ...patternCond, [field]: value });
  };

  const handleTypeChange = (newType: "indicator" | "pattern") => {
    if (newType === "indicator") {
      onChange({
        indicator: "rsi",
        operator: "below",
        value: 30,
      } as IndicatorCondition);
    } else {
      onChange({
        pattern: "golden_cross",
      } as PricePatternCondition);
    }
  };

  return (
    <div className="flex items-start gap-2 p-3 bg-gray-50 rounded border border-gray-200">
      <div className="flex-1 grid grid-cols-1 gap-2">
        {/* Type selector */}
        <div className="flex gap-2">
          <select
            value={isIndicator ? "indicator" : "pattern"}
            onChange={(e) => handleTypeChange(e.target.value as "indicator" | "pattern")}
            className="px-2 py-1 border border-gray-300 rounded text-sm"
          >
            <option value="indicator">Indicator</option>
            <option value="pattern">Pattern</option>
          </select>
        </div>

        {/* Indicator fields */}
        {isIndicator && indicatorCond && (
          <div className="grid grid-cols-3 gap-2">
            <select
              value={indicatorCond.indicator}
              onChange={(e) => handleIndicatorChange("indicator", e.target.value)}
              className="px-2 py-1 border border-gray-300 rounded text-sm"
            >
              <option value="rsi">RSI</option>
              <option value="macd">MACD</option>
              <option value="ma">Moving Average</option>
              <option value="bb">Bollinger Bands</option>
              <option value="volume">Volume</option>
              <option value="price">Price</option>
            </select>

            <select
              value={indicatorCond.operator}
              onChange={(e) => handleIndicatorChange("operator", e.target.value)}
              className="px-2 py-1 border border-gray-300 rounded text-sm"
            >
              <option value="above">Above</option>
              <option value="below">Below</option>
              <option value="crosses_above">Crosses Above</option>
              <option value="crosses_below">Crosses Below</option>
              <option value="between">Between</option>
            </select>

            <input
              type="number"
              step="any"
              value={indicatorCond.value ?? ""}
              onChange={(e) => handleIndicatorChange("value", e.target.value ? parseFloat(e.target.value) : undefined)}
              placeholder="Value"
              className="px-2 py-1 border border-gray-300 rounded text-sm"
            />

            {indicatorCond.operator === "between" && (
              <input
                type="number"
                step="any"
                value={indicatorCond.value_high ?? ""}
                onChange={(e) => handleIndicatorChange("value_high", e.target.value ? parseFloat(e.target.value) : undefined)}
                placeholder="High value"
                className="px-2 py-1 border border-gray-300 rounded text-sm col-start-3"
              />
            )}

            {(indicatorCond.indicator === "ma" || indicatorCond.indicator === "rsi") && (
              <input
                type="number"
                value={indicatorCond.period ?? ""}
                onChange={(e) => handleIndicatorChange("period", e.target.value ? parseInt(e.target.value) : undefined)}
                placeholder="Period"
                className="px-2 py-1 border border-gray-300 rounded text-sm col-start-3"
              />
            )}
          </div>
        )}

        {/* Pattern fields */}
        {!isIndicator && patternCond && (
          <div className="grid grid-cols-2 gap-2">
            <select
              value={patternCond.pattern}
              onChange={(e) => handlePatternChange("pattern", e.target.value)}
              className="px-2 py-1 border border-gray-300 rounded text-sm"
            >
              <option value="golden_cross">Golden Cross</option>
              <option value="death_cross">Death Cross</option>
              <option value="macd_cross">MACD Cross</option>
              <option value="bb_squeeze">BB Squeeze</option>
            </select>

            {patternCond.pattern === "macd_cross" && (
              <select
                value={patternCond.direction ?? ""}
                onChange={(e) => handlePatternChange("direction", e.target.value || undefined)}
                className="px-2 py-1 border border-gray-300 rounded text-sm"
              >
                <option value="">Any</option>
                <option value="bullish">Bullish</option>
                <option value="bearish">Bearish</option>
              </select>
            )}
          </div>
        )}
      </div>

      {/* Remove button */}
      {showRemove && (
        <button
          type="button"
          onClick={onRemove}
          className="px-2 py-1 text-red-600 hover:bg-red-50 rounded text-sm"
        >
          ✕
        </button>
      )}
    </div>
  );
}
