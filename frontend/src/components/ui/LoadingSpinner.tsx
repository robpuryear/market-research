export function LoadingSpinner({ size = "md" }: { size?: "sm" | "md" | "lg" }) {
  const sizes = { sm: "h-4 w-4", md: "h-8 w-8", lg: "h-12 w-12" };
  return (
    <div className="flex items-center justify-center p-8">
      <div
        className={`${sizes[size]} border-2 border-gray-300 border-t-blue-600 rounded-full animate-spin`}
      />
    </div>
  );
}

export function LoadingCard() {
  return (
    <div className="bg-white border border-gray-300 rounded-lg p-4 animate-pulse">
      <div className="h-3 bg-gray-100 rounded w-1/3 mb-3" />
      <div className="h-6 bg-gray-100 rounded w-1/2" />
    </div>
  );
}
