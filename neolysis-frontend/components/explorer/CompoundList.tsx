'use client';

import { useState } from 'react';
import { CompoundWithDocking } from '@/lib/types';
import { CompoundCard } from './CompoundCard';
import { SkeletonCard } from '@/components/ui/LoadingSpinner';
import { CustomSelect } from '@/components/ui/CustomSelect';
import { motion } from 'framer-motion';
import { Info } from 'lucide-react';

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.05
    }
  }
};

interface CompoundListProps {
  compounds: CompoundWithDocking[];
  isLoading?: boolean;
}

export function CompoundList({ compounds, isLoading }: CompoundListProps) {
  const [sortBy, setSortBy] = useState<'score' | 'name'>('score');
  const [filterLipinski, setFilterLipinski] = useState<'all' | 'pass' | 'fail'>('all');

  const filteredCompounds = compounds.filter((c) => {
    if (filterLipinski === 'all') return true;
    if (filterLipinski === 'pass') return c.lipinskiPass;
    return !c.lipinskiPass;
  });

  const sortedCompounds = [...filteredCompounds].sort((a, b) => {
    if (sortBy === 'score') return a.dockingScore - b.dockingScore;
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
        <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
          <div className="flex items-center gap-3">
            <h3 className="text-2xl font-serif font-bold text-black">Drug Candidates</h3>
            <span className="px-3 py-1 bg-white border border-gray-400 text-black text-xs font-bold rounded-full">
              {compounds.length} Found
            </span>
          </div>
        </div>

        {/* Ranking methodology note */}
        <div className="flex items-start gap-2 mb-5 p-3 bg-white border border-gray-200 text-xs text-gray-600 leading-relaxed">
          <Info className="h-3.5 w-3.5 mt-0.5 shrink-0 text-gray-400" />
          <span>
            Ranked by <strong className="text-black">predicted binding affinity</strong> (AutoDock Vina).
            Compounds flagged under Lipinski Rule of 5 may still be viable candidates —
            many approved drugs exceed Ro5 thresholds.
          </span>
        </div>

        <div className="flex flex-wrap gap-6">
          <div className="flex items-center gap-3">
            <label className="text-xs font-bold text-black uppercase tracking-wider">Sort by:</label>
            <CustomSelect
              value={sortBy}
              onChange={(val) => setSortBy(val as 'score' | 'name')}
              options={[
                { label: 'Docking Score', value: 'score' },
                { label: 'Compound Name', value: 'name' }
              ]}
            />
          </div>

          <div className="flex items-center gap-3">
            <label className="text-xs font-bold text-black uppercase tracking-wider">Lipinski Rule:</label>
            <div className="flex gap-2">
              {(['all', 'pass', 'fail'] as const).map((f) => (
                <button
                  key={f}
                  onClick={() => setFilterLipinski(f)}
                  className={`px-4 py-1.5 text-xs font-bold transition-all border ${
                    filterLipinski === f
                      ? 'bg-black text-white border-black'
                      : 'bg-white text-gray-800 border-gray-400 hover:border-black hover:text-black'
                  }`}
                >
                  {f === 'all' ? 'All' : f === 'pass' ? 'Pass' : 'Flagged'}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="max-h-[600px] overflow-y-auto bg-gray-50 custom-scrollbar p-1">
        {isLoading ? (
          <div className="p-5 space-y-4">
            {[1, 2, 3].map((i) => (
              <SkeletonCard key={i} />
            ))}
          </div>
        ) : sortedCompounds.length === 0 ? (
          <div className="p-12 text-center">
            <div className="inline-block p-4 rounded-full bg-white border border-gray-300 mb-4">
              <span className="text-2xl opacity-50">🔬</span>
            </div>
            <p className="text-gray-800 font-medium">No compounds match your current filters.</p>
          </div>
        ) : (
          <motion.div 
            variants={staggerContainer}
            initial="hidden"
            animate="visible"
            className="space-y-1"
          >
            {sortedCompounds.map((compound, idx) => (
              <CompoundCard
                key={compound.cid}
                compound={compound}
                targetId={compound.targetId}
                rank={sortBy === 'score' ? idx + 1 : undefined}
              />
            ))}
          </motion.div>
        )}
      </div>
    </motion.div>
  );
}
