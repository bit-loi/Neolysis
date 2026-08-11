'use client';

import {
  MethodologyLimitations,
  PresetSelector,
  QuantumPageHeader,
  QuantumTabs,
  QuboExplanation,
  SolverComparison,
  SolverErrorAlert,
  SolverLoadingPanel,
  VerificationBanner,
} from '@/components/variants/quantum';

import { useQuantumVariantRanking } from './useQuantumVariantRanking';

export default function QuantumVariantsPage() {
  const {
    activeTab,
    customRequest,
    error,
    loading,
    result,
    selectedPreset,
    rerunCurrentRequest,
    selectPreset,
    setActiveTab,
  } = useQuantumVariantRanking();

  return (
    <div className="min-h-screen bg-[#0b1329] px-4 pt-24 pb-16 font-sans text-gray-100 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl space-y-8">
        <QuantumPageHeader />

        <PresetSelector
          loading={loading}
          selectedPreset={selectedPreset}
          onRunOptimization={rerunCurrentRequest}
          onSelectPreset={selectPreset}
        />

        {error && <SolverErrorAlert message={error} />}
        {loading && <SolverLoadingPanel />}

        {!loading && result && (
          <div className="space-y-6">
            <VerificationBanner check={result.correctness_check} />

            <QuantumTabs activeTab={activeTab} onSelectTab={setActiveTab} />

            {activeTab === 'comparison' && (
              <SolverComparison request={customRequest} result={result} />
            )}
            {activeTab === 'qubo' && <QuboExplanation />}
            {activeTab === 'disclaimer' && (
              <MethodologyLimitations limitations={result.limitations} />
            )}
          </div>
        )}
      </div>
    </div>
  );
}
