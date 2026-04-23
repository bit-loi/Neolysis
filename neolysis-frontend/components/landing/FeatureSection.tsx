'use client';

import { motion, useInView } from 'framer-motion';
import { useRef } from 'react';
import Image from 'next/image';

const partners = [
  {
    name: 'AlphaFold DB',
    logo: '/logos/alphafold.png',
  },
  {
    name: 'RCSB PDB',
    logo: '/logos/RCSB_PDB.png',
  },
  {
    name: 'PubChem',
    logo: '/logos/PubChem.png',
  },
  {
    name: 'AutoDock Vina',
    logo: '/logos/AutoDock Vina.png',
  },
  {
    name: 'Gemma',
    logo: '/logos/gemma.png',
  },
];

export function FeatureSection() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-50px' });

  return (
    <section className="py-20 section-light">
      <div ref={ref} className="mx-auto max-w-6xl px-6 lg:px-8">
        <motion.h3
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.5 }}
          className="text-3xl sm:text-4xl font-serif text-gray-900 mb-16"
        >
          Tools Powering Neolysis
        </motion.h3>

        <div className="flex flex-wrap items-center justify-between gap-10 lg:gap-16">
          {partners.map((partner, i) => (
            <motion.div
              key={partner.name}
              initial={{ opacity: 0, y: 20 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ delay: i * 0.08, duration: 0.5 }}
              className="flex items-center gap-3 group cursor-default"
            >
              <div className="relative w-10 h-10 flex-shrink-0">
                <Image
                  src={partner.logo}
                  alt={partner.name}
                  fill
                  className="object-contain"
                />
              </div>
              <span className="text-lg sm:text-xl font-medium text-gray-800 tracking-tight group-hover:text-gray-900 transition-colors">
                {partner.name}
              </span>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
