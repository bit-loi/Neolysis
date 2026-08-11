import type { FormEvent, ReactNode } from 'react';
import { AlertTriangle, GitBranch, ListChecks } from 'lucide-react';

import { TargetConditions } from '@/lib/enzyme-api';

interface VariantInputFormProps {
  conditions: TargetConditions;
  error: string | null;
  loading: boolean;
  variantText: string;
  wildType: string;
  onConditionChange: (key: keyof TargetConditions, value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onVariantTextChange: (value: string) => void;
  onWildTypeChange: (value: string) => void;
}

export function VariantInputForm({
  conditions,
  error,
  loading,
  variantText,
  wildType,
  onConditionChange,
  onSubmit,
  onVariantTextChange,
  onWildTypeChange,
}: VariantInputFormProps) {
  return (
    <form onSubmit={onSubmit} className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_420px]">
      <section className="space-y-6">
        <SequenceTextArea
          icon={<GitBranch className="h-5 w-5 text-[#5BA8B9]" />}
          label="Wild-type sequence"
          minHeight="min-h-[220px]"
          value={wildType}
          onChange={onWildTypeChange}
        />
        <SequenceTextArea
          icon={<ListChecks className="h-5 w-5 text-[#5BA8B9]" />}
          label="Candidate variants"
          minHeight="min-h-[160px]"
          value={variantText}
          onChange={onVariantTextChange}
        />
      </section>

      <TargetConditionsPanel
        conditions={conditions}
        error={error}
        loading={loading}
        onConditionChange={onConditionChange}
      />
    </form>
  );
}

function SequenceTextArea({
  icon,
  label,
  minHeight,
  value,
  onChange,
}: {
  icon: ReactNode;
  label: string;
  minHeight: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <div className="border border-gray-300 bg-white p-6">
      <div className="flex items-center gap-3">
        {icon}
        <h2 className="font-serif text-xl font-semibold">{label}</h2>
      </div>
      <textarea
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className={`mt-5 w-full resize-y border border-gray-300 bg-[#fbfbf8] p-4 font-mono text-sm outline-none focus:border-[#5BA8B9] ${minHeight}`}
        spellCheck={false}
      />
    </div>
  );
}

function TargetConditionsPanel({
  conditions,
  error,
  loading,
  onConditionChange,
}: {
  conditions: TargetConditions;
  error: string | null;
  loading: boolean;
  onConditionChange: (key: keyof TargetConditions, value: string) => void;
}) {
  return (
    <aside className="border border-gray-300 bg-white p-6">
      <h2 className="font-serif text-xl font-semibold">Target conditions</h2>
      <div className="mt-5 space-y-4">
        <NumberInput
          label="Temperature C"
          value={conditions.temperature_c ?? 0}
          onChange={(value) => onConditionChange('temperature_c', value)}
        />
        <NumberInput
          label="pH"
          step="0.1"
          value={conditions.ph ?? 7}
          onChange={(value) => onConditionChange('ph', value)}
        />
        <NumberInput
          label="Salinity mM"
          value={conditions.salinity_m_m ?? 0}
          onChange={(value) => onConditionChange('salinity_m_m', value)}
        />
        <SelectInput
          label="Use case"
          value={conditions.use_case || 'custom'}
          options={['detergent', 'food biotech', 'textile', 'biofuel', 'academic research', 'custom']}
          onChange={(value) => onConditionChange('use_case', value)}
        />
        <SelectInput
          label="Solvent exposure"
          value={conditions.solvent_exposure || 'none'}
          options={['none', 'low', 'moderate', 'high']}
          onChange={(value) => onConditionChange('solvent_exposure', value)}
        />
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
  );
}

function NumberInput({
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

function SelectInput({
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
