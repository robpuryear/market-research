"use client";

import { useState } from "react";
import type { Strategy } from "@/lib/types";

interface StrategyCardProps {
  strategy: Strategy;
  onRun: (id: string) => Promise<void>;
  onToggle: (id: string, enabled: boolean) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
  onViewResults: (id: string) => void;
}

export function StrategyCard({ strategy, onRun, onToggle, onDelete, onViewResults }: StrategyCardProps) {
  const [isRunning, setIsRunning] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const handleRun = async () => {
    setIsRunning(true);
    try {
      await onRun(strategy.id);
    } finally {
      setIsRunning(false);
    }
  };

  const handleToggle = async () => {
    await onToggle(strategy.id, !strategy.enabled);
  };

  const handleDelete = async () => {
    if (!confirm(`Are you sure you want to delete strategy "${strategy.name}"?`)) {
      return;
    }
    setIsDeleting(true);
    try {
      await onDelete(strategy.id);
    } finally {
      setIsDeleting(false);
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return "Never";
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
    return `${Math.floor(diffMins / 1440)}d ago`;
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="font-semibold text-gray-900">{strategy.name}</h3>
            <span
              className={`px-2 py-0.5 text-xs rounded-full ${
                strategy.enabled
                  ? "bg-green-100 text-green-700"
                  : "bg-gray-100 text-gray-600"
              }`}
            >
              {strategy.enabled ? "Active" : "Disabled"}
            </span>
            {strategy.generate_alerts && (
              <span className="px-2 py-0.5 text-xs bg-blue-100 text-blue-700 rounded-full">
                Alerts
              </span>
            )}
          </div>
          {strategy.description && (
            <p className="text-sm text-gray-600">{strategy.description}</p>
          )}
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mb-4 p-3 bg-gray-50 rounded">
        <div>
          <p className="text-xs text-gray-500">Scope</p>
          <p className="text-sm font-medium text-gray-900 capitalize">{strategy.scope}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Today</p>
          <p className="text-sm font-medium text-gray-900">{strategy.hits_today} hits</p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Total</p>
          <p className="text-sm font-medium text-gray-900">{strategy.total_hits} hits</p>
        </div>
      </div>

      {/* Conditions summary */}
      <div className="mb-4 text-sm">
        <p className="text-gray-600">
          <span className="font-medium">Entry:</span> {strategy.entry_conditions.conditions.length} condition(s) • {strategy.entry_conditions.logic}
        </p>
        {strategy.exit_conditions && (
          <p className="text-gray-600">
            <span className="font-medium">Exit:</span> {strategy.exit_conditions.conditions.length} condition(s) • {strategy.exit_conditions.logic}
          </p>
        )}
      </div>

      {/* Last run */}
      <div className="mb-4 text-xs text-gray-500">
        Last run: {formatDate(strategy.last_run)}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2">
        <button
          onClick={handleRun}
          disabled={isRunning}
          className="flex-1 px-3 py-2 bg-blue-500 text-white text-sm rounded hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isRunning ? "Running..." : "Run Now"}
        </button>
        <button
          onClick={() => onViewResults(strategy.id)}
          className="px-3 py-2 text-sm text-blue-600 hover:bg-blue-50 border border-blue-200 rounded"
        >
          Results
        </button>
        <button
          onClick={handleToggle}
          className={`px-3 py-2 text-sm rounded border ${
            strategy.enabled
              ? "text-gray-600 hover:bg-gray-50 border-gray-300"
              : "text-green-600 hover:bg-green-50 border-green-300"
          }`}
        >
          {strategy.enabled ? "Disable" : "Enable"}
        </button>
        <button
          onClick={handleDelete}
          disabled={isDeleting}
          className="px-3 py-2 text-sm text-red-600 hover:bg-red-50 border border-red-200 rounded disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Delete
        </button>
      </div>
    </div>
  );
}
