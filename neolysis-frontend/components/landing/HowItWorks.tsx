'use client';

import Image from 'next/image';
import Link from 'next/link';
import { ArrowRight } from 'lucide-react';
import { motion, useInView } from 'framer-motion';
import { useRef } from 'react';

const workflow = [
  {
    title: 'Analyze sequences',
    description: 'Validate FASTA inputs, clean protein sequences, and extract baseline protein descriptors.',
    href: '/analyze',
    cta: 'Open Analyzer',
  },
  {
    title: 'Score process fit',
    description: 'Estimate thermostability, pH fit, solubility, and condition fit with transparent baseline indicators.',
    href: '/methodology',
    cta: 'Review Method',
  },
  {
    title: 'Rank variants',
    description: 'Compare candidate mutations with risk flags and wet-lab priority labels.',
    href: '/variants',
    cta: 'Rank Variants',
  },
];

export function HowItWorks() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-50px' });

  return (
    <section ref={ref} className="section-light overflow-hidden">
      <div className="grid grid-cols-1 lg:grid-cols-2">
        <div className="px-8 py-20 sm:px-12 lg:px-16 lg:py-28 xl:px-24">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.6 }}
          >
            <h2 className="mb-16 font-serif text-4xl leading-tight text-gray-900 sm:text-5xl">
              Enzyme workflow
              <br />
              <em className="italic text-gray-500">From sequence to validation plan</em>
            </h2>
          </motion.div>

          <div>
            {workflow.map((item, i) => (
              <motion.div
                key={item.title}
                initial={{ opacity: 0, y: 40 }}
                animate={isInView ? { opacity: 1, y: 0 } : {}}
                transition={{ delay: i * 0.2, duration: 0.6 }}
                className="border-b border-gray-300 py-8 last:border-b-0"
              >
                <h3 className="mb-3 font-serif text-2xl text-gray-900 sm:text-3xl">
                  {item.title}
                </h3>
                <p className="mb-5 max-w-lg text-base leading-relaxed text-gray-600">
                  {item.description}
                </p>
                <Link href={item.href} className="btn-bordered btn-bordered-dark">
                  <ArrowRight className="h-4 w-4" />
                  {item.cta}
                </Link>
              </motion.div>
            ))}
          </div>
        </div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={isInView ? { opacity: 1 } : {}}
          transition={{ duration: 0.8, delay: 0.3 }}
          className="relative min-h-[500px] lg:min-h-full"
        >
          <Image
            src="/researcher-illustration.jpg"
            alt="Researcher preparing enzyme validation workflow"
            fill
            className="object-cover"
          />
        </motion.div>
      </div>
    </section>
  );
}
