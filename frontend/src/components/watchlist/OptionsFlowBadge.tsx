interface OptionsFlowBadgeProps {
  isUnusual: boolean;
}

export function OptionsFlowBadge({ isUnusual }: OptionsFlowBadgeProps) {
  if (!isUnusual) return null;
  return (
    <span className="inline-flex items-center gap-1 bg-yellow-100/50 text-yellow-700 text-xs px-2 py-0.5 rounded border border-yellow-200">
      ⚡ Unusual Flow
    </span>
  );
}
