import Link from 'next/link';
import { ExternalLink, Github, Linkedin } from 'lucide-react';

export function Footer() {
  return (
    <footer className="relative bg-[#081e24] text-gray-300 grain-overlay">
      <div className="relative z-10 mx-auto max-w-7xl px-6 py-16 lg:px-8 lg:py-20">
        <div className="grid grid-cols-1 gap-12 md:grid-cols-2 lg:grid-cols-4 lg:gap-8">
          <div>
            <span className="font-serif text-2xl font-bold tracking-tight text-[#7EC8D9]">
              NEOLYSIS
            </span>
            <p className="mt-4 max-w-xs text-sm leading-relaxed text-gray-400">
              Computational enzyme intelligence for industrial biotechnology. Built for candidate prioritization before wet-lab validation.
            </p>
          </div>

          <div>
            <h3 className="mb-6 text-sm font-medium uppercase tracking-wider text-white">
              Platform
            </h3>
            <ul className="space-y-3">
              {[
                ['Sequence Analysis', '/analyze'],
                ['Variant Ranking', '/variants'],
                ['Agentic Report', '/agent-report'],
                ['Methodology', '/methodology'],
              ].map(([label, href]) => (
                <li key={href}>
                  <Link href={href} className="text-sm text-gray-400 transition-colors hover:text-[#B2D8E5]">
                    {label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h3 className="mb-6 text-sm font-medium uppercase tracking-wider text-white">
              Scientific Stack
            </h3>
            <ul className="space-y-3">
              <li>
                <a href="https://biopython.org" target="_blank" rel="noopener noreferrer" className="flex items-center gap-1.5 text-sm text-gray-400 transition-colors hover:text-[#B2D8E5]">
                  Biopython <ExternalLink className="h-3 w-3" />
                </a>
              </li>
              <li>
                <a href="https://alphafold.ebi.ac.uk" target="_blank" rel="noopener noreferrer" className="flex items-center gap-1.5 text-sm text-gray-400 transition-colors hover:text-[#B2D8E5]">
                  AlphaFold DB <ExternalLink className="h-3 w-3" />
                </a>
              </li>
              <li>
                <a href="https://www.rcsb.org" target="_blank" rel="noopener noreferrer" className="flex items-center gap-1.5 text-sm text-gray-400 transition-colors hover:text-[#B2D8E5]">
                  RCSB PDB <ExternalLink className="h-3 w-3" />
                </a>
              </li>
            </ul>
          </div>

          <div>
            <h3 className="mb-6 text-sm font-medium uppercase tracking-wider text-white">
              Connect
            </h3>
            <div className="flex gap-4">
              <a href="https://github.com" target="_blank" rel="noopener noreferrer" className="flex h-10 w-10 items-center justify-center rounded-full border border-gray-700 text-gray-400 transition-colors hover:border-[#B2D8E5] hover:text-[#B2D8E5]" aria-label="GitHub">
                <Github className="h-4 w-4" />
              </a>
              <a href="#" className="flex h-10 w-10 items-center justify-center rounded-full border border-gray-700 text-gray-400 transition-colors hover:border-[#B2D8E5] hover:text-[#B2D8E5]" aria-label="LinkedIn">
                <Linkedin className="h-4 w-4" />
              </a>
            </div>
          </div>
        </div>

        <div className="mt-16 border-t border-[#1a3d44] pt-8">
          <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
            <p className="text-xs text-gray-500">
              (c) 2026 Neolysis. Computational estimates require wet-lab validation.
            </p>
            <div className="flex gap-6 text-xs text-gray-500">
              <span>Terms</span>
              <span>Privacy</span>
              <span>Scientific limitations</span>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
