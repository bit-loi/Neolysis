'use client';

import { FlaskConical, Database, Users, Globe } from 'lucide-react';
import { motion } from 'framer-motion';

const fadeInUp = {
  hidden: { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: 'easeOut' } }
};

const staggerChildren = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1
    }
  }
};

export default function AboutPage() {
  return (
    <div className="min-h-screen bg-[#f5f5f0] text-black pt-24 pb-16 grain-overlay">
      <div className="relative z-10 mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
        <motion.h1 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7 }}
          className="text-5xl md:text-6xl font-serif font-bold text-black mb-12 tracking-tight"
        >
          About Neolysis
        </motion.h1>
        
        <div className="space-y-20 font-sans">
          <motion.section variants={fadeInUp} initial="hidden" whileInView="visible" viewport={{ once: true }}>
            <h2 className="text-3xl font-serif font-bold text-black mb-6">Our Mission</h2>
            <p className="text-gray-800 leading-relaxed text-lg max-w-3xl">
              Neolysis is an open-access computational drug discovery platform designed specifically for 
              neglected tropical diseases (NTDs) that disproportionately affect ASEAN populations. 
              We aim to democratize early-stage drug discovery by providing free access to validated 
              protein targets, pre-computed molecular docking scores, and AI-generated research insights.
            </p>
          </motion.section>

          <motion.section variants={staggerChildren} initial="hidden" whileInView="visible" viewport={{ once: true, margin: '-50px' }}>
            <motion.h2 variants={fadeInUp} className="text-3xl font-serif font-bold text-black mb-8 border-b border-gray-300/60 pb-4">Data Sources</motion.h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-px bg-gray-300/60 border border-gray-300/60 p-px">
              <DataSourceCard
                icon={<Database className="h-5 w-5 text-gray-700" />}
                name="AlphaFold DB"
                description="AI-predicted protein structures with confidence scores for validated drug targets."
                link="https://alphafold.ebi.ac.uk"
              />
              <DataSourceCard
                icon={<FlaskConical className="h-5 w-5 text-gray-700" />}
                name="RCSB PDB"
                description="Experimental protein structures validated by X-ray crystallography and cryo-EM."
                link="https://www.rcsb.org"
              />
              <DataSourceCard
                icon={<Globe className="h-5 w-5 text-gray-700" />}
                name="PubChem"
                description="Curated chemical compound database with molecular properties and SMILES structures."
                link="https://pubchem.ncbi.nlm.nih.gov"
              />
              <DataSourceCard
                icon={<Users className="h-5 w-5 text-gray-700" />}
                name="AutoDock Vina"
                description="Open-source molecular docking software for predicting binding affinities."
                link="https://vina.scripps.edu"
              />
            </div>
          </motion.section>

          <motion.section variants={fadeInUp} initial="hidden" whileInView="visible" viewport={{ once: true }}>
            <h2 className="text-3xl font-serif font-bold text-black mb-6">Open Access Commitment</h2>
            <p className="text-gray-800 leading-relaxed max-w-3xl mb-8 text-lg">
              All data on Neolysis is freely accessible without registration or licensing requirements. 
              Our platform is built on the principle that scientific tools should serve the global research 
              community, especially for diseases that predominantly affect under-resourced regions.
            </p>
            <div className="bg-[#e8e6e0] p-6 border-l-4 border-gray-500 flex items-start gap-4">
              <Globe className="h-6 w-6 text-black shrink-0 mt-0.5" />
              <p className="text-sm text-gray-800 leading-relaxed">
                <strong className="text-black">Disclaimer:</strong> This platform is designed for research exploration only. AI-generated insights are not 
                clinical advice and should be validated through appropriate experimental methods.
              </p>
            </div>
          </motion.section>

          <motion.section variants={staggerChildren} initial="hidden" whileInView="visible" viewport={{ once: true }}>
            <motion.h2 variants={fadeInUp} className="text-3xl font-serif font-bold text-black mb-8 border-b border-gray-300/60 pb-4">Platform Statistics</motion.h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-px bg-gray-300/60 border border-gray-300/60 p-px">
              <StatCard label="Diseases" value="4" />
              <StatCard label="Protein Targets" value="12+" />
              <StatCard label="Drug Candidates" value="50+" />
              <StatCard label="Open Data" value="100%" />
            </div>
          </motion.section>
        </div>
      </div>
    </div>
  );
}

function DataSourceCard({ name, description, link, icon }: { name: string; description: string; link: string; icon: React.ReactNode }) {
  return (
    <motion.div variants={fadeInUp} className="bg-[#f5f5f0] p-8 flex flex-col h-full hover:bg-white transition-colors duration-300">
      <div className="flex items-center gap-3 mb-4">
        {icon}
        <h3 className="text-xl font-serif font-bold text-black">{name}</h3>
      </div>
      <p className="text-sm text-gray-700 leading-relaxed flex-grow mb-8">{description}</p>
      <a
        href={link}
        target="_blank"
        rel="noopener noreferrer"
        className="btn-bordered btn-bordered-dark mt-auto w-fit text-sm py-2 px-5 font-bold"
      >
        Visit Source <span>→</span>
      </a>
    </motion.div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <motion.div variants={fadeInUp} className="bg-[#f5f5f0] p-8 text-center hover:bg-white transition-colors duration-300">
      <div className="text-4xl md:text-5xl font-serif font-bold text-black mb-3">{value}</div>
      <div className="text-xs text-gray-700 font-bold tracking-[0.1em] uppercase font-sans">{label}</div>
    </motion.div>
  );
}
