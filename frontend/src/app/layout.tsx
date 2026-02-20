import type { Metadata } from "next";
import "./globals.css";
import { Sidebar } from "@/components/layout/Sidebar";
import { TopBar } from "@/components/layout/TopBar";
import { StatusBar } from "@/components/layout/StatusBar";

export const metadata: Metadata = {
  title: "Market Intelligence",
  description: "Professional stock market intelligence platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="bg-gray-100 text-gray-900 antialiased">
        <div className="flex flex-col h-screen">
          <TopBar />
          <div className="flex flex-1 overflow-hidden">
            <Sidebar />
            <main className="flex-1 overflow-y-auto">
              {children}
            </main>
          </div>
          <StatusBar />
        </div>
      </body>
    </html>
  );
}
