import { format, formatDistanceToNow } from "date-fns";

export function formatCurrency(value: number | null | undefined): string {
  if (value == null) return "—";
  if (Math.abs(value) >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
  if (Math.abs(value) >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
  if (Math.abs(value) >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
  if (Math.abs(value) >= 1e3) return `$${(value / 1e3).toFixed(2)}K`;
  return `$${value.toFixed(2)}`;
}

export function formatPrice(value: number | null | undefined): string {
  if (value == null) return "—";
  return `$${value.toFixed(2)}`;
}

export function formatPct(value: number | null | undefined, decimals = 2): string {
  if (value == null) return "—";
  const sign = value >= 0 ? "+" : "";
  return `${sign}${value.toFixed(decimals)}%`;
}

export function formatVolume(value: number | null | undefined): string {
  if (value == null) return "—";
  if (value >= 1e9) return `${(value / 1e9).toFixed(2)}B`;
  if (value >= 1e6) return `${(value / 1e6).toFixed(2)}M`;
  if (value >= 1e3) return `${(value / 1e3).toFixed(2)}K`;
  return value.toFixed(0);
}

export function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return "—";
  try {
    return format(new Date(dateStr), "MMM d, yyyy");
  } catch {
    return dateStr;
  }
}

export function formatDateTime(dateStr: string | null | undefined): string {
  if (!dateStr) return "—";
  try {
    return format(new Date(dateStr), "MMM d, yyyy HH:mm");
  } catch {
    return dateStr;
  }
}

export function timeAgo(dateStr: string | null | undefined): string {
  if (!dateStr) return "—";
  try {
    return formatDistanceToNow(new Date(dateStr), { addSuffix: true });
  } catch {
    return dateStr;
  }
}

export function formatMultiplier(value: number | null | undefined): string {
  if (value == null) return "—";
  return `${value.toFixed(1)}x`;
}
