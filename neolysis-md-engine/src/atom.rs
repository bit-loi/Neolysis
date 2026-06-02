use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct Atom {
    pub id: usize,
    pub label: String,
    pub mass: f64,
    pub position: [f64; 3],
    pub velocity: [f64; 3],
    pub force: [f64; 3],
}

impl Atom {
    pub fn new(id: usize, label: &str, mass: f64, position: [f64; 3], velocity: [f64; 3]) -> Self {
        Atom {
            id,
            label: label.to_string(),
            mass,
            position,
            velocity,
            force: [0.0, 0.0, 0.0],
        }
    }

    pub fn reset_forces(&mut self) {
        self.force = [0.0, 0.0, 0.0];
    }
}
