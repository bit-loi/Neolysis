export default function Loading() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 py-8">
        <div className="h-4 w-48 bg-gray-200 rounded animate-pulse mb-6" />
        
        <div className="space-y-6">
          <div className="bg-white rounded-xl border border-gray-200 p-6 animate-pulse">
            <div className="h-8 w-1/3 bg-gray-200 rounded mb-4" />
            <div className="h-4 w-24 bg-gray-100 rounded mb-6" />
            <div className="flex gap-6">
              <div className="w-48 h-48 bg-gray-200 rounded-lg" />
              <div className="flex-grow space-y-3">
                <div className="h-4 w-full bg-gray-100 rounded" />
                <div className="h-4 w-3/4 bg-gray-100 rounded" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
