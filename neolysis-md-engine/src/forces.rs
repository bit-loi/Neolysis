use crate::atom::Atom;

pub enum ForceField {
    LennardJones { epsilon: f64, sigma: f64 },
}

impl ForceField {
    pub fn compute(&self, atoms: &mut [Atom]) {
        match self {
            ForceField::LennardJones { epsilon, sigma } => {
                lj_forces(atoms, *epsilon, *sigma);
            }
        }
    }
}

fn lj_forces(atoms: &mut [Atom], epsilon: f64, sigma: f64) {
    for atom in atoms.iter_mut() {
        atom.reset_forces();
    }

    let n = atoms.len();
    for i in 0..n {
        for j in (i + 1)..n {
            let dx = atoms[j].position[0] - atoms[i].position[0];
            let dy = atoms[j].position[1] - atoms[i].position[1];
            let dz = atoms[j].position[2] - atoms[i].position[2];
            let r2 = dx * dx + dy * dy + dz * dz;

            if r2 < 1e-10 {
                continue;
            }

            let s2 = sigma * sigma / r2;
            let s6 = s2 * s2 * s2;
            let s12 = s6 * s6;
            let force = 24.0 * epsilon * (2.0 * s12 - s6) / r2;

            let fx = force * dx;
            let fy = force * dy;
            let fz = force * dz;

            atoms[i].force[0] += fx;
            atoms[i].force[1] += fy;
            atoms[i].force[2] += fz;
            atoms[j].force[0] -= fx;
            atoms[j].force[1] -= fy;
            atoms[j].force[2] -= fz;
        }
    }
}
