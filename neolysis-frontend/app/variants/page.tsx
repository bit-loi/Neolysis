'use client';

import { FormEvent, useState } from 'react';
import { AlertTriangle, GitBranch, ListChecks } from 'lucide-react';
import {
  RankedVariant,
  TargetConditions,
  VariantCandidate,
  VariantRankResponse,
  rankVariants,
  sampleEnzymeSequence,
} from '@/lib/enzyme-api';

const defaultConditions: TargetConditions = {
  temperature_c: 60,
  ph: 10,
  salinity_m_m: 250,
  solvent_exposure: 'moderate',
  use_case: 'detergent',
};

export default function VariantsPage() {
  const [wildType, setWildType] = useState(sampleEnzymeSequence);
  const [variantText, setVariantText] = useState('V1: M1A\nV2: C75S\nV3: G120A');
  const [conditions, setConditions] = useState<TargetConditions>(defaultConditions);
  const [result, setResult] = useState<VariantRankResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const updateCondition = (key: keyof TargetConditions, value: string) => {
    setConditions((current) => ({
      ...current,
      [key]: ['temperature_c', 'ph', 'salinity_m_m'].includes(key)
        ? Number(value)
        : value,
    }));
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const variants = parseVariants(variantText);
      const response = await rankVariants({
        wild_type_sequence: wildType,
        variants,
        target_conditions: conditions,
      });
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Variant ranking failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#f5f5f0] pt-28 pb-16 text-[#171717] grain-overlay">
      <div className="relative z-10 mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="mb-10 max-w-3xl">
          <p className="text-sm font-medium uppercase tracking-[0.2em] text-[#5BA8B9]">
            Variant Ranking
          </p>
          <h1 className="mt-3 text-4xl font-serif font-bold tracking-tight sm:text-5xl">
            Prioritize candidate variants
          </h1>
          <p className="mt-4 text-lg leading-relaxed text-gray-700">
            Compare mutation candidates against industrial conditions with baseline fit and risk scoring.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_420px]">
          <section className="space-y-6">
            <div className="border border-gray-300 bg-white p-6">
              <div className="flex items-center gap-3">
                <GitBranch className="h-5 w-5 text-[#5BA8B9]" />
                <h2 className="text-xl font-serif font-semibold">Wild-type sequence</h2>
              </div>
              <textarea
                value={wildType}
                onChange={(event) => setWildType(event.target.value)}
                className="mt-5 min-h-[220px] w-full resize-y border border-gray-300 bg-[#fbfbf8] p-4 font-mono text-sm outline-none focus:border-[#5BA8B9]"
                spellCheck={false}
              />
            </div>

            <div className="border border-gray-300 bg-white p-6">
              <div className="flex items-center gap-3">
                <ListChecks className="h-5 w-5 text-[#5BA8B9]" />
                <h2 className="text-xl font-serif font-semibold">Candidate variants</h2>
              </div>
              <textarea
                value={variantText}
                onChange={(event) => setVariantText(event.target.value)}
                className="mt-5 min-h-[160px] w-full resize-y border border-gray-300 bg-[#fbfbf8] p-4 font-mono text-sm outline-none focus:border-[#5BA8B9]"
                spellCheck={false}
              />
            </div>
          </section>

          <aside className="border border-gray-300 bg-white p-6">
            <h2 className="text-xl font-serif font-semibold">Target conditions</h2>
            <div className="mt-5 space-y-4">
              <Input label="Temperature C" value={conditions.temperature_c ?? 0} onChange={(value) => updateCondition('temperature_c', value)} />
              <Input label="pH" value={conditions.ph ?? 7} onChange={(value) => updateCondition('ph', value)} step="0.1" />
              <Input label="Salinity mM" value={conditions.salinity_m_m ?? 0} onChange={(value) => updateCondition('salinity_m_m', value)} />
              <Select label="Use case" value={conditions.use_case || 'custom'} options={['detergent', 'food biotech', 'textile', 'biofuel', 'academic research', 'custom']} onChange={(value) => updateCondition('use_case', value)} />
              <Select label="Solvent exposure" value={conditions.solvent_exposure || 'none'} options={['none', 'low', 'moderate', 'high']} onChange={(value) => updateCondition('solvent_exposure', value)} />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="mt-6 w-full border border-black px-6 py-3 text-sm font-medium uppercase tracking-wide transition hover:border-[#5BA8B9] hover:text-[#5BA8B9] disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? 'Ranking...' : 'Rank variants'}
            </button>
            {error && (
              <p className="mt-4 flex items-start gap-2 text-sm text-rose-700">
                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
                {error}
              </p>
            )}
          </aside>
        </form>

        {result && (
          <section className="mt-8 border border-gray-300 bg-white p-6">
            <h2 className="text-2xl font-serif font-semibold">Ranked variants</h2>
            <div className="mt-5 overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 text-left text-gray-500">
                    <th className="py-3 pr-4">Rank</th>
                    <th className="py-3 pr-4">Variant</th>
                    <th className="py-3 pr-4">Mutation summary</th>
                    <th className="py-3 pr-4">Fit</th>
                    <th className="py-3 pr-4">Risk</th>
                    <th className="py-3 pr-4">Priority</th>
                  </tr>
                </thead>
                <tbody>
                  {result.ranked_variants.map((variant) => (
                    <VariantRow key={variant.variant_id} variant={variant} />
                  ))}
                </tbody>
              </table>
            </div>
            <p className="mt-5 text-sm text-gray-600">
              These rankings are computational estimates for candidate prioritization. Wet-lab validation is required before industrial use.
            </p>
          </section>
        )}
      </div>
    </div>
  );
}

function parseVariants(text: string): VariantCandidate[] {
  return text
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line, index) => {
      const colonIndex = line.indexOf(':');
      const idPart = colonIndex >= 0 ? line.slice(0, colonIndex) : `V${index + 1}`;
      const value = (colonIndex >= 0 ? line.slice(colonIndex + 1) : line).trim();
      const looksLikeSequence = /^[ACDEFGHIKLMNPQRSTVWY]{30,}$/i.test(value);
      return looksLikeSequence
        ? { variant_id: idPart.trim(), sequence: value.toUpperCase() }
        : {
            variant_id: idPart.trim(),
            mutations: value.split(/[,\s]+/).map((item) => item.trim()).filter(Boolean),
          };
    });
}

function VariantRow({ variant }: { variant: RankedVariant }) {
  return (
    <tr className="border-b border-gray-100">
      <td className="py-4 pr-4 font-medium">#{variant.rank}</td>
      <td className="py-4 pr-4">{variant.variant_id}</td>
      <td className="max-w-md py-4 pr-4 font-mono text-xs">{variant.mutation_summary}</td>
      <td className="py-4 pr-4">{variant.predicted_fit_score.toFixed(2)}</td>
      <td className="py-4 pr-4">{variant.risk_score.toFixed(2)}</td>
      <td className="py-4 pr-4 capitalize">{variant.wet_lab_priority}</td>
    </tr>
  );
}

function Input({
  label,
  value,
  onChange,
  step,
}: {
  label: string;
  value: string | number;
  onChange: (value: string) => void;
  step?: string;
}) {
  return (
    <label className="block text-sm font-medium text-gray-700">
      {label}
      <input
        type="number"
        step={step}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="mt-2 w-full border border-gray-300 bg-[#fbfbf8] px-3 py-2 text-black outline-none focus:border-[#5BA8B9]"
      />
    </label>
  );
}

function Select({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: string[];
  onChange: (value: string) => void;
}) {
  return (
    <label className="block text-sm font-medium text-gray-700">
      {label}
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="mt-2 w-full border border-gray-300 bg-[#fbfbf8] px-3 py-2 text-black outline-none focus:border-[#5BA8B9]"
      >
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </label>
  );
}
