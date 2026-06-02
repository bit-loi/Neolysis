use crate::atom::Atom;
use crate::forces::ForceField;
use crate::integrator::Integrator;
use serde::{Deserialize, Serialize};
use wasm_bindgen::prelude::*;

#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct AtomPosition {
    pub id: usize,
    pub label: String,
    pub x: f64,
    pub y: f64,
    pub z: f64,
}

#[wasm_bindgen]
pub struct MDSimulator {
    atoms: Vec<Atom>,
    timestep: f64,
    step_count: u32,
    force_field: ForceField,
    integrator: Integrator,
    temperature_proxy: Option<f64>,
}

impl Default for MDSimulator {
    fn default() -> Self {
        Self {
            atoms: Vec::new(),
            timestep: 0.001,
            step_count: 0,
            force_field: ForceField::LennardJones {
                epsilon: 1.0,
                sigma: 1.0,
            },
            integrator: Integrator::VelocityVerlet,
            temperature_proxy: None,
        }
    }
}

#[wasm_bindgen]
impl MDSimulator {
    #[wasm_bindgen(constructor)]
    pub fn new() -> Self {
        crate::utils::set_panic_hook();
        Self::default()
    }

    pub fn add_atom(
        &mut self,
        label: String,
        mass: f64,
        x: f64,
        y: f64,
        z: f64,
        vx: f64,
        vy: f64,
        vz: f64,
    ) -> usize {
        let id = self.atoms.len();
        self.atoms
            .push(Atom::new(id, &label, mass, [x, y, z], [vx, vy, vz]));
        id
    }

    pub fn step(&mut self) {
        self.force_field.compute(&mut self.atoms);
        self.integrator.integrate(&mut self.atoms, self.timestep);
        self.step_count += 1;
    }

    pub fn run_steps(&mut self, steps: u32) {
        for _ in 0..steps {
            self.step();
        }
    }

    pub fn get_positions(&self) -> JsValue {
        serde_wasm_bindgen::to_value(&self.position_snapshot()).unwrap_or(JsValue::NULL)
    }

    pub fn get_atoms_json(&self) -> JsValue {
        serde_wasm_bindgen::to_value(&self.atoms).unwrap_or(JsValue::NULL)
    }

    pub fn reset(&mut self) {
        self.atoms.clear();
        self.step_count = 0;
        self.temperature_proxy = None;
    }

    pub fn set_timestep(&mut self, dt: f64) {
        if dt.is_finite() && dt > 0.0 {
            self.timestep = dt;
        }
    }

    pub fn set_lennard_jones_params(&mut self, epsilon: f64, sigma: f64) {
        if epsilon.is_finite() && sigma.is_finite() && sigma > 0.0 {
            self.force_field = ForceField::LennardJones { epsilon, sigma };
        }
    }

    pub fn set_temperature_proxy(&mut self, value: f64) {
        if value.is_finite() && value >= 0.0 {
            self.temperature_proxy = Some(value);
        }
    }

    pub fn atom_count(&self) -> usize {
        self.atoms.len()
    }

    pub fn current_step(&self) -> u32 {
        self.step_count
    }
}

impl MDSimulator {
    pub fn position_snapshot(&self) -> Vec<AtomPosition> {
        self.atoms
            .iter()
            .map(|atom| AtomPosition {
                id: atom.id,
                label: atom.label.clone(),
                x: atom.position[0],
                y: atom.position[1],
                z: atom.position[2],
            })
            .collect()
    }
}

#[cfg(test)]
mod tests {
    use super::MDSimulator;

    #[test]
    fn simulator_initializes_empty() {
        let sim = MDSimulator::new();
        assert_eq!(sim.atom_count(), 0);
        assert_eq!(sim.current_step(), 0);
    }

    #[test]
    fn add_atom_increments_count() {
        let mut sim = MDSimulator::new();
        let id = sim.add_atom("O".to_string(), 16.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0);
        assert_eq!(id, 0);
        assert_eq!(sim.atom_count(), 1);
    }

    #[test]
    fn simulation_step_does_not_panic() {
        let mut sim = MDSimulator::new();
        sim.add_atom("A".to_string(), 1.0, -0.5, 0.0, 0.0, 0.0, 0.0, 0.0);
        sim.add_atom("B".to_string(), 1.0, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0);
        sim.step();
        assert_eq!(sim.current_step(), 1);
    }

    #[test]
    fn positions_snapshot_is_frontend_friendly() {
        let mut sim = MDSimulator::new();
        sim.add_atom("H".to_string(), 1.0, 0.9, 0.0, 0.0, 0.0, 0.0, 0.0);
        let positions = sim.position_snapshot();
        assert_eq!(positions.len(), 1);
        assert_eq!(positions[0].id, 0);
        assert_eq!(positions[0].label, "H");
        assert_eq!(positions[0].x, 0.9);
    }

    #[test]
    fn near_zero_distance_does_not_crash() {
        let mut sim = MDSimulator::new();
        sim.add_atom("A".to_string(), 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0);
        sim.add_atom("B".to_string(), 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0);
        sim.step();
        assert_eq!(sim.current_step(), 1);
    }

    #[test]
    fn reset_clears_state() {
        let mut sim = MDSimulator::new();
        sim.add_atom("O".to_string(), 16.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0);
        sim.run_steps(2);
        sim.reset();
        assert_eq!(sim.atom_count(), 0);
        assert_eq!(sim.current_step(), 0);
    }
}
