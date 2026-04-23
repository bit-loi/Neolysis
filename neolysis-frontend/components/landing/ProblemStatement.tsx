'use client';

import Link from 'next/link';
import { motion, useInView } from 'framer-motion';
import { useRef } from 'react';
import { ArrowRight, HelpCircle } from 'lucide-react';

export function ProblemStatement() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });

  return (
    <section className="py-24 lg:py-32 section-light">
      <div
        ref={ref}
        className="mx-auto max-w-5xl px-6 lg:px-8"
      >
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.8, ease: 'easeOut' }}
          className="flex items-start gap-4 mb-10"
        >
          <span className="text-gray-400 text-2xl mt-1">◆</span>
          <p className="text-3xl sm:text-4xl lg:text-[2.8rem] leading-[1.35] font-serif text-gray-900">
            Neolysis is an open-access, AI-powered drug discovery platform.{' '}
            <span className="text-gray-500">
              Purpose-built for ASEAN neglected tropical disease research, it provides
              computational tools that were previously locked behind expensive licenses
              and high-performance infrastructure — now free for every researcher,
              student, and developer.
            </span>
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="flex flex-col sm:flex-row gap-4"
        >
          <Link
            href="/targets"
            className="btn-bordered btn-bordered-dark"
          >
            <ArrowRight className="h-4 w-4" />
            Explore Targets
          </Link>
          <Link
            href="/about"
            className="inline-flex items-center gap-3 px-6 py-4 text-gray-700 font-normal hover:text-gray-900 transition-colors"
          >
            <HelpCircle className="h-4 w-4" />
            <span className="uppercase text-sm tracking-wider">What is Neolysis?</span>
          </Link>
        </motion.div>
      </div>
    </section>
  );
}
