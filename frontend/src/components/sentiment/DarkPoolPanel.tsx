export function DarkPoolPanel() {
  return (
    <div className="bg-white border border-gray-300 rounded-lg p-4">
      <div className="text-xs text-gray-500 uppercase tracking-wide mb-3">Dark Pool Activity</div>
      <div className="text-gray-500 text-sm">
        <div className="mb-2">🔒 Requires Polygon.io premium access</div>
        <div className="text-xs text-gray-500">
          Configure <code className="bg-gray-100 px-1 rounded">POLYGON_API_KEY</code> in .env to enable dark pool tracking.
        </div>
      </div>
    </div>
  );
}
