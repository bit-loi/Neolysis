'use client';

import { useEffect } from 'react';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center max-w-md mx-auto px-4">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">Something went wrong</h1>
        <p className="text-gray-600 mb-6">
          {error.message || 'An unexpected error occurred. Please try again.'}
        </p>
        <button
          onClick={reset}
          className="px-4 py-2 bg-teal-600 text-white rounded-lg hover:bg-teal-700 transition-colors"
        >
          Try again
        </button>
      </div>
    </div>
  );
}
