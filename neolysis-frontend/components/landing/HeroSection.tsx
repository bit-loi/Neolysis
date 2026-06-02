'use client';

import Link from 'next/link';
import { ArrowRight } from 'lucide-react';
import { motion } from 'framer-motion';
import { SmokeBackground } from '@/components/ui/SmokeBackground';

const fadeInUp = {
  hidden: { opacity: 0, y: 40 },
  visible: { opacity: 1, y: 0 },
};

export function HeroSection() {
  return (
    <section className="relative min-h-screen overflow-hidden bg-navy grain-overlay">
      <div className="absolute inset-0 z-0">
        <SmokeBackground smokeColor="#4EC8D9" />
      </div>

      <div className="relative z-10 mx-auto max-w-7xl px-6 pt-40 pb-16 lg:px-8 lg:pt-48 lg:pb-24">
        <div className="mx-auto max-w-5xl text-center">
          <motion.h1
            initial="hidden"
            animate="visible"
            variants={fadeInUp}
            transition={{ duration: 1, ease: [0.25, 0.46, 0.45, 0.94] }}
            className="font-serif text-5xl leading-[1.1] text-accent cyan-glow-text sm:text-6xl lg:text-[5.5rem]"
          >
            Computational enzyme intelligence for industrial biotechnology.
          </motion.h1>

          <motion.p
            initial="hidden"
            animate="visible"
            variants={fadeInUp}
            transition={{ duration: 0.8, delay: 0.3, ease: [0.25, 0.46, 0.45, 0.94] }}
            className="mx-auto mt-8 max-w-3xl font-sans text-lg leading-relaxed text-gray-300 sm:text-xl"
          >
            Neolysis helps R&amp;D teams analyze enzyme sequences, estimate process-relevant properties, rank variants, and plan wet-lab validation.
          </motion.p>

          <motion.div
            initial="hidden"
            animate="visible"
            variants={fadeInUp}
            transition={{ duration: 0.8, delay: 0.5 }}
            className="mt-12 flex flex-col items-center justify-center gap-6 sm:flex-row"
          >
            <Link href="/analyze" className="btn-bordered btn-bordered-light text-lg">
              <ArrowRight className="h-5 w-5" />
              Analyze Sequence
            </Link>
            <Link href="/agent-report" className="btn-bordered btn-bordered-light text-lg">
              <ArrowRight className="h-5 w-5" />
              Generate Report
            </Link>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
