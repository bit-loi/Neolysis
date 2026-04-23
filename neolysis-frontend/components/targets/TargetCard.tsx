'use client';

import Link from 'next/link';
import { ArrowRight, Database } from 'lucide-react';
import { ProteinTarget } from '@/lib/types';
import { DiseaseBadge } from './DiseaseBadge';
import { motion } from 'framer-motion';

const fadeInUp = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: 'easeOut' } }
};

interface TargetCardProps {
  target: ProteinTarget;
}

export function TargetCard({ target }: TargetCardProps) {
  return (
    <motion.div variants={fadeInUp} className="h-full">
      <Link href={`/targets/${target.id}`} className="block h-full outline-none font-sans">
        <div className="group bg-white border border-gray-300 p-8 hover:border-black hover:shadow-lg transition-all duration-300 cursor-pointer h-full flex flex-col relative">
          <div className="flex items-start justify-between mb-6">
            <div>
              <h3 className="text-2xl font-serif font-bold text-black transition-colors mb-2">
                {target.name}
              </h3>
              <p className="text-sm font-bold text-gray-600">{target.organism}</p>
            </div>
          </div>

          <div className="mb-6">
            <DiseaseBadge disease={target.disease} size="sm" />
          </div>

          <p className="mb-8 text-gray-700 line-clamp-3 flex-grow leading-relaxed">
            {target.description}
          </p>

          <div className="pt-6 border-t border-gray-200 flex items-center justify-between">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-gray-50 text-black border border-gray-300 text-xs font-bold">
              <Database className="w-3.5 h-3.5" />
              {target.candidateCount} candidates
            </span>
            <span className="inline-flex items-center gap-2 text-sm font-bold text-black group-hover:gap-3 transition-all">
              Explore 
              <ArrowRight className="h-4 w-4" />
            </span>
          </div>
        </div>
      </Link>
    </motion.div>
  );
}
