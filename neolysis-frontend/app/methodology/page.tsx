'use client';

import { Info } from 'lucide-react';
import { motion } from 'framer-motion';

const fadeInUp = {
  hidden: { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: 'easeOut' } }
};

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1
    }
  }
};

export default function MethodologyPage() {
  return (
    <div className="min-h-screen bg-[#f5f5f0] text-black pt-24 pb-16 grain-overlay">
      <div className="relative z-10 mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
        <motion.h1 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7 }}
          className="text-5xl md:text-6xl font-serif font-bold text-black mb-12 tracking-tight"
        >
          Methodology
        </motion.h1>
        
        <div className="space-y-20 font-sans">
          
          <motion.section id="protein-structures" variants={fadeInUp} initial="hidden" whileInView="visible" viewport={{ once: true }}>
            <h2 className="text-3xl font-serif font-bold text-black mb-6">Protein Structure Sources</h2>
            <div className="bg-white border border-gray-300/60 p-8 md:p-10">
              <p className="text-gray-800 leading-relaxed mb-6 text-lg">
                Protein structures are sourced from two primary databases to ensure comprehensive coverage:
              </p>
              
              <motion.ul variants={staggerContainer} initial="hidden" whileInView="visible" viewport={{ once: true }} className="space-y-6 mb-8">
                <motion.li variants={fadeInUp} className="flex items-start gap-4">
                  <div className="w-1.5 h-1.5 rounded-full bg-black mt-2.5 shrink-0"></div>
                  <p className="text-gray-800 leading-relaxed">
                    <strong className="text-black font-serif font-bold text-lg block mb-1">RCSB PDB:</strong> 
                    Experimental structures determined by X-ray crystallography, 
                    NMR spectroscopy, or cryo-electron microscopy. These represent validated, biologically 
                    relevant conformations.
                  </p>
                </motion.li>
                <motion.li variants={fadeInUp} className="flex items-start gap-4">
                  <div className="w-1.5 h-1.5 rounded-full bg-black mt-2.5 shrink-0"></div>
                  <p className="text-gray-800 leading-relaxed">
                    <strong className="text-black font-serif font-bold text-lg block mb-1">AlphaFold DB:</strong> 
                    AI-predicted structures using deep learning models. 
                    Provides coverage for targets without experimental structures, with per-residue 
                    confidence scores (pLDDT) to assess prediction reliability.
                  </p>
                </motion.li>
              </motion.ul>
              <p className="text-gray-700 leading-relaxed text-sm bg-gray-50 p-4 border-l-2 border-gray-400">
                Structures are validated for structural integrity and appropriate resolution before 
                inclusion in the platform. Binding site residues are identified using computational 
                cavity detection algorithms.
              </p>
            </div>
          </motion.section>

          <motion.section id="docking-pipeline" variants={fadeInUp} initial="hidden" whileInView="visible" viewport={{ once: true }}>
            <h2 className="text-3xl font-serif font-bold text-black mb-6">Docking Pipeline</h2>
            <div className="bg-white border border-gray-300/60 p-8 md:p-10">
              <p className="text-gray-800 leading-relaxed mb-8 text-lg">
                Molecular docking is performed using AutoDock Vina, an open-source docking program 
                known for its accuracy and speed:
              </p>
              
              <div className="bg-[#171717] border border-black p-6 font-mono text-sm overflow-x-auto text-gray-200 mb-8 w-full shadow-inner">
                <pre>{`{
  "target_id": "lipl32",
  "pdbqt_receptor": "Lipl32_receptor.pdbqt",
  "pdbqt_ligand": "compound.pdbqt",
  "center": {"x": 0, "y": 0, "z": 0},
  "size": {"x": 20, "y": 20, "z": 20},
  "exhaustiveness": 32,
  "num_modes": 10
}`}</pre>
              </div>
              
              <p className="text-gray-800 leading-relaxed mb-8">
                Binding site coordinates are derived from the receptor structure, and scoring 
                function parameters follow established best practices. Each compound is docked 
                in multiple poses to identify the lowest energy binding conformation.
              </p>

              <div className="bg-[#e8e6e0] border-l-4 border-gray-500 p-5 flex items-start gap-4">
                <Info className="w-5 h-5 text-black shrink-0 mt-0.5" />
                <p className="text-sm text-gray-800 leading-relaxed">
                  <strong className="text-black">Note:</strong> Pre-computed docking scores are predictions based on 
                  computational modeling. Experimental validation through surface plasmon resonance, 
                  ITC, or cellular assays is required to confirm binding.
                </p>
              </div>
            </div>
          </motion.section>

          <motion.section id="compound-filtering" variants={fadeInUp} initial="hidden" whileInView="visible" viewport={{ once: true }}>
            <h2 className="text-3xl font-serif font-bold text-black mb-6">Compound Filtering</h2>
            <div className="bg-white border border-gray-300/60">
              <div className="p-8 md:p-10 pb-6 border-b border-gray-200">
                <p className="text-gray-800 leading-relaxed text-lg">
                  Drug candidates are filtered through multiple criteria to identify compounds with 
                  favorable pharmaceutical properties:
                </p>
              </div>
              
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead>
                    <tr className="bg-gray-50 border-b border-gray-200">
                      <th className="text-left font-bold text-black px-8 py-4">Filter</th>
                      <th className="text-left font-bold text-black px-8 py-4">Criterion</th>
                      <th className="text-left font-bold text-black px-8 py-4 hidden md:table-cell">Reference</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {[
                      { filter: 'Lipinski MW', criteria: '≤ 500 g/mol', ref: 'Lipinski et al., 2001' },
                      { filter: 'Lipinski LogP', criteria: '≤ 5', ref: 'Lipinski et al., 2001' },
                      { filter: 'H-Bond Donors', criteria: '≤ 5', ref: 'Lipinski et al., 2001' },
                      { filter: 'H-Bond Acceptors', criteria: '≤ 10', ref: 'Lipinski et al., 2001' },
                      { filter: 'TPSA', criteria: '≤ 140 Å²', ref: 'Veber et al., 2002' },
                      { filter: 'Rotatable Bonds', criteria: '≤ 10', ref: 'Veber et al., 2002' },
                    ].map((row, i) => (
                      <tr key={i} className="hover:bg-gray-50/50 transition-colors">
                        <td className="px-8 py-4 text-gray-800 font-bold">{row.filter}</td>
                        <td className="px-8 py-4 text-gray-700 font-mono">{row.criteria}</td>
                        <td className="px-8 py-4 text-gray-600 hidden md:table-cell">{row.ref}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </motion.section>

          <motion.section id="ai-explanations" variants={fadeInUp} initial="hidden" whileInView="visible" viewport={{ once: true }}>
            <h2 className="text-3xl font-serif font-bold text-black mb-6">AI Explanation System</h2>
            <div className="bg-white border border-gray-300/60 p-8 md:p-10">
              <p className="text-gray-800 leading-relaxed mb-8 text-lg">
                AI-generated insights are produced using a structured prompt system that synthesizes:
              </p>
              
              <motion.div variants={staggerContainer} initial="hidden" whileInView="visible" viewport={{ once: true }} className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-10">
                {[
                  "Target protein biological function and disease relevance",
                  "Compound molecular properties and drug-likeness profile",
                  "Docking score interpretation and binding mode analysis",
                  "Literature-derived context for ASEAN disease burden"
                ].map((item, i) => (
                  <motion.div variants={fadeInUp} key={i} className="flex items-start gap-3 bg-gray-50 border border-gray-200 px-4 py-4">
                    <div className="w-1.5 h-1.5 rounded-full bg-black shrink-0 mt-2"></div>
                    <span className="text-sm font-medium text-gray-800">{item}</span>
                  </motion.div>
                ))}
              </motion.div>
              
              <p className="text-gray-800 leading-relaxed mb-6">
                The LLM generates three narrative sections:
              </p>
              
              <div className="space-y-6 mb-10 border-l-2 border-gray-300 pl-6">
                <div>
                  <strong className="text-black font-serif font-bold text-lg block mb-1">1. Why this target matters</strong>
                  <span className="text-gray-700 text-sm">Disease context and validation status</span>
                </div>
                <div>
                  <strong className="text-black font-serif font-bold text-lg block mb-1">2. Why this compound is promising</strong>
                  <span className="text-gray-700 text-sm">Binding affinity and drug-likeness rationale</span>
                </div>
                <div>
                  <strong className="text-black font-serif font-bold text-lg block mb-1">3. Research gap & next steps</strong>
                  <span className="text-gray-700 text-sm">Suggested experimental validation approaches</span>
                </div>
              </div>

              <div className="bg-[#e8e6e0] border-l-4 border-gray-500 p-5 mt-8">
                <p className="text-sm text-gray-800 leading-relaxed">
                  <strong className="text-black">Disclaimer:</strong> AI-generated narratives are research aids for hypothesis 
                  generation and should not be interpreted as clinical recommendations. All findings require 
                  experimental validation through appropriate laboratory methods.
                </p>
              </div>
            </div>
          </motion.section>

          <motion.section id="citations" variants={fadeInUp} initial="hidden" whileInView="visible" viewport={{ once: true }} className="pt-8 border-t border-gray-300">
            <h2 className="text-2xl font-serif font-bold text-black mb-6">Citations</h2>
            <div className="space-y-6 text-sm text-gray-700 leading-relaxed max-w-4xl">
              <p>
                Trott, O., & Olson, A. J. (2010). AutoDock Vina: improving the speed and accuracy 
                of docking with a new scoring function, efficient optimization, and multithreading. 
                <em className="text-black font-medium"> Journal of Computational Chemistry</em>, 31(2), 455-461.
              </p>
              <p>
                Lipinski, C. A., Lombardo, F., Dominy, B. W., & Feeney, P. J. (2001). Experimental 
                and computational approaches to estimate solubility and permeability in drug discovery 
                and development settings. <em className="text-black font-medium">Advanced Drug Delivery Reviews</em>, 46(1-3), 3-26.
              </p>
              <p>
                Veber, D. F., Johnson, S. R., Cheng, H. Y., Smith, B. R., Ward, K. W., & Kopple, K. D. 
                (2002). Molecular properties that influence the oral bioavailability of drug candidates. 
                <em className="text-black font-medium"> Journal of Medicinal Chemistry</em>, 45(12), 2615-2623.
              </p>
              <p>
                Jumper, J., Evans, R., Pritzel, A., et al. (2021). Highly accurate protein structure 
                prediction with AlphaFold. <em className="text-black font-medium">Nature</em>, 596(7873), 583-589.
              </p>
            </div>
          </motion.section>
        </div>
      </div>
    </div>
  );
}
