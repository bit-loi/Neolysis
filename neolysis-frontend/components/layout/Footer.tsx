import Link from 'next/link';
import { Github, Linkedin, ExternalLink } from 'lucide-react';

export function Footer() {
  return (
    <footer className="bg-[#081e24] text-gray-300 grain-overlay relative">
      <div className="relative z-10 mx-auto max-w-7xl px-6 lg:px-8 py-16 lg:py-20">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-12 lg:gap-8">
          {/* About Neolysis */}
          <div className="lg:col-span-1">
            <span className="text-2xl font-bold font-serif text-[#7EC8D9] tracking-tight">
              NEOLYSIS
            </span>
            <p className="mt-4 text-sm text-gray-400 leading-relaxed max-w-xs">
              Open-access AI-powered drug discovery platform for ASEAN neglected
              tropical disease research. Accelerating therapeutic development
              through computational analysis.
            </p>
          </div>

          {/* Platform */}
          <div>
            <h3 className="text-sm font-medium text-white tracking-wider uppercase mb-6">
              Platform
            </h3>
            <ul className="space-y-3">
              <li>
                <Link
                  href="/targets"
                  className="text-sm text-gray-400 hover:text-[#B2D8E5] transition-colors"
                >
                  Protein Targets
                </Link>
              </li>
              <li>
                <Link
                  href="/methodology"
                  className="text-sm text-gray-400 hover:text-[#B2D8E5] transition-colors"
                >
                  Methodology
                </Link>
              </li>
              <li>
                <Link
                  href="/about"
                  className="text-sm text-gray-400 hover:text-[#B2D8E5] transition-colors"
                >
                  About
                </Link>
              </li>
            </ul>
          </div>

          {/* Data Sources */}
          <div>
            <h3 className="text-sm font-medium text-white tracking-wider uppercase mb-6">
              Data Sources
            </h3>
            <ul className="space-y-3">
              <li>
                <a
                  href="https://alphafold.ebi.ac.uk"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-gray-400 hover:text-[#B2D8E5] transition-colors flex items-center gap-1.5"
                >
                  AlphaFold DB <ExternalLink className="h-3 w-3" />
                </a>
              </li>
              <li>
                <a
                  href="https://www.rcsb.org"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-gray-400 hover:text-[#B2D8E5] transition-colors flex items-center gap-1.5"
                >
                  RCSB PDB <ExternalLink className="h-3 w-3" />
                </a>
              </li>
              <li>
                <a
                  href="https://pubchem.ncbi.nlm.nih.gov"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-gray-400 hover:text-[#B2D8E5] transition-colors flex items-center gap-1.5"
                >
                  PubChem <ExternalLink className="h-3 w-3" />
                </a>
              </li>
            </ul>
          </div>

          {/* Stay Connected */}
          <div>
            <h3 className="text-sm font-medium text-white tracking-wider uppercase mb-6">
              Stay Connected
            </h3>
            <div className="flex gap-4">
              <a
                href="https://github.com"
                target="_blank"
                rel="noopener noreferrer"
                className="w-10 h-10 rounded-full border border-gray-700 flex items-center justify-center text-gray-400 hover:border-[#B2D8E5] hover:text-[#B2D8E5] transition-colors"
                aria-label="GitHub"
              >
                <Github className="h-4 w-4" />
              </a>
              <a
                href="#"
                className="w-10 h-10 rounded-full border border-gray-700 flex items-center justify-center text-gray-400 hover:border-[#B2D8E5] hover:text-[#B2D8E5] transition-colors"
                aria-label="LinkedIn"
              >
                <Linkedin className="h-4 w-4" />
              </a>
            </div>
          </div>
        </div>

        {/* Copyright */}
        <div className="mt-16 pt-8 border-t border-[#1a3d44]">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <p className="text-xs text-gray-500">
              © 2026 Neolysis, All Rights Reserved
            </p>
            <div className="flex gap-6">
              <span className="text-xs text-gray-500 hover:text-gray-400 cursor-pointer transition-colors">
                Terms &amp; Conditions
              </span>
              <span className="text-xs text-gray-500 hover:text-gray-400 cursor-pointer transition-colors">
                Privacy Policy
              </span>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
