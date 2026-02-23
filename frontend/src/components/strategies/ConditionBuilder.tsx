"use client";

import { ConditionRow } from "./ConditionRow";
import type { ConditionGroup, Condition, IndicatorCondition } from "@/lib/types";

interface ConditionBuilderProps {
  conditionGroup: ConditionGroup;
  onChange: (group: ConditionGroup) => void;
  label: string;
}

export function ConditionBuilder({ conditionGroup, onChange, label }: ConditionBuilderProps) {
  const handleLogicChange = (logic: "AND" | "OR") => {
    onChange({ ...conditionGroup, logic });
  };

  const handleConditionChange = (index: number, condition: Condition) => {
    const newConditions = [...conditionGroup.conditions];
    newConditions[index] = condition;
    onChange({ ...conditionGroup, conditions: newConditions });
  };

  const handleAddCondition = () => {
    const newCondition: IndicatorCondition = {
      indicator: "rsi",
      operator: "below",
      value: 30,
    };
    onChange({
      ...conditionGroup,
      conditions: [...conditionGroup.conditions, newCondition],
    });
  };

  const handleRemoveCondition = (index: number) => {
    const newConditions = conditionGroup.conditions.filter((_, i) => i !== index);
    onChange({ ...conditionGroup, conditions: newConditions });
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="font-medium text-gray-900">{label}</h3>
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-600">Logic:</span>
          <div className="flex gap-1 bg-gray-100 rounded p-1">
            <button
              type="button"
              onClick={() => handleLogicChange("AND")}
              className={`px-3 py-1 text-sm rounded ${
                conditionGroup.logic === "AND"
                  ? "bg-blue-500 text-white"
                  : "text-gray-600 hover:bg-gray-200"
              }`}
            >
              AND
            </button>
            <button
              type="button"
              onClick={() => handleLogicChange("OR")}
              className={`px-3 py-1 text-sm rounded ${
                conditionGroup.logic === "OR"
                  ? "bg-blue-500 text-white"
                  : "text-gray-600 hover:bg-gray-200"
              }`}
            >
              OR
            </button>
          </div>
        </div>
      </div>

      <div className="space-y-2">
        {conditionGroup.conditions.map((condition, index) => (
          <ConditionRow
            key={index}
            condition={condition}
            onChange={(newCondition) => handleConditionChange(index, newCondition)}
            onRemove={() => handleRemoveCondition(index)}
            showRemove={conditionGroup.conditions.length > 1}
          />
        ))}
      </div>

      <button
        type="button"
        onClick={handleAddCondition}
        className="w-full px-4 py-2 text-sm text-blue-600 hover:bg-blue-50 border border-blue-200 rounded"
      >
        + Add Condition
      </button>

      {/* Live preview */}
      <div className="p-3 bg-blue-50 rounded border border-blue-200">
        <p className="text-xs font-medium text-blue-900 mb-1">Summary:</p>
        <p className="text-sm text-blue-800">
          {conditionGroup.conditions.length === 0 && "No conditions set"}
          {conditionGroup.conditions.map((cond, idx) => {
            let summary = "";
            if ("indicator" in cond) {
              const ind = cond as IndicatorCondition;
              summary = `${ind.indicator.toUpperCase()} ${ind.operator.replace("_", " ")} ${ind.value ?? "?"}`;
              if (ind.period) summary += ` (${ind.period} period)`;
            } else {
              summary = `${cond.pattern.replace("_", " ")}${cond.direction ? ` (${cond.direction})` : ""}`;
            }
            return (
              <span key={idx}>
                {summary}
                {idx < conditionGroup.conditions.length - 1 && (
                  <span className="mx-2 font-bold">{conditionGroup.logic}</span>
                )}
              </span>
            );
          })}
        </p>
      </div>
    </div>
  );
}
