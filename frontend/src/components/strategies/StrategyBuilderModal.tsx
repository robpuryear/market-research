"use client";

import { useState } from "react";
import { ConditionBuilder } from "./ConditionBuilder";
import type { ConditionGroup, IndicatorCondition } from "@/lib/types";

interface StrategyBuilderModalProps {
  open: boolean;
  onClose: () => void;
  onCreate: (strategy: {
    name: string;
    description?: string;
    entry_conditions: ConditionGroup;
    exit_conditions?: ConditionGroup;
    enabled?: boolean;
    scope?: "watchlist" | "market";
    generate_alerts?: boolean;
  }) => void;
}

export function StrategyBuilderModal({ open, onClose, onCreate }: StrategyBuilderModalProps) {
  const [step, setStep] = useState(1); // 1: Basic Info, 2: Entry, 3: Exit, 4: Settings
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [enabled, setEnabled] = useState(true);
  const [scope, setScope] = useState<"watchlist" | "market">("watchlist");
  const [generateAlerts, setGenerateAlerts] = useState(false);
  const [includeExit, setIncludeExit] = useState(false);

  const [entryConditions, setEntryConditions] = useState<ConditionGroup>({
    logic: "AND",
    conditions: [
      {
        indicator: "rsi",
        operator: "below",
        value: 30,
      } as IndicatorCondition,
    ],
  });

  const [exitConditions, setExitConditions] = useState<ConditionGroup>({
    logic: "OR",
    conditions: [
      {
        indicator: "rsi",
        operator: "above",
        value: 70,
      } as IndicatorCondition,
    ],
  });

  const handleSubmit = () => {
    onCreate({
      name,
      description: description || undefined,
      entry_conditions: entryConditions,
      exit_conditions: includeExit ? exitConditions : undefined,
      enabled,
      scope,
      generate_alerts: generateAlerts,
    });

    // Reset form
    handleReset();
    onClose();
  };

  const handleReset = () => {
    setStep(1);
    setName("");
    setDescription("");
    setEnabled(true);
    setScope("watchlist");
    setGenerateAlerts(false);
    setIncludeExit(false);
    setEntryConditions({
      logic: "AND",
      conditions: [
        {
          indicator: "rsi",
          operator: "below",
          value: 30,
        } as IndicatorCondition,
      ],
    });
    setExitConditions({
      logic: "OR",
      conditions: [
        {
          indicator: "rsi",
          operator: "above",
          value: 70,
        } as IndicatorCondition,
      ],
    });
  };

  const handleCancel = () => {
    handleReset();
    onClose();
  };

  const canProceed = () => {
    if (step === 1) return name.trim().length > 0;
    if (step === 2) return entryConditions.conditions.length > 0;
    if (step === 3) return !includeExit || exitConditions.conditions.length > 0;
    return true;
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Create Strategy</h2>
              <p className="text-sm text-gray-600 mt-1">
                Step {step} of 4 - {step === 1 ? "Basic Info" : step === 2 ? "Entry Conditions" : step === 3 ? "Exit Conditions" : "Settings"}
              </p>
            </div>
            <button
              onClick={handleCancel}
              className="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>

          {/* Progress indicator */}
          <div className="flex gap-2 mb-6">
            {[1, 2, 3, 4].map((s) => (
              <div
                key={s}
                className={`flex-1 h-2 rounded ${
                  s <= step ? "bg-blue-500" : "bg-gray-200"
                }`}
              />
            ))}
          </div>

          {/* Step 1: Basic Info */}
          {step === 1 && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Strategy Name *
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g., RSI Oversold with Volume Surge"
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  autoFocus
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description (Optional)
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Describe what this strategy does..."
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
          )}

          {/* Step 2: Entry Conditions */}
          {step === 2 && (
            <ConditionBuilder
              conditionGroup={entryConditions}
              onChange={setEntryConditions}
              label="Entry Conditions"
            />
          )}

          {/* Step 3: Exit Conditions */}
          {step === 3 && (
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="includeExit"
                  checked={includeExit}
                  onChange={(e) => setIncludeExit(e.target.checked)}
                  className="w-4 h-4 text-blue-600"
                />
                <label htmlFor="includeExit" className="text-sm font-medium text-gray-700">
                  Include exit conditions (optional)
                </label>
              </div>

              {includeExit && (
                <ConditionBuilder
                  conditionGroup={exitConditions}
                  onChange={setExitConditions}
                  label="Exit Conditions"
                />
              )}

              {!includeExit && (
                <div className="p-4 bg-gray-50 rounded border border-gray-200 text-sm text-gray-600">
                  Exit conditions are optional. If not specified, the strategy will only track entry signals.
                </div>
              )}
            </div>
          )}

          {/* Step 4: Settings */}
          {step === 4 && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Scope
                </label>
                <div className="flex gap-4">
                  <label className="flex items-center gap-2">
                    <input
                      type="radio"
                      value="watchlist"
                      checked={scope === "watchlist"}
                      onChange={(e) => setScope(e.target.value as "watchlist" | "market")}
                      className="w-4 h-4 text-blue-600"
                    />
                    <span className="text-sm">Watchlist only</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input
                      type="radio"
                      value="market"
                      checked={scope === "market"}
                      onChange={(e) => setScope(e.target.value as "watchlist" | "market")}
                      className="w-4 h-4 text-blue-600"
                    />
                    <span className="text-sm">Full market</span>
                  </label>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="enabled"
                  checked={enabled}
                  onChange={(e) => setEnabled(e.target.checked)}
                  className="w-4 h-4 text-blue-600"
                />
                <label htmlFor="enabled" className="text-sm font-medium text-gray-700">
                  Enable strategy immediately
                </label>
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="generateAlerts"
                  checked={generateAlerts}
                  onChange={(e) => setGenerateAlerts(e.target.checked)}
                  className="w-4 h-4 text-blue-600"
                />
                <label htmlFor="generateAlerts" className="text-sm font-medium text-gray-700">
                  Auto-generate alerts when strategy matches
                </label>
              </div>

              {/* Summary */}
              <div className="p-4 bg-blue-50 rounded border border-blue-200">
                <h4 className="font-medium text-blue-900 mb-2">Summary</h4>
                <div className="text-sm text-blue-800 space-y-1">
                  <p><strong>Name:</strong> {name}</p>
                  {description && <p><strong>Description:</strong> {description}</p>}
                  <p><strong>Scope:</strong> {scope === "watchlist" ? "Watchlist only" : "Full market"}</p>
                  <p><strong>Entry Conditions:</strong> {entryConditions.conditions.length} condition(s) with {entryConditions.logic} logic</p>
                  {includeExit && <p><strong>Exit Conditions:</strong> {exitConditions.conditions.length} condition(s) with {exitConditions.logic} logic</p>}
                  <p><strong>Alerts:</strong> {generateAlerts ? "Enabled" : "Disabled"}</p>
                </div>
              </div>
            </div>
          )}

          {/* Footer */}
          <div className="flex items-center justify-between mt-6 pt-4 border-t border-gray-200">
            <button
              onClick={() => setStep(Math.max(1, step - 1))}
              disabled={step === 1}
              className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Back
            </button>

            <div className="flex gap-2">
              <button
                onClick={handleCancel}
                className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded"
              >
                Cancel
              </button>

              {step < 4 ? (
                <button
                  onClick={() => setStep(step + 1)}
                  disabled={!canProceed()}
                  className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next
                </button>
              ) : (
                <button
                  onClick={handleSubmit}
                  disabled={!canProceed()}
                  className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Create Strategy
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
