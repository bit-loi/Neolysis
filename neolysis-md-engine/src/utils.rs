pub fn set_panic_hook() {
    // Better error messages di browser console waktu panic
    #[cfg(feature = "console_error_panic_hook")]
    console_error_panic_hook::set_once();
}

// Tambah utility lain di sini, misalnya:
pub fn distance(x1: f64, y1: f64, z1: f64, x2: f64, y2: f64, z2: f64) -> f64 {
    let dx = x2 - x1;
    let dy = y2 - y1;
    let dz = z2 - z1;
    (dx * dx + dy * dy + dz * dz).sqrt()
}
