import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

export default function Loading() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-xl border border-gray-200 p-6 animate-pulse">
          <div className="h-8 w-1/3 bg-gray-200 rounded mb-4" />
          <div className="h-4 w-1/4 bg-gray-100 rounded mb-4" />
          <div className="space-y-2">
            <div className="h-4 w-full bg-gray-100 rounded" />
            <div className="h-4 w-3/4 bg-gray-100 rounded" />
          </div>
        </div>

        <div className="mt-8 grid grid-cols-1 lg:grid-cols-5 gap-6">
          <div className="lg:col-span-3 bg-gray-200 rounded-xl h-[500px] animate-pulse" />
          <div className="lg:col-span-2 bg-gray-200 rounded-xl h-[500px] animate-pulse" />
        </div>
      </div>
    </div>
  );
}
