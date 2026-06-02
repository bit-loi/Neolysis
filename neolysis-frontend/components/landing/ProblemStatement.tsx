'use client';

import Link from 'next/link';
import { ArrowRight, HelpCircle } from 'lucide-react';
import { motion, useInView } from 'framer-motion';
import { useRef } from 'react';

export function ProblemStatement() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });

  return (
    <section className="section-light py-24 lg:py-32">
      <div ref={ref} className="mx-auto max-w-5xl px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.8, ease: 'easeOut' }}
          className="mb-10 flex items-start gap-4"
        >
          <span className="mt-1 text-2xl text-gray-400">◆</span>
          <p className="font-serif text-3xl leading-[1.35] text-gray-900 sm:text-4xl lg:text-[2.8rem]">
            Industrial enzyme programs need candidates that survive real process conditions.{' '}
            <span className="text-gray-500">
              Neolysis narrows sequence and variant choices before expensive wet-lab screening.
            </span>
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="flex flex-col gap-4 sm:flex-row"
        >
          <Link href="/analyze" className="btn-bordered btn-bordered-dark">
            <ArrowRight className="h-4 w-4" />
            Start Analysis
          </Link>
          <Link href="/methodology" className="inline-flex items-center gap-3 px-6 py-4 font-normal text-gray-700 transition-colors hover:text-gray-900">
            <HelpCircle className="h-4 w-4" />
            <span className="text-sm uppercase tracking-wider">Methodology</span>
          </Link>
        </motion.div>
      </div>
    </section>
  );
}
