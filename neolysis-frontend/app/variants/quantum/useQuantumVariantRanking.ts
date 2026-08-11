import { useCallback, useEffect, useState } from 'react';

import {
  PRESET_QUANTUM_SCENARIOS,
  PresetScenario,
  QuantumTab,
  QuantumVariantRankRequest,
  QuantumVariantRankResponse,
  rankQuantumVariants,
} from '@/lib/quantum';

export function useQuantumVariantRanking() {
  const [selectedPreset, setSelectedPreset] = useState<PresetScenario>(
    PRESET_QUANTUM_SCENARIOS[0]
  );
  const [customRequest, setCustomRequest] = useState<QuantumVariantRankRequest>(
    PRESET_QUANTUM_SCENARIOS[0].request
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<QuantumVariantRankResponse | null>(null);
  const [activeTab, setActiveTab] = useState<QuantumTab>('comparison');

  const runOptimization = useCallback(async (request: QuantumVariantRankRequest) => {
    setLoading(true);
    setError(null);

    try {
      setResult(await rankQuantumVariants(request));
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'An unexpected error occurred during quantum optimization.'
      );
    } finally {
      setLoading(false);
    }
  }, []);

  const selectPreset = useCallback((preset: PresetScenario) => {
    setSelectedPreset(preset);
    setCustomRequest(preset.request);
  }, []);

  const rerunCurrentRequest = useCallback(() => {
    void runOptimization(customRequest);
  }, [customRequest, runOptimization]);

  useEffect(() => {
    void runOptimization(selectedPreset.request);
  }, [runOptimization, selectedPreset]);

  return {
    activeTab,
    customRequest,
    error,
    loading,
    result,
    selectedPreset,
    rerunCurrentRequest,
    selectPreset,
    setActiveTab,
  };
}
