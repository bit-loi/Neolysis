import { FormEvent, useCallback, useState } from 'react';

import {
  TargetConditions,
  VariantRankResponse,
  rankVariants,
  sampleEnzymeSequence,
} from '@/lib/enzyme-api';
import { defaultVariantConditions, defaultVariantInput, parseVariantInput } from '@/lib/variants';

const numericConditionKeys = new Set<keyof TargetConditions>([
  'temperature_c',
  'ph',
  'salinity_m_m',
]);

export function useVariantRanking() {
  const [wildType, setWildType] = useState(sampleEnzymeSequence);
  const [variantText, setVariantText] = useState(defaultVariantInput);
  const [conditions, setConditions] = useState<TargetConditions>(defaultVariantConditions);
  const [result, setResult] = useState<VariantRankResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const updateCondition = useCallback((key: keyof TargetConditions, value: string) => {
    setConditions((current) => ({
      ...current,
      [key]: numericConditionKeys.has(key) ? Number(value) : value,
    }));
  }, []);

  const submitRanking = useCallback(
    async (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      setLoading(true);
      setError(null);

      try {
        const variants = parseVariantInput(variantText);
        setResult(
          await rankVariants({
            wild_type_sequence: wildType,
            variants,
            target_conditions: conditions,
          })
        );
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Variant ranking failed');
      } finally {
        setLoading(false);
      }
    },
    [conditions, variantText, wildType]
  );

  return {
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
  };
}
