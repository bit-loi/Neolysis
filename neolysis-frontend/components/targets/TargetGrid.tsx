'use client';

import { ProteinTarget } from '@/lib/types';
import { TargetCard } from './TargetCard';
import { Database } from 'lucide-react';
import { motion } from 'framer-motion';

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1
    }
  }
};

interface TargetGridProps {
  targets: ProteinTarget[];
}

export function TargetGrid({ targets }: TargetGridProps) {
  if (targets.length === 0) {
    return (
      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="flex flex-col items-center justify-center py-24 text-center bg-white border border-gray-300"
      >
        <div className="w-16 h-16 bg-gray-50 border border-gray-200 flex items-center justify-center mb-6">
          <Database className="w-8 h-8 text-black" />
        </div>
        <h3 className="text-2xl font-serif font-bold text-black mb-2">No targets found</h3>
        <p className="text-gray-700 max-w-md font-sans">Try selecting a different disease category. Our database is continuously expanding with new targets.</p>
      </motion.div>
    );
  }

  return (
    <motion.div 
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 relative z-10"
    >
      {targets.map((target) => (
        <TargetCard key={target.id} target={target} />
      ))}
    </motion.div>
  );
}
