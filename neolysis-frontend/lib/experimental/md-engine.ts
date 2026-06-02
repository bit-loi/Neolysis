export type MDEngineModule = {
  MDSimulator: new (...args: number[]) => ExperimentalMDSimulator;
};

export type AtomPosition = {
  id: number;
  label: string;
  x: number;
  y: number;
  z: number;
};

export type ExperimentalMDSimulator = {
  add_atom: (...args: unknown[]) => number | void;
  atom_count: () => number;
  current_step?: () => number;
  get_positions: () => unknown;
  reset?: () => void;
  run_steps?: (steps: number) => void;
  set_lennard_jones_params?: (epsilon: number, sigma: number) => void;
  set_timestep?: (dt: number) => void;
  step: (() => void) | number;
};

let wasmModule: MDEngineModule | null = null;

export async function getExperimentalMDEngine() {
  if (!wasmModule) {
    const importModule = new Function(
      'specifier',
      'return import(specifier)'
    ) as (specifier: string) => Promise<unknown>;

    wasmModule = (await importModule('neolysis-md-engine')) as MDEngineModule;
  }

  return wasmModule;
}

export function isMDEngineEnabled() {
  return process.env.NEXT_PUBLIC_ENABLE_MD_ENGINE === 'true';
}

export function normalizePositions(value: unknown): AtomPosition[] {
  if (Array.isArray(value)) {
    return value.filter(isAtomPosition);
  }

  if (value instanceof Float64Array || ArrayBuffer.isView(value)) {
    const flat = Array.from(value as unknown as ArrayLike<number>);
    const positions: AtomPosition[] = [];

    for (let i = 0; i < flat.length; i += 3) {
      positions.push({
        id: i / 3,
        label: `Atom ${i / 3}`,
        x: flat[i] ?? 0,
        y: flat[i + 1] ?? 0,
        z: flat[i + 2] ?? 0,
      });
    }

    return positions;
  }

  return [];
}

function isAtomPosition(value: unknown): value is AtomPosition {
  if (!value || typeof value !== 'object') {
    return false;
  }

  const maybe = value as Record<string, unknown>;

  return (
    typeof maybe.id === 'number' &&
    typeof maybe.label === 'string' &&
    typeof maybe.x === 'number' &&
    typeof maybe.y === 'number' &&
    typeof maybe.z === 'number'
  );
}
