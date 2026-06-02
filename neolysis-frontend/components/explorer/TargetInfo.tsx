'use client';

import { ExternalLink } from 'lucide-react';
import { ProteinTarget } from '@/lib/types';
import { DiseaseBadge } from '@/components/targets/DiseaseBadge';
import { getAlphaFoldUrl } from '@/lib/utils';
import { motion } from 'framer-motion';

interface TargetInfoProps {
  target: ProteinTarget;
}

export function TargetInfo({ target }: TargetInfoProps) {
  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: 'easeOut' }}
      className="bg-white border border-gray-300 p-8 md:p-10 font-sans"
    >
      <div className="flex flex-wrap items-start gap-4 mb-8 pb-8 border-b border-gray-200">
        <div className="flex-grow">
          <h1 className="text-4xl md:text-5xl font-serif font-bold text-black tracking-tight mb-2">{target.name}</h1>
          <p className="text-gray-500 font-serif font-bold text-lg">{target.fullName}</p>
        </div>
        <DiseaseBadge disease={target.disease} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-10 mb-10">
        <div className="md:col-span-1">
          <p className="text-sm font-bold text-black uppercase tracking-wider mb-2">Organism</p>
          <div className="bg-gray-50 border border-gray-200 p-4">
            <p className="text-gray-700 font-mono text-sm">{target.organism}</p>
          </div>
        </div>

        <div className="md:col-span-2">
          <p className="text-sm font-bold text-black uppercase tracking-wider mb-2">Description</p>
          <p className="text-gray-700 leading-relaxed text-lg">{target.description}</p>
        </div>
      </div>

      <div className="mb-10">
        <p className="text-sm font-bold text-black uppercase tracking-wider mb-4">External Links</p>
        <div className="flex flex-wrap gap-4">
          <a
            href={`https://www.rcsb.org/structure/${target.pdbId}`}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-bordered btn-bordered-dark text-sm px-4 py-2"
          >
            PDB: {target.pdbId} <ExternalLink className="h-4 w-4" />
          </a>
          <a
            href={getAlphaFoldUrl(target.alphafoldId)}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-bordered btn-bordered-dark text-sm px-4 py-2"
          >
            AlphaFold <ExternalLink className="h-4 w-4" />
          </a>
          <a
            href={`https://rest.uniprot.org/uniprotkb/${target.uniprotId}.json`}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-bordered btn-bordered-dark text-sm px-4 py-2"
          >
            UniProt <ExternalLink className="h-4 w-4" />
          </a>
        </div>
      </div>

      <details className="group bg-gray-50 border border-gray-200 cursor-pointer">
        <summary className="flex items-center gap-3 p-5 text-black font-serif font-bold text-lg outline-none list-none [&::-webkit-details-marker]:hidden">
          <span
            className="inline-block w-0 h-0 border-t-[5px] border-t-transparent border-b-[5px] border-b-transparent border-l-[8px] border-l-gray-500 transform transition-transform group-open:rotate-90 shrink-0"
          />
          Why this target matters
        </summary>
        <div className="px-5 pb-5 pt-2 text-gray-700 leading-relaxed">
          <div className="flex gap-4">
            <div className="w-0.5 bg-gray-300 shrink-0"></div>
            <div>
              <p className="mb-3">{target.bindingSiteDescription}</p>
              <p className="text-sm">
                This target has been selected based on validated scientific literature and represents a high-priority 
                therapeutic intervention point for <strong className="text-black">{target.disease.replace('-', ' ')}</strong> research.
              </p>
            </div>
          </div>
        </div>
      </details>
    </motion.div>
  );
}
