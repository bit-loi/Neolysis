'use client';

import {
  RankedVariantsTable,
  VariantInputForm,
  VariantRankingHeader,
} from '@/components/variants/heuristic';

import { useVariantRanking } from './useVariantRanking';

export default function VariantsPage() {
  const {
    conditions,
    error,
    loading,
    result,
    submitRanking,
    updateCondition,
    setVariantText,
    setWildType,
    variantText,
    wildType,
  } = useVariantRanking();

  return (
    <div className="min-h-screen bg-[#f5f5f0] pt-28 pb-16 text-[#171717] grain-overlay">
      <div className="relative z-10 mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <VariantRankingHeader />

        <VariantInputForm
          conditions={conditions}
          error={error}
          loading={loading}
          variantText={variantText}
          wildType={wildType}
          onConditionChange={updateCondition}
          onSubmit={submitRanking}
          onVariantTextChange={setVariantText}
          onWildTypeChange={setWildType}
        />

        {result && <RankedVariantsTable result={result} />}
      </div>
    </div>
  );
}
