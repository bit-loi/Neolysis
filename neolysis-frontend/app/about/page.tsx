import Link from 'next/link';
import { ArrowRight, CheckCircle2, FlaskConical, ShieldAlert } from 'lucide-react';

export const metadata = {
  title: 'About | Neolysis',
  description: 'Neolysis is a computational enzyme intelligence platform for industrial biotechnology.',
};

export default function AboutPage() {
  return (
    <div className="min-h-screen bg-[#f5f5f0] pt-28 pb-16 text-[#171717] grain-overlay">
      <div className="relative z-10 mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        <div className="max-w-3xl">
          <p className="text-sm font-medium uppercase tracking-[0.2em] text-[#5BA8B9]">
            About Neolysis
          </p>
          <h1 className="mt-3 font-serif text-4xl font-bold tracking-tight sm:text-5xl">
            Enzyme engineering software for candidate prioritization.
          </h1>
          <p className="mt-6 text-lg leading-relaxed text-gray-700">
            Neolysis helps biotech and industrial R&amp;D teams analyze enzyme sequences, estimate relevant properties, prioritize variants, and plan wet-lab validation for industrial use cases.
          </p>
        </div>

        <div className="mt-12 grid gap-6 md:grid-cols-3">
          <section className="border border-gray-300 bg-white p-6">
            <FlaskConical className="h-6 w-6 text-[#5BA8B9]" />
            <h2 className="mt-5 font-serif text-2xl font-semibold">What it does</h2>
            <ul className="mt-4 space-y-3 text-sm leading-relaxed text-gray-700">
              <li>FASTA validation and sequence cleaning</li>
              <li>Protein feature extraction</li>
              <li>Baseline enzyme function prediction scaffold</li>
              <li>Industrial property scoring scaffold</li>
              <li>Variant ranking and mutation risk flags</li>
              <li>Agentic validation planning reports</li>
            </ul>
          </section>

          <section className="border border-gray-300 bg-white p-6">
            <CheckCircle2 className="h-6 w-6 text-[#5BA8B9]" />
            <h2 className="mt-5 font-serif text-2xl font-semibold">Who it serves</h2>
            <ul className="mt-4 space-y-3 text-sm leading-relaxed text-gray-700">
              <li>Industrial biotech R&amp;D teams</li>
              <li>Protein engineering labs</li>
              <li>Synthetic biology startups</li>
              <li>Food biotech, detergent, textile, and biofuel teams</li>
              <li>Academic enzyme engineering groups</li>
            </ul>
          </section>

          <section className="border border-gray-300 bg-white p-6">
            <ShieldAlert className="h-6 w-6 text-[#5BA8B9]" />
            <h2 className="mt-5 font-serif text-2xl font-semibold">What it is not</h2>
            <ul className="mt-4 space-y-3 text-sm leading-relaxed text-gray-700">
              <li>Not experimental proof of activity</li>
              <li>Not a guarantee of better enzymes</li>
              <li>Not a replacement for wet-lab validation</li>
              <li>Not an autonomous final protein design system</li>
            </ul>
          </section>
        </div>

        <section className="mt-10 border border-gray-300 bg-white p-8">
          <h2 className="font-serif text-3xl font-semibold">Scientific positioning</h2>
          <p className="mt-4 max-w-4xl leading-relaxed text-gray-700">
            The staging platform uses deterministic tools and baseline computational scaffolds to organize sequence-level evidence. The agentic layer coordinates those tools and explains outputs; it does not invent scientific results.
          </p>
          <Link href="/analyze" className="btn-bordered btn-bordered-dark mt-8">
            <ArrowRight className="h-4 w-4" />
            Analyze a Sequence
          </Link>
        </section>
      </div>
    </div>
  );
}
