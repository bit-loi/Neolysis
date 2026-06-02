'use client';

import { motion, useInView } from 'framer-motion';
import { useRef } from 'react';

const stats = [
  { value: 'FASTA', label: 'Sequence Input' },
  { value: 'Baseline', label: 'Property Scoring' },
  { value: 'Variant', label: 'Ranking Scaffold' },
  { value: 'Report', label: 'Validation Planning' },
];

export function StatsSection() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-50px' });

  return (
    <section className="border-y border-gray-100 bg-white py-16">
      <div ref={ref} className="mx-auto max-w-6xl px-6 lg:px-8">
        <div className="grid grid-cols-2 gap-8 md:grid-cols-4">
          {stats.map((stat, i) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 20 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ delay: i * 0.1, duration: 0.5 }}
              className="text-center"
            >
              <div className="font-serif text-3xl text-gray-900 sm:text-4xl">
                {stat.value}
              </div>
              <div className="mt-2 text-sm uppercase tracking-wide text-gray-500">
                {stat.label}
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
