import { Skeleton } from '@/components/ui/skeleton';

export default function Loading() {
  return (
    <div className="min-h-screen bg-[#f5f5f0] pt-24 pb-16 px-4 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl animate-pulse">
        {/* Header Skeleton */}
        <div className="flex flex-col items-center mb-12">
          <Skeleton className="h-12 w-64 mb-4" />
          <Skeleton className="h-6 w-96 max-w-full" />
        </div>

        {/* Content Tabs / Filters Skeleton */}
        <div className="flex justify-center gap-3 mb-12">
          <Skeleton className="h-10 w-24" />
          <Skeleton className="h-10 w-32" />
          <Skeleton className="h-10 w-28" />
          <Skeleton className="h-10 w-24" />
        </div>

        {/* Grid content Skeleton */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="bg-white border border-gray-200 p-8 flex flex-col h-64">
              <Skeleton className="h-8 w-3/4 mb-4" />
              <Skeleton className="h-4 w-1/4 mb-6" />
              <div className="space-y-2 flex-grow">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-2/3" />
              </div>
              <div className="flex justify-between items-center mt-6 pt-6 border-t border-gray-100">
                <Skeleton className="h-6 w-24" />
                <Skeleton className="h-4 w-16" />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
