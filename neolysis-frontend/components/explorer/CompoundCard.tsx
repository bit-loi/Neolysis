'use client';

import Link from 'next/link';
import { ArrowRight, Check, X, AlertTriangle } from 'lucide-react';
import { CompoundWithDocking } from '@/lib/types';
import { motion } from 'framer-motion';
import { AffinityBar } from '@/components/ui/AffinityBar';
import { useState } from 'react';

const fadeInUp = {
  hidden: { opacity: 0, y: 10 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.3, ease: 'easeOut' } }
};

interface CompoundCardProps {
  compound: CompoundWithDocking;
  targetId: string;
  rank?: number;
}

/**
 * Truncate a compound name at a sensible boundary (word or hyphen),
 * never mid-word, with a max length.
 */
function smartTruncate(name: string, maxLen: number): { display: string; truncated: boolean } {
  if (name.length <= maxLen) return { display: name, truncated: false };

  // Find the last hyphen or space before maxLen
  let cutIdx = maxLen;
  for (let i = maxLen; i >= maxLen - 20 && i > 0; i--) {
    if (name[i] === '-' || name[i] === ' ' || name[i] === ',') {
      cutIdx = i;
      break;
    }
  }

  return { display: name.substring(0, cutIdx) + '…', truncated: true };
}

export function CompoundCard({ compound, targetId, rank }: CompoundCardProps) {
  const [showTooltip, setShowTooltip] = useState(false);
  const { display: displayName, truncated } = smartTruncate(compound.name, 50);

  return (
    <motion.div variants={fadeInUp}>
      <Link href={`/compound/${compound.cid}?target=${targetId}`} className="block outline-none font-sans">
        <div className="bg-white border border-gray-200 p-5 hover:border-black hover:shadow-md transition-all cursor-pointer">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-grow min-w-0">
              <div className="flex flex-wrap items-center gap-2 mb-1.5">
                {rank && (
                  <span className="inline-flex items-center justify-center w-6 h-6 bg-black text-white text-xs font-bold rounded-full shrink-0">
                    {rank}
                  </span>
                )}
                <div
                  className="relative"
                  onMouseEnter={() => truncated && setShowTooltip(true)}
                  onMouseLeave={() => setShowTooltip(false)}
                >
                  <h4 className="font-serif font-bold text-lg text-black leading-tight">
                    {displayName}
                  </h4>
                  {showTooltip && (
                    <div className="absolute z-50 bottom-full left-0 mb-2 px-3 py-2 bg-black text-white text-xs rounded shadow-lg max-w-sm whitespace-normal">
                      {compound.name}
                    </div>
                  )}
                </div>
              </div>
              <span className="px-2 py-0.5 bg-white border border-gray-300 text-black text-xs font-mono font-bold">
                CID {compound.cid}
              </span>
            </div>

            <div className="text-right flex-shrink-0">
              <div className="inline-flex items-center gap-1.5 px-3 py-1.5 border bg-white border-gray-300">
                <span className="font-bold text-black">
                  {compound.dockingScore.toFixed(2)}
                </span>
                <span className="text-xs text-gray-700 font-bold">kcal/mol</span>
              </div>
            </div>
          </div>

          <div className="mt-3 mb-3">
            <AffinityBar affinity={compound.dockingScore} size="sm" />
          </div>

          <div className="flex items-center justify-between pt-3 border-t border-gray-200">
            <div className="flex flex-wrap items-center gap-3 text-xs font-bold">
              <span className="text-black bg-white px-2 py-1 border border-gray-300">
                MW: {compound.mw.toFixed(1)}
              </span>
              <span className="text-black bg-white px-2 py-1 border border-gray-300">
                LogP: {compound.logP.toFixed(1)}
              </span>
              {compound.lipinskiPass ? (
                <span className="flex items-center gap-1 text-emerald-700 bg-emerald-50 px-2 py-1 border border-emerald-200">
                  <Check className="h-3 w-3" /> Ro5 Pass
                </span>
              ) : (
                <span className="flex items-center gap-1 text-amber-700 bg-amber-50 px-2 py-1 border border-amber-200">
                  <AlertTriangle className="h-3 w-3" /> Ro5 Flagged
                </span>
              )}
            </div>
            <span className="inline-flex items-center gap-2 text-sm font-bold text-black">
              Analyze
              <ArrowRight className="h-4 w-4" />
            </span>
          </div>
        </div>
      </Link>
    </motion.div>
  );
}