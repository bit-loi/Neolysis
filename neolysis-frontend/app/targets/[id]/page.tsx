import { notFound } from 'next/navigation';
import Link from 'next/link';
import { getTargetById } from '@/lib/targets';
import { getCompoundsWithDockingForTarget } from '@/lib/docking';
import { TargetInfo } from '@/components/explorer/TargetInfo';
import { ProteinViewer } from '@/components/explorer/ProteinViewer';
import { CompoundList } from '@/components/explorer/CompoundList';

interface TargetPageProps {
  params: Promise<{ id: string }>;
}

export const dynamic = 'force-dynamic';

export async function generateStaticParams() {
  return [];
}

export async function generateMetadata({ params }: TargetPageProps) {
  const { id } = await params;
  const target = getTargetById(id);
  
  if (!target) {
    return { title: 'Target Not Found' };
  }

  return {
    title: `${target.name} - ${target.fullName} | Neolysis`,
    description: target.description,
  };
}

export default async function TargetPage({ params }: TargetPageProps) {
  const { id } = await params;
  const target = getTargetById(id);

  if (!target) {
    notFound();
  }

  const compounds = getCompoundsWithDockingForTarget(target.id);

  return (
    <div className="min-h-screen bg-[#f5f5f0] text-[#171717] pt-24 pb-16 grain-overlay">
      <div className="relative z-10 mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <Link
          href="/targets"
          className="inline-flex items-center gap-2 mb-6 text-sm font-medium text-gray-500 hover:text-black transition-colors duration-200 group"
        >
          <span className="transform transition-transform group-hover:-translate-x-1">&larr;</span>
          Back to All Targets
        </Link>

        <TargetInfo target={target} />

        <div className="mt-8 grid grid-cols-1 lg:grid-cols-5 gap-6">
          <div className="lg:col-span-3">
            <ProteinViewer pdbId={target.pdbId} proteinName={target.name} alphafoldId={target.alphafoldId} />
          </div>
          <div className="lg:col-span-2">
            <CompoundList compounds={compounds} />
          </div>
        </div>
      </div>
    </div>
  );
}