"use client";

import { useNotifications } from "@/hooks/useNotifications";
import Link from "next/link";

export function NotificationBell() {
  const { unreadCount } = useNotifications(true);

  return (
    <Link
      href="/alerts"
      className="relative flex items-center justify-center w-8 h-8 rounded-full hover:bg-gray-100 transition-colors"
      title={`${unreadCount} unread notifications`}
    >
      {/* Bell Icon */}
      <svg
        className="w-5 h-5 text-gray-600"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
        />
      </svg>

      {/* Badge */}
      {unreadCount > 0 && (
        <span className="absolute -top-1 -right-1 flex items-center justify-center w-5 h-5 text-xs font-bold text-white bg-red-600 rounded-full">
          {unreadCount > 9 ? "9+" : unreadCount}
        </span>
      )}
    </Link>
  );
}
