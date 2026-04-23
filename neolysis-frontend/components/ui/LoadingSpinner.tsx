'use client';

import { Skeleton } from './skeleton';

export function LoadingSpinner({ size = 'md' }: { size?: 'sm' | 'md' | 'lg' | 'xl' }) {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
    xl: 'w-16 h-16'
  };

  return (
    <div className="flex items-center justify-center">
      <div
        className={`${sizeClasses[size]} border-2 border-gray-300 border-t-black rounded-full animate-spin`}
      />
    </div>
  );
}

export function SkeletonCard() {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 flex flex-col space-y-3 shadow-sm">
      <Skeleton className="h-6 w-1/2" />
      <Skeleton className="h-4 w-3/4" />
      <div className="pt-2">
        <Skeleton className="h-3 w-full mb-2" />
        <Skeleton className="h-3 w-2/3" />
      </div>
    </div>
  );
}

export function SkeletonText({ lines = 3 }: { lines?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          className="h-4"
          style={{ width: `${100 - i * 15}%` }}
        />
      ))}
    </div>
  );
}
