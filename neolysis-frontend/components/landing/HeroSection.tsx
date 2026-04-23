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
    <section className="relative overflow-hidden min-h-screen bg-navy grain-overlay">
      {/* WebGL Smoke Background — Cyan/Teal color */}
      <div className="absolute inset-0 z-0">
        <SmokeBackground smokeColor="#4EC8D9" />
      </div>

      {/* Content */}
      <div className="relative z-10 mx-auto max-w-7xl px-6 lg:px-8 pt-40 pb-16 lg:pt-48 lg:pb-24">
        <div className="text-center max-w-5xl mx-auto">
          <motion.h1
            initial="hidden"
            animate="visible"
            variants={fadeInUp}
            transition={{ duration: 1, ease: [0.25, 0.46, 0.45, 0.94] }}
            className="text-5xl sm:text-6xl lg:text-[5.5rem] leading-[1.1] font-serif text-accent cyan-glow-text"
          >
            Discovery Starts{' '}
            <em className="italic">With the Right</em>{' '}
            Target
          </motion.h1>

          <motion.p
            initial="hidden"
            animate="visible"
            variants={fadeInUp}
            transition={{
              duration: 0.8,
              delay: 0.3,
              ease: [0.25, 0.46, 0.45, 0.94],
            }}
            className="mt-8 text-lg sm:text-xl text-gray-300 max-w-3xl mx-auto leading-relaxed font-sans"
          >
            An open-access, AI-powered drug discovery platform for ASEAN
            neglected tropical diseases. Explore 3D protein structures,
            pre-computed docking scores, and AI-generated insights.
          </motion.p>

          <motion.div
            initial="hidden"
            animate="visible"
            variants={fadeInUp}
            transition={{ duration: 0.8, delay: 0.5 }}
            className="mt-12 flex flex-col sm:flex-row items-center justify-center gap-6"
          >
            <Link href="/targets" className="btn-bordered btn-bordered-light text-lg">
              <ArrowRight className="h-5 w-5" />
              Start Exploring
            </Link>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
