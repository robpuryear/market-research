"use client";

import { useState } from "react";
import type { PriceCondition, SignalCondition, EarningsCondition } from "@/lib/types";

interface CreateAlertModalProps {
  open: boolean;
  onClose: () => void;
  onCreate: (alert: {
    ticker: string;
    alert_type: string;
    condition: PriceCondition | SignalCondition | EarningsCondition;
    notification_methods: string[];
    message?: string;
  }) => void;
  defaultTicker?: string;
}

export function CreateAlertModal({ open, onClose, onCreate, defaultTicker = "" }: CreateAlertModalProps) {
  const [ticker, setTicker] = useState(defaultTicker);
  const [alertType, setAlertType] = useState<"price" | "signal" | "earnings">("price");
  const [message, setMessage] = useState("");

  // Price condition fields
  const [priceCondType, setPriceCondType] = useState<"above" | "below" | "pct_change">("above");
  const [priceThreshold, setPriceThreshold] = useState("");
  const [pctChange, setPctChange] = useState("");

  // Signal condition fields
  const [signalType, setSignalType] = useState<"rsi" | "ml_signal">("rsi");
  const [rsiOperator, setRsiOperator] = useState<"above" | "below">("below");
  const [rsiThreshold, setRsiThreshold] = useState("30");
  const [mlDirection, setMlDirection] = useState<"bullish" | "bearish" | "">("bullish");

  // Earnings condition fields
  const [daysBefore, setDaysBefore] = useState("1");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    let condition: PriceCondition | SignalCondition | EarningsCondition;

    if (alertType === "price") {
      if (priceCondType === "pct_change") {
        condition = {
          condition_type: "pct_change",
          percentage: parseFloat(pctChange),
        };
      } else {
        condition = {
          condition_type: priceCondType,
          threshold: parseFloat(priceThreshold),
        };
      }
    } else if (alertType === "signal") {
      if (signalType === "rsi") {
        condition = {
          signal_type: "rsi",
          operator: rsiOperator,
          threshold: parseFloat(rsiThreshold),
        };
      } else {
        condition = {
          signal_type: "ml_signal",
          operator: "fired",
          direction: mlDirection || undefined,
        };
      }
    } else {
      // Earnings alert
      condition = {
        days_before: parseInt(daysBefore),
        notify_on_surprise: false,
        surprise_threshold: 10,
      };
    }

    onCreate({
      ticker: ticker.toUpperCase(),
      alert_type: alertType,
      condition,
      message: message || undefined,
      notification_methods: ["in_app"],
    });

    // Reset form
    setTicker(defaultTicker);
    setMessage("");
    setPriceThreshold("");
    setPctChange("");
    onClose();
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-900">Create Alert</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Ticker */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Ticker</label>
              <input
                type="text"
                value={ticker}
                onChange={(e) => setTicker(e.target.value.toUpperCase())}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="AAPL"
                required
              />
            </div>

            {/* Alert Type */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Alert Type</label>
              <select
                value={alertType}
                onChange={(e) => setAlertType(e.target.value as "price" | "signal" | "earnings")}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="price">Price</option>
                <option value="signal">Signal</option>
                <option value="earnings">Earnings</option>
              </select>
            </div>

            {/* Price Conditions */}
            {alertType === "price" && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Condition</label>
                  <select
                    value={priceCondType}
                    onChange={(e) => setPriceCondType(e.target.value as "above" | "below" | "pct_change")}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="above">Above Price</option>
                    <option value="below">Below Price</option>
                    <option value="pct_change">Percentage Change</option>
                  </select>
                </div>

                {priceCondType === "pct_change" ? (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Percentage (%)</label>
                    <input
                      type="number"
                      value={pctChange}
                      onChange={(e) => setPctChange(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="5"
                      step="0.1"
                      min="0"
                      required
                    />
                    <p className="text-xs text-gray-500 mt-1">Alert when price moves ±{pctChange || "X"}% in a day</p>
                  </div>
                ) : (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Price Threshold ($)</label>
                    <input
                      type="number"
                      value={priceThreshold}
                      onChange={(e) => setPriceThreshold(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="150.00"
                      step="0.01"
                      min="0"
                      required
                    />
                  </div>
                )}
              </>
            )}

            {/* Signal Conditions */}
            {alertType === "signal" && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Signal Type</label>
                  <select
                    value={signalType}
                    onChange={(e) => setSignalType(e.target.value as "rsi" | "ml_signal")}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="rsi">RSI Level</option>
                    <option value="ml_signal">ML Signal</option>
                  </select>
                </div>

                {signalType === "rsi" ? (
                  <>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Operator</label>
                      <select
                        value={rsiOperator}
                        onChange={(e) => setRsiOperator(e.target.value as "above" | "below")}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="below">Below (Oversold)</option>
                        <option value="above">Above (Overbought)</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">RSI Threshold</label>
                      <input
                        type="number"
                        value={rsiThreshold}
                        onChange={(e) => setRsiThreshold(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="30"
                        step="1"
                        min="0"
                        max="100"
                        required
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        Common: 30 (oversold), 70 (overbought)
                      </p>
                    </div>
                  </>
                ) : (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Direction (Optional)</label>
                    <select
                      value={mlDirection}
                      onChange={(e) => setMlDirection(e.target.value as "bullish" | "bearish" | "")}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">Any Direction</option>
                      <option value="bullish">Bullish</option>
                      <option value="bearish">Bearish</option>
                    </select>
                    <p className="text-xs text-gray-500 mt-1">
                      Alert when any ML signal fires
                    </p>
                  </div>
                )}
              </>
            )}

            {/* Earnings Conditions */}
            {alertType === "earnings" && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Days Before Earnings</label>
                <input
                  type="number"
                  value={daysBefore}
                  onChange={(e) => setDaysBefore(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="1"
                  step="1"
                  min="0"
                  max="30"
                  required
                />
                <p className="text-xs text-gray-500 mt-1">
                  Get notified X days before earnings date
                </p>
              </div>
            )}

            {/* Custom Message */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Custom Message (Optional)</label>
              <input
                type="text"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="My custom alert message"
              />
            </div>

            {/* Actions */}
            <div className="flex gap-3 pt-4">
              <button
                type="button"
                onClick={onClose}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors font-medium"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors font-medium"
              >
                Create Alert
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
