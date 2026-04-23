'use client';

import Link from 'next/link';
import Image from 'next/image';
import { motion, useInView } from 'framer-motion';
import { useRef } from 'react';
import { ArrowRight } from 'lucide-react';

const useCases = [
  {
    title: 'For Researchers',
    description:
      'Explore validated protein targets across four NTDs. Access pre-computed docking scores, 3D binding site visualizations, and AI-generated insights to accelerate your early-stage drug discovery.',
    cta: 'Explore Protein Targets',
    href: '/targets',
  },
  {
    title: 'For Students',
    description:
      'Learn computational drug discovery with interactive 3D protein structures and AI-guided explanations. No expensive software or HPC infrastructure required — just a browser.',
    cta: 'Start Learning',
    href: '/methodology',
  },
  {
    title: 'For Developers',
    description:
      'Access open data from AlphaFold DB, RCSB PDB, and PubChem through our unified platform. Integrate molecular insights into your own research tools and pipelines.',
    cta: 'View Documentation',
    href: '/about',
  },
];

export function HowItWorks() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-50px' });

  return (
    <section ref={ref} className="section-light overflow-hidden">
      <div className="grid grid-cols-1 lg:grid-cols-2">
        {/* Left: Text content */}
        <div className="px-8 sm:px-12 lg:px-16 xl:px-24 py-20 lg:py-28">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.6 }}
          >
            <h2 className="text-4xl sm:text-5xl font-serif text-gray-900 leading-tight mb-16">
              Get Started
              <br />
              <em className="italic text-gray-500">With Neolysis</em>
            </h2>
          </motion.div>

          <div className="space-y-0">
            {useCases.map((useCase, i) => (
              <motion.div
                key={useCase.title}
                initial={{ opacity: 0, y: 40 }}
                animate={isInView ? { opacity: 1, y: 0 } : {}}
                transition={{ delay: i * 0.2, duration: 0.6 }}
                className="py-8 border-b border-gray-300 last:border-b-0"
              >
                <h3 className="text-2xl sm:text-3xl font-serif text-gray-900 mb-3">
                  {useCase.title}
                </h3>
                <p className="text-gray-600 text-base leading-relaxed mb-5 max-w-lg">
                  {useCase.description}
                </p>
                <Link
                  href={useCase.href}
                  className="btn-bordered btn-bordered-dark"
                >
                  <ArrowRight className="h-4 w-4" />
                  {useCase.cta}
                </Link>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Right: Image flush to edge */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={isInView ? { opacity: 1 } : {}}
          transition={{ duration: 0.8, delay: 0.3 }}
          className="relative min-h-[500px] lg:min-h-full"
        >
          <Image
            src="/researcher-illustration.jpg"
            alt="Researcher in laboratory"
            fill
            className="object-cover"
          />
        </motion.div>
      </div>
    </section>
  );
}
