"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { clsx } from "clsx";

const NAV_ITEMS = [
  { href: "/", label: "Dashboard", icon: "◈" },
  { href: "/market", label: "Market", icon: "▦" },
  { href: "/watchlist", label: "Watchlist", icon: "◉" },
  { href: "/analytics", label: "Analytics", icon: "◎" },
  { href: "/scanner", label: "Scanner", icon: "🔍" },
  { href: "/sentiment", label: "Sentiment", icon: "◆" },
  { href: "/reports", label: "Reports", icon: "▣" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-52 min-h-screen bg-gray-50 border-r border-gray-300 flex flex-col">
      <div className="p-4 border-b border-gray-300">
        <div className="text-blue-600 font-bold text-sm tracking-widest font-mono">
          ▸ MARKET INTEL
        </div>
        <div className="text-gray-500 text-xs mt-0.5">v1.0.0</div>
      </div>

      <nav className="flex-1 p-3 space-y-1">
        {NAV_ITEMS.map((item) => {
          const active =
            item.href === "/"
              ? pathname === "/"
              : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={clsx(
                "flex items-center gap-3 px-3 py-2 rounded text-sm font-mono transition-colors",
                active
                  ? "bg-blue-50 text-blue-700 border border-blue-200"
                  : "text-gray-500 hover:text-gray-800 hover:bg-gray-50"
              )}
            >
              <span className="text-base">{item.icon}</span>
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="p-3 border-t border-gray-300">
        <div className="text-xs text-gray-500 font-mono">
          Data: yfinance, PRAW
        </div>
        <div className="text-xs text-gray-600 mt-0.5">
          Not financial advice
        </div>
      </div>
    </aside>
  );
}
