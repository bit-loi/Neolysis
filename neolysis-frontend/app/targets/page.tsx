'use client';

import { useState } from 'react';
import { proteinTargets } from '@/lib/targets';
import { Disease, DISEASE_LABELS } from '@/lib/types';
import { TargetGrid } from '@/components/targets/TargetGrid';
import { SectionHeader } from '@/components/ui/SectionHeader';
import { motion } from 'framer-motion';

const diseases: Array<Disease | 'all'> = ['all', 'leptospirosis', 'scrub-typhus', 'melioidosis', 'dengue'];

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1
    }
  }
};

const fadeInUp = {
  hidden: { opacity: 0, y: 10 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: 'easeOut' } }
};

export default function TargetsPage() {
  const [selectedDisease, setSelectedDisease] = useState<Disease | 'all'>('all');

  const filteredTargets = selectedDisease === 'all'
    ? proteinTargets
    : proteinTargets.filter((t) => t.disease === selectedDisease);

  return (
    <div className="min-h-screen bg-[#f5f5f0] text-black pt-24 pb-16 grain-overlay">
      <div className="relative z-10 mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <SectionHeader
          title="Protein Targets"
          subtitle="Select a validated target to begin exploration and AI-powered drug candidate analysis"
          centered={true}
        />

        <motion.div 
          variants={staggerContainer} 
          initial="hidden" 
          animate="visible" 
          className="mb-12 flex flex-wrap justify-center gap-3 font-sans"
        >
          {diseases.map((disease) => {
            const isSelected = selectedDisease === disease;
            return (
              <motion.button
                variants={fadeInUp}
                key={disease}
                onClick={() => setSelectedDisease(disease)}
                className={`px-5 py-2.5 text-sm font-medium transition-all duration-300 border ${
                  isSelected
                    ? 'bg-black text-white border-black'
                    : 'bg-transparent text-gray-700 border-gray-400 hover:border-black hover:text-black'
                }`}
              >
                {disease === 'all' ? 'All Diseases' : DISEASE_LABELS[disease as Disease]}
              </motion.button>
            );
          })}
        </motion.div>

        <TargetGrid targets={filteredTargets} />
      </div>
    </div>
  );
}
