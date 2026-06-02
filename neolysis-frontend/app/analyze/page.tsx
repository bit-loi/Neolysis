'use client';

import { ChangeEvent, FormEvent, ReactNode, useState } from 'react';
import { Activity, AlertTriangle, CheckCircle2, FileText, FlaskConical } from 'lucide-react';
import {
  AgentAnalysisResponse,
  TargetConditions,
  analyzeSequence,
  sampleEnzymeSequence,
} from '@/lib/enzyme-api';

const defaultConditions: TargetConditions = {
  temperature_c: 60,
  ph: 10,
  salinity_m_m: 250,
  solvent_exposure: 'moderate',
  use_case: 'detergent',
};

export default function AnalyzePage() {
  const [sequence, setSequence] = useState(`>alkaline_protease_candidate\n${sampleEnzymeSequence}`);
  const [conditions, setConditions] = useState<TargetConditions>(defaultConditions);
  const [result, setResult] = useState<AgentAnalysisResponse | null>(null);
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

  const handleFile = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setSequence(await file.text());
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const response = await analyzeSequence({
        sequence,
        target_conditions: conditions,
        user_question: 'Prioritize this enzyme candidate for the selected industrial conditions.',
      });
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed');
    } finally {
      setLoading(false);
    }
  };

  const validation = result?.structured_analysis.sequence?.validation;
  const features = result?.structured_analysis.sequence?.features;
  const prediction = result?.structured_analysis.enzyme_function?.prediction;
  const scoring = result?.structured_analysis.property_scoring;

  return (
    <div className="min-h-screen bg-[#f5f5f0] pt-28 pb-16 text-[#171717] grain-overlay">
      <div className="relative z-10 mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="mb-10 max-w-3xl">
          <p className="text-sm font-medium uppercase tracking-[0.2em] text-[#5BA8B9]">
            Sequence Analysis
          </p>
          <h1 className="mt-3 text-4xl font-serif font-bold tracking-tight sm:text-5xl">
            Enzyme candidate screening
          </h1>
          <p className="mt-4 text-lg leading-relaxed text-gray-700">
            Validate an enzyme sequence, estimate baseline protein properties, and generate a wet-lab validation report.
          </p>
        </div>

        <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_420px]">
          <form onSubmit={handleSubmit} className="space-y-6">
            <section className="border border-gray-300 bg-white p-6">
              <div className="flex items-center gap-3">
                <FileText className="h-5 w-5 text-[#5BA8B9]" />
                <h2 className="text-xl font-serif font-semibold">Protein FASTA</h2>
              </div>
              <textarea
                value={sequence}
                onChange={(event) => setSequence(event.target.value)}
                className="mt-5 min-h-[320px] w-full resize-y border border-gray-300 bg-[#fbfbf8] p-4 font-mono text-sm outline-none focus:border-[#5BA8B9]"
                spellCheck={false}
              />
              <div className="mt-4 flex flex-wrap items-center gap-3">
                <label className="inline-flex cursor-pointer items-center gap-2 border border-gray-300 px-4 py-2 text-sm hover:border-[#5BA8B9]">
                  Upload FASTA
                  <input
                    type="file"
                    accept=".fasta,.fa,.txt"
                    className="hidden"
                    onChange={handleFile}
                  />
                </label>
                <button
                  type="button"
                  className="border border-gray-300 px-4 py-2 text-sm hover:border-[#5BA8B9]"
                  onClick={() => setSequence(`>alkaline_protease_candidate\n${sampleEnzymeSequence}`)}
                >
                  Load sample
                </button>
              </div>
            </section>

            <section className="border border-gray-300 bg-white p-6">
              <div className="flex items-center gap-3">
                <FlaskConical className="h-5 w-5 text-[#5BA8B9]" />
                <h2 className="text-xl font-serif font-semibold">Industrial conditions</h2>
              </div>
              <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                <LabeledInput
                  label="Temperature C"
                  type="number"
                  value={conditions.temperature_c ?? 0}
                  onChange={(value) => updateCondition('temperature_c', value)}
                />
                <LabeledInput
                  label="pH"
                  type="number"
                  step="0.1"
                  value={conditions.ph ?? 7}
                  onChange={(value) => updateCondition('ph', value)}
                />
                <LabeledInput
                  label="Salinity mM"
                  type="number"
                  value={conditions.salinity_m_m ?? 0}
                  onChange={(value) => updateCondition('salinity_m_m', value)}
                />
                <LabeledSelect
                  label="Solvent exposure"
                  value={conditions.solvent_exposure || 'none'}
                  options={['none', 'low', 'moderate', 'high']}
                  onChange={(value) => updateCondition('solvent_exposure', value)}
                />
                <LabeledSelect
                  label="Use case"
                  value={conditions.use_case || 'custom'}
                  options={['detergent', 'food biotech', 'textile', 'biofuel', 'academic research', 'custom']}
                  onChange={(value) => updateCondition('use_case', value)}
                />
              </div>
              <button
                type="submit"
                disabled={loading}
                className="mt-6 inline-flex items-center gap-3 border border-black px-6 py-3 text-sm font-medium uppercase tracking-wide transition hover:border-[#5BA8B9] hover:text-[#5BA8B9] disabled:cursor-not-allowed disabled:opacity-50"
              >
                <Activity className="h-4 w-4" />
                {loading ? 'Analyzing...' : 'Run analysis'}
              </button>
              {error && (
                <p className="mt-4 flex items-center gap-2 text-sm text-rose-700">
                  <AlertTriangle className="h-4 w-4" />
                  {error}
                </p>
              )}
            </section>
          </form>

          <aside className="space-y-5">
            <ResultPanel title="Sequence Quality" icon={<CheckCircle2 className="h-5 w-5" />}>
              {validation ? (
                <dl className="space-y-2 text-sm">
                  <Metric label="Status" value={validation.valid ? 'Valid' : 'Needs review'} />
                  <Metric label="Length" value={`${validation.sequence_length} aa`} />
                  <Metric label="Format" value={validation.detected_format} />
                  <Metric label="Warnings" value={validation.warnings.length ? validation.warnings.join(', ') : 'None'} />
                </dl>
              ) : (
                <p className="text-sm text-gray-600">Results will appear after analysis.</p>
              )}
            </ResultPanel>

            <ResultPanel title="Protein Features" icon={<Activity className="h-5 w-5" />}>
              {features ? (
                <dl className="space-y-2 text-sm">
                  <Metric label="Molecular weight" value={`${features.molecular_weight.toLocaleString()} Da`} />
                  <Metric label="GRAVY" value={features.gravy ?? 'N/A'} />
                  <Metric label="Isoelectric point" value={features.isoelectric_point ?? 'N/A'} />
                  <Metric label="Method" value={features.method} />
                </dl>
              ) : (
                <p className="text-sm text-gray-600">No feature result yet.</p>
              )}
            </ResultPanel>

            <ResultPanel title="Industrial Fit" icon={<FlaskConical className="h-5 w-5" />}>
              {scoring ? (
                <dl className="space-y-2 text-sm">
                  <Metric label="Fit score" value={scoring.industrial_fit_score.toFixed(2)} />
                  <Metric label="Thermostability" value={scoring.thermostability.label} />
                  <Metric label="pH fit" value={scoring.ph_fit.label} />
                  <Metric label="Solubility" value={scoring.solubility.label} />
                  <Metric label="Confidence" value={scoring.confidence.toFixed(2)} />
                </dl>
              ) : (
                <p className="text-sm text-gray-600">No scoring result yet.</p>
              )}
            </ResultPanel>
          </aside>
        </div>

        {result && (
          <section className="mt-8 border border-gray-300 bg-white p-6">
            <h2 className="text-2xl font-serif font-semibold">Agentic report</h2>
            {prediction && (
              <p className="mt-3 text-gray-700">
                Baseline function scaffold: <span className="font-medium text-black">{prediction.predicted_family}</span>
              </p>
            )}
            <pre className="mt-5 max-h-[520px] overflow-auto whitespace-pre-wrap bg-[#081e24] p-5 text-sm leading-relaxed text-gray-100">
              {result.final_report}
            </pre>
          </section>
        )}
      </div>
    </div>
  );
}

function LabeledInput({
  label,
  value,
  onChange,
  type,
  step,
}: {
  label: string;
  value: string | number;
  onChange: (value: string) => void;
  type: string;
  step?: string;
}) {
  return (
    <label className="block text-sm font-medium text-gray-700">
      {label}
      <input
        type={type}
        step={step}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="mt-2 w-full border border-gray-300 bg-[#fbfbf8] px-3 py-2 text-black outline-none focus:border-[#5BA8B9]"
      />
    </label>
  );
}

function LabeledSelect({
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

function ResultPanel({
  title,
  icon,
  children,
}: {
  title: string;
  icon: ReactNode;
  children: ReactNode;
}) {
  return (
    <section className="border border-gray-300 bg-white p-5">
      <div className="mb-4 flex items-center gap-3 text-[#5BA8B9]">
        {icon}
        <h2 className="font-serif text-xl font-semibold text-black">{title}</h2>
      </div>
      {children}
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-gray-100 pb-2 last:border-b-0">
      <dt className="text-gray-500">{label}</dt>
      <dd className="max-w-[220px] text-right font-medium text-black">{value}</dd>
    </div>
  );
}
