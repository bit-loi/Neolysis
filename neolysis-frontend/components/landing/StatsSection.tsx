'use client';

import { motion, useInView } from 'framer-motion';
import { useRef } from 'react';

const stats = [
  { value: '4', label: 'Diseases Targeted' },
  { value: '12+', label: 'Protein Targets' },
  { value: 'Open', label: 'Access for All' },
  { value: 'Free', label: 'No License Required' },
];

export function StatsSection() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-50px' });

  return (
    <section className="py-16 bg-white border-y border-gray-100">
      <div ref={ref} className="mx-auto max-w-6xl px-6 lg:px-8">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          {stats.map((stat, i) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 20 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ delay: i * 0.1, duration: 0.5 }}
              className="text-center"
            >
              <div className="text-4xl sm:text-5xl font-serif text-gray-900">
                {stat.value}
              </div>
              <div className="mt-2 text-sm text-gray-500 tracking-wide uppercase">
                {stat.label}
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
