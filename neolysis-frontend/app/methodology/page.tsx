import Link from 'next/link';
import { ArrowRight, Bot, FileText, GitBranch, Microscope, ShieldAlert } from 'lucide-react';

export const metadata = {
  title: 'Methodology | Neolysis',
  description: 'Sequence validation, feature extraction, baseline scoring, variant ranking, and agentic report generation methodology.',
};

const sections = [
  {
    title: 'Sequence validation',
    icon: FileText,
    body: 'FASTA or raw protein input is cleaned, uppercased, and checked against canonical amino acid residues. Invalid or ambiguous residues are returned as structured warnings.',
  },
  {
    title: 'Protein feature extraction',
    icon: Microscope,
    body: 'The backend extracts sequence length, amino acid composition, molecular weight, GRAVY, aromaticity, instability index, and isoelectric point when available. Biopython is used when present, with a transparent fallback for staging.',
  },
  {
    title: 'Industrial property scoring',
    icon: ShieldAlert,
    body: 'Thermostability, pH fit, solubility, and condition fit are baseline sequence-derived indicators. They are prioritization signals, not measured process performance.',
  },
  {
    title: 'Variant ranking',
    icon: GitBranch,
    body: 'Candidate variants are ranked by baseline industrial fit adjusted by mutation risk. Risk flags highlight changes that may affect folding, charge interactions, supplied active-site positions, or supplied conserved motifs.',
  },
  {
    title: 'Agentic orchestration',
    icon: Bot,
    body: 'The agent calls structured tools in order, records each call, and generates a report from tool outputs only. Missing data is reported as a limitation instead of being inferred.',
  },
];

export default function MethodologyPage() {
  return (
    <div className="min-h-screen bg-[#f5f5f0] pt-28 pb-16 text-[#171717] grain-overlay">
      <div className="relative z-10 mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        <div className="max-w-3xl">
          <p className="text-sm font-medium uppercase tracking-[0.2em] text-[#5BA8B9]">
            Methodology
          </p>
          <h1 className="mt-3 font-serif text-4xl font-bold tracking-tight sm:text-5xl">
            Transparent computational screening for enzyme engineering.
          </h1>
          <p className="mt-6 text-lg leading-relaxed text-gray-700">
            Neolysis staging prioritizes reliable workflow structure over exaggerated model claims. Every prediction is labeled as a baseline or computational estimate.
          </p>
        </div>

        <div className="mt-12 grid gap-6 md:grid-cols-2">
          {sections.map((section) => {
            const Icon = section.icon;
            return (
              <section key={section.title} className="border border-gray-300 bg-white p-6">
                <Icon className="h-6 w-6 text-[#5BA8B9]" />
                <h2 className="mt-5 font-serif text-2xl font-semibold">{section.title}</h2>
                <p className="mt-4 text-sm leading-relaxed text-gray-700">{section.body}</p>
              </section>
            );
          })}
        </div>

        <section className="mt-10 border border-gray-300 bg-white p-8">
          <h2 className="font-serif text-3xl font-semibold">Required limitation</h2>
          <p className="mt-4 max-w-4xl leading-relaxed text-gray-700">
            These results are computational estimates intended for candidate prioritization. Experimental wet-lab validation is required before industrial use.
          </p>
          <Link href="/agent-report" className="btn-bordered btn-bordered-dark mt-8">
            <ArrowRight className="h-4 w-4" />
            Generate Agentic Report
          </Link>
        </section>
      </div>
    </div>
  );
}
