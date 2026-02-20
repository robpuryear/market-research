import { clsx } from "clsx";

type BadgeVariant =
  | "bull" | "bear" | "neutral" | "volatile"
  | "low" | "elevated" | "high" | "extreme"
  | "positive" | "negative"
  | "call" | "put"
  | "default";

const variantStyles: Record<BadgeVariant, string> = {
  bull: "bg-green-100 text-green-700",
  bear: "bg-red-100 text-red-700",
  neutral: "bg-gray-100 text-gray-700",
  volatile: "bg-orange-100 text-orange-700",
  low: "bg-green-100 text-green-700",
  elevated: "bg-yellow-100 text-yellow-700",
  high: "bg-red-100 text-red-700",
  extreme: "bg-red-50 text-red-700",
  positive: "bg-green-100 text-green-700",
  negative: "bg-red-100 text-red-700",
  call: "bg-green-100 text-green-700",
  put: "bg-red-100 text-red-700",
  default: "bg-purple-100 text-purple-700",
};

interface BadgeProps {
  variant?: BadgeVariant;
  children: React.ReactNode;
  className?: string;
}

export function Badge({ variant = "default", children, className }: BadgeProps) {
  return (
    <span
      className={clsx(
        "inline-block px-2 py-0.5 rounded text-xs font-bold uppercase tracking-wide",
        variantStyles[variant],
        className
      )}
    >
      {children}
    </span>
  );
}

export function ChangeText({ value }: { value: number | null }) {
  if (value == null) return <span className="text-gray-500">—</span>;
  const positive = value >= 0;
  return (
    <span className={positive ? "text-green-600" : "text-red-600"}>
      {positive ? "+" : ""}{value.toFixed(2)}%
    </span>
  );
}
