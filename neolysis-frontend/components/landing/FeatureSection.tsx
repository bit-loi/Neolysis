'use client';

import { motion, useInView } from 'framer-motion';
import { useRef } from 'react';
import { Bot, Factory, FlaskConical, GitBranch, ShieldAlert } from 'lucide-react';

const features = [
  {
    title: 'Industrial use cases',
    description: 'Detergent, food biotech, textile, biofuel, and academic enzyme engineering programs.',
    icon: Factory,
  },
  {
    title: 'Property indicators',
    description: 'Thermostability, pH fit, solubility, and process-condition fit as baseline estimates.',
    icon: FlaskConical,
  },
  {
    title: 'Variant prioritization',
    description: 'Mutation summaries, risk flags, confidence notes, and wet-lab priority labels.',
    icon: GitBranch,
  },
  {
    title: 'Agentic analysis',
    description: 'A tool-using workflow agent that records its plan, tool calls, and structured outputs.',
    icon: Bot,
  },
  {
    title: 'Scientific safety',
    description: 'Every report labels outputs as computational estimates that require wet-lab validation.',
    icon: ShieldAlert,
  },
];

export function FeatureSection() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-50px' });

  return (
    <section className="section-light py-20">
      <div ref={ref} className="mx-auto max-w-6xl px-6 lg:px-8">
        <motion.h3
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.5 }}
          className="mb-12 font-serif text-3xl text-gray-900 sm:text-4xl"
        >
          Built for candidate prioritization
        </motion.h3>

        <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
          {features.map((feature, i) => {
            const Icon = feature.icon;
            return (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                animate={isInView ? { opacity: 1, y: 0 } : {}}
                transition={{ delay: i * 0.08, duration: 0.5 }}
                className="border border-gray-300 bg-white p-6"
              >
                <Icon className="h-6 w-6 text-[#5BA8B9]" />
                <h4 className="mt-5 font-serif text-2xl text-gray-900">{feature.title}</h4>
                <p className="mt-3 text-sm leading-relaxed text-gray-600">{feature.description}</p>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
