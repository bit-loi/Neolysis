'use client';

import { useState } from 'react';
import Link from 'next/link';
import { ArrowRight } from 'lucide-react';
import { motion } from 'framer-motion';
import { AffinityBar } from '@/components/ui/AffinityBar';

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.05
    }
  }
};

interface CSVCompound {
  target: string;
  pocket: number;
  cid: number;
  name: string;
  smiles: string;
  mw: number;
  logp: number;
  affinity: number;
  ligand_eff: number;
  affinity_rank: number;
  le_rank: number;
  composite: number;
  confidence: number;
  explanation?: string;
}

interface CSVCompoundListProps {
  compounds: CSVCompound[];
  targetId: string;
}

export function CSVCompoundList({ compounds, targetId }: CSVCompoundListProps) {
  const [sortBy, setSortBy] = useState<'score' | 'name'>('score');

  const sortedCompounds = [...compounds].sort((a, b) => {
    if (sortBy === 'score') return a.affinity - b.affinity;
    return a.name.localeCompare(b.name);
  });

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.2, ease: 'easeOut' }}
      className="bg-white border border-gray-300 overflow-hidden font-sans"
    >
      <div className="p-6 border-b border-gray-300 bg-[#f5f5f0]">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
          <div className="flex items-center gap-3">
            <h3 className="text-2xl font-serif font-bold text-black">Drug Candidates</h3>
            <span className="px-3 py-1 bg-white border border-gray-400 text-black text-xs font-bold rounded-full">
              {compounds.length} Found
            </span>
          </div>
        </div>

        <div className="flex flex-wrap gap-6">
          <div className="flex items-center gap-3">
            <label className="text-xs font-bold text-black uppercase tracking-wider">Sort by:</label>
            <div className="flex gap-2">
              {(['score', 'name'] as const).map((s) => (
                <button
                  key={s}
                  onClick={() => setSortBy(s)}
                  className={`px-4 py-1.5 text-xs font-bold transition-all border ${
                    sortBy === s
                      ? 'bg-black text-white border-black'
                      : 'bg-white text-gray-800 border-gray-400 hover:border-black hover:text-black'
                  }`}
                >
                  {s === 'score' ? 'Docking Score' : 'Name'}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="max-h-[600px] overflow-y-auto bg-gray-50 custom-scrollbar p-1">
        {compounds.length === 0 ? (
          <div className="p-12 text-center">
            <div className="inline-block p-4 rounded-full bg-white border border-gray-300 mb-4">
              <span className="text-2xl opacity-50">🔬</span>
            </div>
            <p className="text-gray-800 font-medium">No compounds found.</p>
          </div>
        ) : (
          <motion.div 
            variants={staggerContainer}
            initial="hidden"
            animate="visible"
            className="space-y-1"
          >
            {sortedCompounds.map((compound) => (
              <CSVCompoundCard 
                key={compound.cid} 
                compound={compound} 
                targetId={targetId} 
              />
            ))}
          </motion.div>
        )}
      </div>
    </motion.div>
  );
}

function CSVCompoundCard({ compound, targetId }: { compound: CSVCompound; targetId: string }) {
  const getAffinityColor = (affinity: number) => {
    if (affinity < -8) return 'text-green-600';
    if (affinity <= -5) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <motion.div>
      <Link href={`/compound/${compound.cid}?target=${targetId}`} className="block outline-none font-sans">
        <div className="bg-white border border-gray-200 p-5 hover:border-black hover:shadow-md transition-all cursor-pointer">
          <div className="flex items-start justify-between gap-4 mb-3">
            <div className="flex-grow min-w-0">
              <div className="flex flex-wrap items-center gap-2 mb-1">
                <h4 className="font-serif font-bold text-lg text-black truncate">{compound.name}</h4>
              </div>
              <span className="px-2 py-0.5 bg-white border border-gray-300 text-black text-xs font-mono font-bold">
                CID {compound.cid}
              </span>
            </div>

            <div className="text-right flex-shrink-0">
              <div className={`text-2xl font-bold ${getAffinityColor(compound.affinity)}`}>
                {compound.affinity.toFixed(1)}
              </div>
              <span className="text-xs text-gray-600 font-bold">kcal/mol</span>
            </div>
          </div>

          <AffinityBar affinity={compound.affinity} size="sm" />

          <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-200">
            <div className="flex flex-wrap items-center gap-3 text-xs font-bold">
              <span className="text-black bg-white px-2 py-1 border border-gray-300">
                MW: <span className="text-black">{compound.mw.toFixed(1)}</span>
              </span>
              <span className="text-black bg-white px-2 py-1 border border-gray-300">
                LogP: <span className="text-black">{compound.logp.toFixed(1)}</span>
              </span>
              <span className="text-black bg-white px-2 py-1 border border-gray-300">
                LE: <span className="text-black">{compound.ligand_eff.toFixed(2)}</span>
              </span>
            </div>
            <span className="inline-flex items-center gap-2 text-sm font-bold text-black group-hover:gap-3 transition-all">
              Analyze 
              <ArrowRight className="h-4 w-4" />
            </span>
          </div>
        </div>
      </Link>
    </motion.div>
  );
}