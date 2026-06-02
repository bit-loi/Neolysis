'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Activity, Play, RefreshCcw, RotateCw, Settings } from 'lucide-react';
import {
  AtomPosition,
  ExperimentalMDSimulator,
  getExperimentalMDEngine,
  isMDEngineEnabled,
  normalizePositions,
} from '@/lib/experimental/md-engine';

const LIMITATION =
  'This experimental WASM simulation module demonstrates simplified browser-based molecular dynamics. It is not a validated protein dynamics engine and should not be used as experimental proof of enzyme activity, stability, or industrial performance.';

type EngineStatus = 'disabled' | 'loading' | 'loaded' | 'unavailable' | 'running' | 'error';

export function MolecularDynamicsSandbox() {
  const enabled = useMemo(() => isMDEngineEnabled(), []);
  const simulatorRef = useRef<ExperimentalMDSimulator | null>(null);
  const engineRef = useRef<Awaited<ReturnType<typeof getExperimentalMDEngine>> | null>(null);
  const [status, setStatus] = useState<EngineStatus>(enabled ? 'loading' : 'disabled');
  const [positions, setPositions] = useState<AtomPosition[]>([]);
  const [atomCount, setAtomCount] = useState(0);
  const [stepCount, setStepCount] = useState(0);
  const [timestep, setTimestep] = useState(0.001);
  const [epsilon, setEpsilon] = useState(1);
  const [sigma, setSigma] = useState(1);
  const [errorMessage, setErrorMessage] = useState('');

  const refreshState = useCallback(() => {
    const simulator = simulatorRef.current;

    if (!simulator) {
      setPositions([]);
      setAtomCount(0);
      setStepCount(0);
      return;
    }

    setAtomCount(simulator.atom_count());
    setStepCount(simulator.current_step?.() ?? 0);
    setPositions(normalizePositions(simulator.get_positions()));
  }, []);

  const applySettings = useCallback(() => {
    const simulator = simulatorRef.current;

    if (!simulator) {
      return;
    }

    simulator.set_timestep?.(timestep);
    simulator.set_lennard_jones_params?.(epsilon, sigma);
  }, [epsilon, sigma, timestep]);

  const initializeDemo = useCallback(() => {
    const simulator = simulatorRef.current;

    if (!simulator) {
      return;
    }

    if (simulator.reset) {
      simulator.reset();
    } else if (simulator.atom_count() > 0 && engineRef.current) {
      simulatorRef.current = new engineRef.current.MDSimulator(timestep);
    }

    applySettings();

    const activeSimulator = simulatorRef.current;

    if (!activeSimulator) {
      return;
    }

    const addAtom = activeSimulator.add_atom.bind(activeSimulator);

    if (addAtom.length >= 9) {
      addAtom('O', 16.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0);
      addAtom('H', 1.0, 0.96, 0.0, 0.0, 0.0, 0.01, 0.0);
      addAtom('H', 1.0, -0.24, 0.93, 0.0, 0.0, -0.01, 0.0);
    } else {
      addAtom(0.0, 0.0, 0.0, 16.0, 'O');
      addAtom(0.96, 0.0, 0.0, 1.0, 'H');
      addAtom(-0.24, 0.93, 0.0, 1.0, 'H');
    }

    setStatus('loaded');
    refreshState();
  }, [applySettings, refreshState, timestep]);

  useEffect(() => {
    if (!enabled) {
      return;
    }

    let cancelled = false;

    async function loadEngine() {
      try {
        const engine = await getExperimentalMDEngine();

        if (cancelled) {
          return;
        }

        engineRef.current = engine;
        simulatorRef.current = new engine.MDSimulator(0.001);
        setStatus('loaded');
        setErrorMessage('');
        setTimeout(() => {
          if (!cancelled) {
            initializeDemo();
          }
        }, 0);
      } catch (error) {
        if (cancelled) {
          return;
        }

        console.error('Neolysis: Failed to load experimental MD engine:', error);
        setStatus('unavailable');
        setErrorMessage(
          'Experimental molecular simulation module unavailable. Core sequence analysis remains available.'
        );
      }
    }

    loadEngine();

    return () => {
      cancelled = true;
    };
  }, [enabled, initializeDemo, timestep]);

  const stepSimulation = () => {
    const simulator = simulatorRef.current;

    if (!simulator) {
      return;
    }

    setStatus('running');
    applySettings();

    try {
      if (typeof simulator.step === 'function') {
        simulator.step();
      }

      setStatus('loaded');
      refreshState();
    } catch (error) {
      console.error('Neolysis: Experimental MD step failed:', error);
      setStatus('error');
      setErrorMessage('Simulation step failed. Core sequence analysis remains available.');
    }
  };

  const runTenSteps = () => {
    const simulator = simulatorRef.current;

    if (!simulator) {
      return;
    }

    setStatus('running');
    applySettings();

    try {
      if (simulator.run_steps) {
        simulator.run_steps(10);
      } else if (typeof simulator.step === 'function') {
        for (let i = 0; i < 10; i += 1) {
          simulator.step();
        }
      }

      setStatus('loaded');
      refreshState();
    } catch (error) {
      console.error('Neolysis: Experimental MD run failed:', error);
      setStatus('error');
      setErrorMessage('Simulation run failed. Core sequence analysis remains available.');
    }
  };

  const resetSimulation = () => {
    if (simulatorRef.current?.reset) {
      simulatorRef.current.reset();
      initializeDemo();
      return;
    }

    initializeDemo();
  };

  if (!enabled) {
    return (
      <ExperimentalShell status="disabled">
        <p className="rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          Experimental molecular dynamics sandbox is disabled. Core enzyme sequence analysis remains available.
        </p>
      </ExperimentalShell>
    );
  }

  return (
    <ExperimentalShell status={status}>
      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_320px]">
        <section className="space-y-4">
          <div className="rounded-md border border-gray-200 bg-white">
            <div className="border-b border-gray-200 px-4 py-3">
              <h2 className="text-sm font-semibold text-gray-900">Toy Particle Positions</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[520px] text-left text-sm">
                <thead className="bg-gray-50 text-xs uppercase text-gray-500">
                  <tr>
                    <th className="px-4 py-3">ID</th>
                    <th className="px-4 py-3">Label</th>
                    <th className="px-4 py-3">X</th>
                    <th className="px-4 py-3">Y</th>
                    <th className="px-4 py-3">Z</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {positions.map((atom) => (
                    <tr key={atom.id}>
                      <td className="px-4 py-3 font-mono text-gray-700">{atom.id}</td>
                      <td className="px-4 py-3 font-medium text-gray-900">{atom.label}</td>
                      <td className="px-4 py-3 font-mono text-gray-700">{atom.x.toFixed(6)}</td>
                      <td className="px-4 py-3 font-mono text-gray-700">{atom.y.toFixed(6)}</td>
                      <td className="px-4 py-3 font-mono text-gray-700">{atom.z.toFixed(6)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {errorMessage ? (
            <p className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
              {errorMessage}
            </p>
          ) : null}
        </section>

        <aside className="space-y-4">
          <div className="rounded-md border border-gray-200 bg-white p-4">
            <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-gray-900">
              <Activity className="h-4 w-4 text-[#5BA8B9]" />
              Status
            </div>
            <dl className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <dt className="text-gray-500">WASM</dt>
                <dd className="font-medium capitalize text-gray-900">{status}</dd>
              </div>
              <div>
                <dt className="text-gray-500">Atoms</dt>
                <dd className="font-medium text-gray-900">{atomCount}</dd>
              </div>
              <div>
                <dt className="text-gray-500">Steps</dt>
                <dd className="font-medium text-gray-900">{stepCount}</dd>
              </div>
            </dl>
          </div>

          <div className="rounded-md border border-gray-200 bg-white p-4">
            <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-gray-900">
              <Settings className="h-4 w-4 text-[#5BA8B9]" />
              Parameters
            </div>
            <div className="space-y-3">
              <NumberField label="Timestep" value={timestep} step={0.001} onChange={setTimestep} />
              <NumberField label="Epsilon" value={epsilon} step={0.1} onChange={setEpsilon} />
              <NumberField label="Sigma" value={sigma} step={0.1} onChange={setSigma} />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={initializeDemo}
              className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-gray-900 px-3 text-sm font-medium text-white hover:bg-gray-800"
            >
              <RefreshCcw className="h-4 w-4" />
              Init
            </button>
            <button
              type="button"
              onClick={stepSimulation}
              className="inline-flex h-10 items-center justify-center gap-2 rounded-md border border-gray-300 px-3 text-sm font-medium text-gray-800 hover:bg-gray-50"
            >
              <Play className="h-4 w-4" />
              Step
            </button>
            <button
              type="button"
              onClick={runTenSteps}
              className="inline-flex h-10 items-center justify-center gap-2 rounded-md border border-gray-300 px-3 text-sm font-medium text-gray-800 hover:bg-gray-50"
            >
              <Play className="h-4 w-4" />
              Run 10
            </button>
            <button
              type="button"
              onClick={resetSimulation}
              className="inline-flex h-10 items-center justify-center gap-2 rounded-md border border-gray-300 px-3 text-sm font-medium text-gray-800 hover:bg-gray-50"
            >
              <RotateCw className="h-4 w-4" />
              Reset
            </button>
          </div>
        </aside>
      </div>
    </ExperimentalShell>
  );
}

function ExperimentalShell({
  children,
  status,
}: {
  children: React.ReactNode;
  status: EngineStatus;
}) {
  return (
    <div className="min-h-screen bg-[#f8faf8] px-6 pb-16 pt-28 text-gray-900">
      <div className="mx-auto max-w-6xl">
        <div className="mb-8">
          <p className="mb-3 text-xs font-semibold uppercase tracking-[0.18em] text-[#5BA8B9]">
            Experimental Module
          </p>
          <h1 className="text-3xl font-semibold tracking-tight text-gray-950 md:text-4xl">
            Experimental WASM Molecular Dynamics Sandbox
          </h1>
          <p className="mt-3 max-w-3xl text-base leading-7 text-gray-600">
            A lightweight Rust/WASM numerical simulation module for future structure-aware enzyme engineering.
          </p>
        </div>

        <div className="mb-6 rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm leading-6 text-amber-950">
          {LIMITATION}
        </div>

        <div className="mb-4 text-sm text-gray-600">Status: {status}</div>
        {children}
      </div>
    </div>
  );
}

function NumberField({
  label,
  value,
  step,
  onChange,
}: {
  label: string;
  value: number;
  step: number;
  onChange: (value: number) => void;
}) {
  return (
    <label className="block text-sm">
      <span className="mb-1 block text-gray-600">{label}</span>
      <input
        type="number"
        min={0}
        step={step}
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
        className="h-10 w-full rounded-md border border-gray-300 bg-white px-3 text-sm text-gray-900 outline-none focus:border-[#5BA8B9]"
      />
    </label>
  );
}
