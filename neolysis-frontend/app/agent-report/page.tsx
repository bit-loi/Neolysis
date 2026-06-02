'use client';

import { FormEvent, useState } from 'react';
import { AlertTriangle, Bot, ClipboardList } from 'lucide-react';
import {
  AgentAnalysisResponse,
  TargetConditions,
  analyzeSequence,
  sampleEnzymeSequence,
} from '@/lib/enzyme-api';

const defaultConditions: TargetConditions = {
  temperature_c: 55,
  ph: 8,
  salinity_m_m: 100,
  solvent_exposure: 'low',
  use_case: 'food biotech',
};

export default function AgentReportPage() {
  const [question, setQuestion] = useState('Which validation steps should we prioritize for this enzyme candidate?');
  const [sequence, setSequence] = useState(sampleEnzymeSequence);
  const [conditions, setConditions] = useState<TargetConditions>(defaultConditions);
  const [result, setResult] = useState<AgentAnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
      setResult(await analyzeSequence({
        sequence,
        target_conditions: conditions,
        user_question: question,
      }));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Agent analysis failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#f5f5f0] pt-28 pb-16 text-[#171717] grain-overlay">
      <div className="relative z-10 mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="mb-10 max-w-3xl">
          <p className="text-sm font-medium uppercase tracking-[0.2em] text-[#5BA8B9]">
            Agentic Report
          </p>
          <h1 className="mt-3 text-4xl font-serif font-bold tracking-tight sm:text-5xl">
            Scientific workflow agent
          </h1>
          <p className="mt-4 text-lg leading-relaxed text-gray-700">
            The agent calls structured tools, records each step, and produces a validation planning report.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="grid gap-8 lg:grid-cols-[420px_minmax(0,1fr)]">
          <aside className="space-y-5">
            <section className="border border-gray-300 bg-white p-6">
              <div className="flex items-center gap-3">
                <Bot className="h-5 w-5 text-[#5BA8B9]" />
                <h2 className="text-xl font-serif font-semibold">Question</h2>
              </div>
              <textarea
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                className="mt-5 min-h-[120px] w-full resize-y border border-gray-300 bg-[#fbfbf8] p-4 text-sm outline-none focus:border-[#5BA8B9]"
              />
              <div className="mt-5 grid gap-4">
                <Input label="Temperature C" value={conditions.temperature_c ?? 0} onChange={(value) => updateCondition('temperature_c', value)} />
                <Input label="pH" value={conditions.ph ?? 7} onChange={(value) => updateCondition('ph', value)} step="0.1" />
                <Select label="Use case" value={conditions.use_case || 'custom'} options={['detergent', 'food biotech', 'textile', 'biofuel', 'academic research', 'custom']} onChange={(value) => updateCondition('use_case', value)} />
              </div>
              <button
                type="submit"
                disabled={loading}
                className="mt-6 w-full border border-black px-6 py-3 text-sm font-medium uppercase tracking-wide transition hover:border-[#5BA8B9] hover:text-[#5BA8B9] disabled:cursor-not-allowed disabled:opacity-50"
              >
                {loading ? 'Running agent...' : 'Generate report'}
              </button>
              {error && (
                <p className="mt-4 flex items-start gap-2 text-sm text-rose-700">
                  <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
                  {error}
                </p>
              )}
            </section>
          </aside>

          <section className="border border-gray-300 bg-white p-6">
            <div className="flex items-center gap-3">
              <ClipboardList className="h-5 w-5 text-[#5BA8B9]" />
              <h2 className="text-xl font-serif font-semibold">Sequence</h2>
            </div>
            <textarea
              value={sequence}
              onChange={(event) => setSequence(event.target.value)}
              className="mt-5 min-h-[260px] w-full resize-y border border-gray-300 bg-[#fbfbf8] p-4 font-mono text-sm outline-none focus:border-[#5BA8B9]"
              spellCheck={false}
            />
          </section>
        </form>

        {result && (
          <div className="mt-8 grid gap-8 lg:grid-cols-[360px_minmax(0,1fr)]">
            <section className="border border-gray-300 bg-white p-6">
              <h2 className="text-2xl font-serif font-semibold">Tool calls</h2>
              <ol className="mt-5 space-y-4">
                {result.tool_calls.map((call) => (
                  <li key={`${call.name}-${call.status}`} className="border-b border-gray-100 pb-4 last:border-b-0">
                    <p className="font-medium text-black">{call.name}</p>
                    <p className="mt-1 text-xs uppercase tracking-wide text-[#5BA8B9]">{call.status}</p>
                    <p className="mt-2 text-sm text-gray-600">{call.summary}</p>
                  </li>
                ))}
              </ol>
            </section>
            <section className="border border-gray-300 bg-white p-6">
              <h2 className="text-2xl font-serif font-semibold">Report</h2>
              <pre className="mt-5 max-h-[620px] overflow-auto whitespace-pre-wrap bg-[#081e24] p-5 text-sm leading-relaxed text-gray-100">
                {result.final_report}
              </pre>
            </section>
          </div>
        )}
      </div>
    </div>
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
