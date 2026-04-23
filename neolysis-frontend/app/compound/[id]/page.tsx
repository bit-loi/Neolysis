import { notFound } from 'next/navigation';
import Link from 'next/link';
import { getCompoundByCid, getDockingScoreForCompound } from '@/lib/docking';
import { getTargetById } from '@/lib/targets';
import { CompoundStructure } from '@/components/compound/CompoundStructure';
import { DockingScoreCard } from '@/components/compound/DockingScoreCard';
import { DrugLikeness } from '@/components/compound/DrugLikeness';
import { AIExplanation } from '@/components/compound/AIExplanation';
import { DISEASE_LABELS } from '@/lib/types';

interface CompoundPageProps {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ target?: string }>;
}

export async function generateStaticParams() {
  return [];
}

export async function generateMetadata({ params }: CompoundPageProps) {
  const { id } = await params;
  const compound = getCompoundByCid(id);
  
  return {
    title: compound
      ? `${compound.name} (CID ${id}) | Neolysis`
      : `Compound CID ${id} | Neolysis`,
    description: `Molecular docking analysis for compound CID ${id}.`,
  };
}

export default async function CompoundPage({ params, searchParams }: CompoundPageProps) {
  const { id } = await params;
  const { target: targetId } = await searchParams;
  
  const compound = getCompoundByCid(id);

  if (!compound) {
    notFound();
  }

  const target = targetId ? getTargetById(targetId) : null;
  const dockingScore = targetId ? getDockingScoreForCompound(id, targetId) : null;

  return (
    <div className="min-h-screen bg-[#f5f5f0] text-[#171717] pt-24 pb-16 grain-overlay">
      <div className="relative z-10 mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
        {/* Breadcrumb */}
        <div className="mb-6 flex items-center gap-2 text-sm text-gray-500">
          {target && (
            <>
              <span>{DISEASE_LABELS[target.disease]}</span>
              <span>/</span>
              <Link href={`/targets/${target.id}`} className="hover:text-black transition-colors">
                {target.name}
              </Link>
              <span>/</span>
            </>
          )}
          <span className="text-black font-medium">CID {id}</span>
        </div>

        <div className="space-y-6">
          <CompoundStructure compound={compound} />



          {dockingScore && target && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <DockingScoreCard dockingScore={dockingScore} target={target} />
              <DrugLikeness compound={compound} />
            </div>
          )}

          {!dockingScore && !target && (
            <DrugLikeness compound={compound} />
          )}

          {target && (
            <AIExplanation target={target} compound={compound} />
          )}
        </div>
      </div>
    </div>
  );
}