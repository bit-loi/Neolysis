'use client';

import Image from 'next/image';
import Link from 'next/link';
import { ArrowRight } from 'lucide-react';
import { motion, useInView } from 'framer-motion';
import { useRef } from 'react';

export function CTASection() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-50px' });

  return (
    <section ref={ref} className="section-gray overflow-hidden">
      <div className="grid grid-cols-1 lg:grid-cols-2">
        <motion.div
          initial={{ opacity: 0 }}
          animate={isInView ? { opacity: 1 } : {}}
          transition={{ duration: 0.8 }}
          className="relative min-h-[420px]"
        >
          <Image
            src="/community-illustration.jpg"
            alt="Biotechnology team planning validation"
            fill
            className="object-cover"
          />
        </motion.div>

        <div className="px-8 py-20 sm:px-12 lg:px-16 lg:py-28 xl:px-24">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.6 }}
          >
            <h2 className="font-serif text-4xl leading-tight text-gray-900 sm:text-5xl">
              Product roadmap
            </h2>
            <div className="mt-8 space-y-4 text-gray-700">
              <p>Current: FASTA validation, feature extraction, baseline scoring, variant ranking, and agentic report generation.</p>
              <p>Next: protein language model embeddings, enzyme family search, structure-aware mutation risk, and richer project storage.</p>
              <p className="font-medium text-black">Not a guarantee of activity. Not a replacement for wet-lab validation.</p>
            </div>
            <Link href="/analyze" className="btn-bordered btn-bordered-dark mt-10">
              <ArrowRight className="h-4 w-4" />
              Start with a Sequence
            </Link>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
