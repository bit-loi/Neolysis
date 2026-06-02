use crate::atom::Atom;

pub enum Integrator {
    VelocityVerlet,
    Euler, // less accurate, tapi buat debug cepet
}

impl Integrator {
    pub fn integrate(&self, atoms: &mut [Atom], dt: f64) {
        match self {
            Integrator::VelocityVerlet => velocity_verlet(atoms, dt),
            Integrator::Euler => euler(atoms, dt),
        }
    }
}

fn velocity_verlet(atoms: &mut [Atom], dt: f64) {
    for atom in atoms.iter_mut() {
        let ax = atom.force[0] / atom.mass;
        let ay = atom.force[1] / atom.mass;
        let az = atom.force[2] / atom.mass;

        atom.position[0] += atom.velocity[0] * dt + 0.5 * ax * dt * dt;
        atom.position[1] += atom.velocity[1] * dt + 0.5 * ay * dt * dt;
        atom.position[2] += atom.velocity[2] * dt + 0.5 * az * dt * dt;

        atom.velocity[0] += ax * dt;
        atom.velocity[1] += ay * dt;
        atom.velocity[2] += az * dt;
    }
}

fn euler(atoms: &mut [Atom], dt: f64) {
    for atom in atoms.iter_mut() {
        atom.velocity[0] += (atom.force[0] / atom.mass) * dt;
        atom.velocity[1] += (atom.force[1] / atom.mass) * dt;
        atom.velocity[2] += (atom.force[2] / atom.mass) * dt;
        atom.position[0] += atom.velocity[0] * dt;
        atom.position[1] += atom.velocity[1] * dt;
        atom.position[2] += atom.velocity[2] * dt;
    }
}
