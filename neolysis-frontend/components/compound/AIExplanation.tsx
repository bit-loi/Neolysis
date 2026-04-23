'use client';

import { useEffect, useState } from 'react';
import { Brain } from 'lucide-react';
import { ProteinTarget, CompoundWithDocking } from '@/lib/types';
import Lottie from 'lottie-react';
import loadingAnimation from '@/public/Sandy Loading.json';

interface AIExplanationProps {
  target: ProteinTarget;
  compound: CompoundWithDocking;
}

interface AIInsight {
  text: string;
}

export function AIExplanation({ target, compound }: AIExplanationProps) {
  const [insight, setInsight] = useState<AIInsight | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchInsight() {
      setIsLoading(true);
      setError(null);
      
      try {
        const response = await fetch('/api/insight', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            targetId: target.id,
            compoundCid: compound.cid,
          }),
        });

        if (!response.ok) throw new Error('Failed to fetch insight');
        
        const data = await response.json();
        setInsight(data);
      } catch (err) {
        setError('Unable to load AI insight. Please try again.');
      } finally {
        setIsLoading(false);
      }
    }

    fetchInsight();
  }, [target.id, compound.cid]);

  return (
    <div className="bg-white rounded-xl border-l-4 border-teal-500 shadow-sm">
      <div className="p-6">
        <div className="flex items-center gap-2 mb-4">
          <Brain className="h-5 w-5 text-teal-600" />
          <h2 className="text-xl font-bold text-gray-900">AI Research Insight</h2>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <div className="text-center flex flex-col items-center">
              <div className="w-32 h-32 mb-2">
                <Lottie animationData={loadingAnimation} loop={true} />
              </div>
              <p className="text-sm text-gray-500 font-medium">Synthesizing narrative with Gemma 4...</p>
            </div>
          </div>
        ) : error ? (
          <div className="flex items-center gap-2 p-4 bg-red-50 rounded-lg text-red-700">
            <span className="text-sm">{error}</span>
          </div>
        ) : insight ? (
          <div className="space-y-6">
            <div className="text-gray-700 leading-relaxed whitespace-pre-wrap">
              {insight.text}
            </div>
          </div>
        ) : null}

        <div className="mt-6 pt-4 border-t border-gray-200">
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <span className="px-2 py-1 bg-gray-100 rounded">AI-generated structured narrative</span>
            <span>|</span>
            <span>Not clinical advice</span>
          </div>
        </div>
      </div>
    </div>
  );
}
