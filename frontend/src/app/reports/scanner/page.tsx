import { Suspense } from "react";
import { ScannerReportView } from "./ScannerReportView";

export default function ScannerReportPage() {
  return (
    <Suspense fallback={<div className="p-6 text-center">Loading report...</div>}>
      <ScannerReportView />
    </Suspense>
  );
}
