# Neolysis MD Engine - Experimental Rust/WASM Molecular Dynamics Sandbox

This module provides a lightweight Rust/WebAssembly molecular dynamics sandbox used by Neolysis for experimental browser-based numerical simulation. It is intended as a future foundation for structure-aware enzyme engineering features.

The module is optional. The core Neolysis product remains focused on enzyme sequence intelligence, industrial property scoring, variant prioritization, and wet-lab validation planning.

## Scientific Limitations

This experimental WASM simulation module demonstrates simplified browser-based molecular dynamics. It is not a validated protein dynamics engine and should not be used as experimental proof of enzyme activity, stability, or industrial performance.

Current limitations:

- simplified particle simulation
- currently uses Lennard-Jones style interactions
- not validated for protein dynamics
- not a replacement for GROMACS, AMBER, NAMD, or OpenMM
- not experimental proof of enzyme stability or activity
- not part of the production enzyme property scoring pipeline

## Current Role

The engine is an experimental browser-based simulation sandbox. It can demonstrate basic particle movement, simple force calculation, numerical integration, and Rust/WASM integration in the Neolysis frontend.

## Future Direction

The engine may become a foundation for future structure-aware enzyme engineering exploration, such as:

- structure visualization
- local flexibility exploration
- active-site movement visualization
- mutation effect visualization
- educational simulation
- integration with real structure data

These are roadmap directions, not currently validated capabilities.

## Structure

```text
neolysis-md-engine/
  Cargo.toml
  README.md
  src/
    lib.rs
    atom.rs
    forces.rs
    integrator.rs
    simulator.rs
    utils.rs
  pkg/
    generated wasm package
```

## WASM API

The public WebAssembly API exposes `MDSimulator`.

Primary methods:

- `new()`
- `add_atom(label, mass, x, y, z, vx, vy, vz)`
- `step()`
- `run_steps(steps)`
- `get_positions()`
- `get_atoms_json()`
- `reset()`
- `set_timestep(dt)`
- `set_lennard_jones_params(epsilon, sigma)`
- `set_temperature_proxy(value)`
- `atom_count()`
- `current_step()`

`get_positions()` returns frontend-friendly data:

```json
[
  {
    "id": 0,
    "label": "O",
    "x": 0.0,
    "y": 0.0,
    "z": 0.0
  }
]
```

## Build And Test

From this directory:

```bash
cargo check
cargo test
wasm-pack build --target web
```

The generated package is consumed by the frontend through:

```json
"neolysis-md-engine": "file:../neolysis-md-engine/pkg"
```

After rebuilding the WASM package, reinstall or refresh frontend dependencies if needed.

## Frontend Integration

The Next.js frontend imports this module through an experimental-only path:

```text
neolysis-frontend/lib/experimental/md-engine.ts
neolysis-frontend/components/experimental/MolecularDynamicsSandbox.tsx
neolysis-frontend/app/experimental/md-sandbox/page.tsx
```

Enable the page with:

```bash
NEXT_PUBLIC_ENABLE_MD_ENGINE=true
```

When the flag is disabled, the frontend shows:

```text
Experimental molecular dynamics sandbox is disabled. Core enzyme sequence analysis remains available.
```

If WASM loading fails, the frontend falls back without crashing the core app.
