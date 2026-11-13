// Biblioteca de equipos del gimnasio (modelos paramétricos, estilizados) para three.js.
// Convención local: x = ancho visto de frente, z = fondo (+z = lado de uso / frente), y = altura.
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';

// ------------------------------------------------------------------ materiales compartidos
const std = (color, rough, metal, extra = {}) => new THREE.MeshStandardMaterial({ color, roughness: rough, metalness: metal, ...extra });
export const MAT = {
  marco: std(0x17181b, 0.42, 0.55),
  marco2: std(0x2a2c31, 0.5, 0.5),
  gris: std(0xc3c7cc, 0.38, 0.55),
  cromo: std(0xe3e6ea, 0.16, 1.0),
  tapiz: std(0x0e0e10, 0.55, 0.05),
  tapizRojo: std(0xb3161b, 0.5, 0.05),
  caucho: std(0x0b0b0c, 0.9, 0.0),
  pesa: std(0x25272b, 0.55, 0.6),
  rojo: std(0xd81f26, 0.45, 0.2),
  blanco: std(0xf2f2ef, 0.6, 0.0),
  d25: std(0xc9151e, 0.6, 0.05), d20: std(0x1e4fa3, 0.6, 0.05), d15: std(0xe2b007, 0.6, 0.05),
  d10: std(0x2a9a4b, 0.6, 0.05), d5: std(0x1c1c1e, 0.6, 0.05),
  madera: std(0xa8763e, 0.6, 0.0),
  piel: std(0xc79a78, 0.75, 0.0),
};
const V = (a) => new THREE.Vector3(a[0], a[1], a[2]);
const EJE_Z = new THREE.Vector3(0, 0, 1), EJE_Y = new THREE.Vector3(0, 1, 0);

export function G() { return new THREE.Group(); }
function M(geo, mat) { const m = new THREE.Mesh(geo, mat); m.castShadow = true; m.receiveShadow = true; return m; }
export function caja(w, h, d, mat, x = 0, y = 0, z = 0) { const m = M(new THREE.BoxGeometry(w, h, d), mat); m.position.set(x, y, z); return m; }
export function viga(a, b, sx, sy, mat) {
  const A = V(a), B = V(b), L = A.distanceTo(B);
  const m = M(new THREE.BoxGeometry(sx, sy, L), mat);
  m.position.copy(A).add(B).multiplyScalar(0.5);
  m.quaternion.setFromUnitVectors(EJE_Z, B.clone().sub(A).normalize());
  return m;
}
export function tubo(a, b, r, mat, seg = 14) {
  const A = V(a), B = V(b), L = A.distanceTo(B);
  const m = M(new THREE.CylinderGeometry(r, r, L, seg), mat);
  m.position.copy(A).add(B).multiplyScalar(0.5);
  m.quaternion.setFromUnitVectors(EJE_Y, B.clone().sub(A).normalize());
  return m;
}
export function capsula(a, b, r, mat) {
  const A = V(a), B = V(b), L = Math.max(0.001, A.distanceTo(B));
  const m = M(new THREE.CapsuleGeometry(r, L, 4, 10), mat);
  m.position.copy(A).add(B).multiplyScalar(0.5);
  m.quaternion.setFromUnitVectors(EJE_Y, B.clone().sub(A).normalize());
  return m;
}
export function cojin(w, h, d, mat, x = 0, y = 0, z = 0, r = 0.028) {
  const m = M(new RoundedBoxGeometry(w, h, d, 3, Math.min(r, h / 2 - 0.002, w / 2 - 0.002, d / 2 - 0.002)), mat);
  m.position.set(x, y, z); return m;
}
// Disco olímpico con eje a lo largo de x
const DISCOS = { 25: [0.225, 0.06, 'd25'], 20: [0.225, 0.05, 'd20'], 15: [0.20, 0.042, 'd15'], 10: [0.175, 0.035, 'd10'], 5: [0.115, 0.026, 'd5'] };
export function disco(kg, x, y, z, eje = 'x') {
  const [r, t, mat] = DISCOS[kg];
  const g = G();
  const c = M(new THREE.CylinderGeometry(r, r, t, 36), MAT[mat]);
  const hub = M(new THREE.CylinderGeometry(r * 0.3, r * 0.3, t + 0.006, 20), MAT.cromo);
  const aro = M(new THREE.CylinderGeometry(r * 0.72, r * 0.72, t + 0.003, 30), MAT.d5);
  g.add(c, aro, hub);
  if (eje === 'x') g.rotation.z = Math.PI / 2; else if (eje === 'z') g.rotation.x = Math.PI / 2;
  g.position.set(x, y, z); g.userData.t = t;
  return g;
}
// Serie de discos sobre un eje (x o z) a partir de la coordenada inicial, avanzando en "sentido"
function discos(g, lista, x, y, z, sentido = 1, eje = 'x') {
  let p = eje === 'x' ? x : z;
  for (const kg of lista) {
    const t = DISCOS[kg][1];
    const pos = p + sentido * t / 2;
    g.add(eje === 'x' ? disco(kg, pos, y, z, 'x') : disco(kg, x, y, pos, 'z'));
    p += sentido * (t + 0.004);
  }
  return p;
}
// Barra olímpica a lo largo de x con discos
export function barra(lista = [20, 10], largo = 2.2) {
  const g = G();
  g.add(tubo([-largo / 2 + 0.41, 0, 0], [largo / 2 - 0.41, 0, 0], 0.014, MAT.cromo));
  for (const s of [-1, 1]) {
    g.add(tubo([s * (largo / 2 - 0.41), 0, 0], [s * largo / 2, 0, 0], 0.025, MAT.cromo, 16));
    g.add(tubo([s * (largo / 2 - 0.43), 0, 0], [s * (largo / 2 - 0.41), 0, 0], 0.04, MAT.cromo, 16));
    discos(g, lista, s * (largo / 2 - 0.405), 0, 0, s);
  }
  return g;
}
// Torre de placas selectorizada (pila + guías + carcasa), base en y = 0, centrada en x, z
export function torre(h = 1.6, w = 0.36, d = 0.2, n = 14) {
  const g = G();
  g.add(caja(w + 0.06, 0.05, d + 0.06, MAT.marco, 0, 0.025, 0));
  for (const s of [-1, 1]) {
    g.add(caja(0.035, h - 0.05, d, MAT.gris, s * (w / 2 + 0.012), h / 2 + 0.025, 0));
    g.add(tubo([s * 0.085, 0.05, 0], [s * 0.085, h - 0.06, 0], 0.011, MAT.cromo, 10));
  }
  g.add(caja(w + 0.06, 0.16, d + 0.02, MAT.gris, 0, h - 0.08, 0));
  g.add(caja(w * 0.62, 0.05, 0.006, MAT.rojo, 0, h - 0.08, d / 2 + 0.012));
  const e = 0.027;
  for (let i = 0; i < n; i++) {
    g.add(caja(w - 0.05, e - 0.004, d - 0.07, MAT.pesa, 0, 0.07 + i * e, 0));
    if (i % 2 === 0) g.add(caja(0.05, 0.012, 0.004, MAT.blanco, 0, 0.07 + i * e, (d - 0.07) / 2 + 0.002));
  }
  g.add(tubo([0, 0.07 + n * e, 0], [0, h - 0.16, 0], 0.004, MAT.marco, 6));
  return g;
}
function mancuerna(kg) {
  const g = G();
  const r = 0.042 + 0.0034 * kg, lc = 0.045 + 0.0042 * kg;
  g.add(tubo([0, 0, -0.065], [0, 0, 0.065], 0.015, MAT.cromo, 10));
  for (const s of [-1, 1]) {
    const c = M(new THREE.CylinderGeometry(r, r, lc, 6), MAT.caucho);
    c.rotation.x = Math.PI / 2; c.position.z = s * (0.065 + lc / 2); g.add(c);
  }
  g.userData.r = r;
  return g;
}

// ------------------------------------------------------------------ equipos
function mancuernero(w, d) {
  const g = G(), h = 0.86;
  for (const s of [-1, 1]) {
    const x = s * (w / 2 - 0.05);
    g.add(viga([x, 0.03, -d / 2 + 0.03], [x, 0.03, d / 2 - 0.03], 0.07, 0.06, MAT.marco));
    g.add(viga([x, 0.03, -d / 2 + 0.1], [x, h, -d / 2 + 0.22], 0.07, 0.07, MAT.marco));
    g.add(viga([x, 0.03, d / 2 - 0.08], [x, 0.46, 0.08], 0.07, 0.07, MAT.marco));
    g.add(viga([x, 0.46, 0.08], [x, h, -d / 2 + 0.22], 0.07, 0.07, MAT.marco));
  }
  const niveles = [{ y: 0.3, z: 0.08, pesos: [20, 20, 17.5, 17.5, 15, 15, 12.5, 12.5] }, { y: 0.7, z: -0.1, pesos: [10, 10, 7.5, 7.5, 5, 5, 2.5, 2.5] }];
  for (const n of niveles) {
    for (const dz of [-0.11, 0.11]) g.add(viga([-w / 2 + 0.05, n.y - dz * 0.35, n.z + dz], [w / 2 - 0.05, n.y - dz * 0.35, n.z + dz], 0.05, 0.035, MAT.marco2));
    const paso = (w - 0.5) / (n.pesos.length - 1);
    n.pesos.forEach((kg, i) => {
      const m = mancuerna(kg);
      m.position.set(-w / 2 + 0.25 + i * paso, n.y + m.userData.r * 0.82 + 0.01, n.z);
      m.rotation.x = 0.33; g.add(m);
    });
  }
  return g;
}
function portaBarras(w, d) {
  const g = G(), h = 1.45;
  for (const s of [-1, 1]) {
    const x = s * (w / 2 - 0.12);
    g.add(viga([x, 0.03, -d / 2 + 0.03], [x, 0.03, d / 2 - 0.03], 0.06, 0.06, MAT.marco));
    g.add(viga([x, 0.03, d / 2 - 0.12], [x, h, -d / 2 + 0.12], 0.06, 0.06, MAT.marco));
    g.add(viga([x, 0.03, -d / 2 + 0.06], [x, h * 0.55, -d / 2 + 0.3], 0.05, 0.05, MAT.marco));
  }
  g.add(viga([-w / 2 + 0.12, 0.03, -d / 2 + 0.05], [w / 2 - 0.12, 0.03, -d / 2 + 0.05], 0.06, 0.06, MAT.marco));
  const pesos = [30, 25, 20, 15, 10];
  pesos.forEach((kg, i) => {
    const t = (i + 0.6) / (pesos.length + 0.4);
    const y = 0.12 + t * (h - 0.2), z = (d / 2 - 0.12) + t * (-d + 0.24) + 0.07;
    for (const s of [-1, 1]) g.add(caja(0.04, 0.03, 0.1, MAT.marco2, s * (w / 2 - 0.12), y - 0.03, z));
    g.add(tubo([-0.56, y, z], [0.56, y, z], 0.014, MAT.cromo, 10));
    const r = 0.06 + kg * 0.0016;
    for (const s of [-1, 1]) { const c = M(new THREE.CylinderGeometry(r, r, 0.05 + kg * 0.0016, 20), MAT.caucho); c.rotation.z = Math.PI / 2; c.position.set(s * 0.5, y, z); g.add(c); }
  });
  return g;
}
function baseMarco(g, w, d, xs = [-0.3, 0.3], frente = true) {
  for (const x of xs) g.add(viga([x, 0.035, -d / 2 + 0.02], [x, 0.035, d / 2 - 0.02], 0.08, 0.07, MAT.marco));
  g.add(viga([-w / 2 + 0.03, 0.035, -d / 2 + 0.06], [w / 2 - 0.03, 0.035, -d / 2 + 0.06], 0.08, 0.07, MAT.marco));
  if (frente) g.add(viga([-w / 2 + 0.1, 0.035, d / 2 - 0.06], [w / 2 - 0.1, 0.035, d / 2 - 0.06], 0.08, 0.07, MAT.marco));
}
function asiento(g, y, z, respaldo = 12, ancho = 0.42, largoResp = 0.62) {
  g.add(cojin(ancho, 0.07, 0.4, MAT.tapiz, 0, y, z));
  g.add(viga([0, 0.07, z], [0, y - 0.03, z], 0.07, 0.07, MAT.marco));
  const a = THREE.MathUtils.degToRad(respaldo);
  const r = cojin(ancho - 0.06, largoResp, 0.07, MAT.tapiz, 0, y + 0.05 + (largoResp / 2) * Math.cos(a), z - 0.22 - (largoResp / 2) * Math.sin(a));
  r.rotation.x = -a; g.add(r);
  g.add(viga([0, 0.07, z - 0.3], [0, y + largoResp * 0.75, z - 0.27 - largoResp * 0.75 * Math.sin(a)], 0.06, 0.06, MAT.marco));
}
function triceps(w, d) {
  const g = G();
  baseMarco(g, w, d, [-0.34, 0.34]);
  const t = torre(1.5, 0.36, 0.2); t.position.set(0, 0, -d / 2 + 0.17); g.add(t);
  asiento(g, 0.46, 0.2, 8, 0.4, 0.55);
  for (const s of [-1, 1]) {
    const x = s * 0.4;
    g.add(viga([x * 0.55, 0.07, -0.32], [x * 0.55, 1.02, -0.32], 0.07, 0.07, MAT.marco));
    g.add(viga([x * 0.55, 1.02, -0.32], [x, 1.02, -0.3], 0.06, 0.06, MAT.marco));
    g.add(viga([x, 1.02, -0.3], [x, 0.74, 0.4], 0.055, 0.055, MAT.gris));
    g.add(tubo([x, 0.74, 0.4], [x, 0.74, 0.58], 0.019, MAT.caucho));
    g.add(tubo([x, 0.3, 0.52], [x, 0.3, 0.66], 0.02, MAT.cromo));
  }
  g.add(viga([-0.4, 0.3, 0.6], [0.4, 0.3, 0.6], 0.045, 0.045, MAT.marco));
  g.add(viga([0, 0.07, 0.6], [0, 0.3, 0.6], 0.06, 0.06, MAT.marco));
  return g;
}
function biceps(w, d) {
  const g = G();
  baseMarco(g, w, d, [-0.36, 0.3]);
  const t = torre(1.73, 0.36, 0.2); t.position.set(-w / 2 + 0.28, 0, -d / 2 + 0.2); g.add(t);
  // asiento y apoyabrazos inclinado
  g.add(cojin(0.38, 0.07, 0.34, MAT.tapiz, 0.15, 0.48, 0.34));
  g.add(viga([0.15, 0.07, 0.34], [0.15, 0.45, 0.34], 0.07, 0.07, MAT.marco));
  const ap = cojin(0.62, 0.08, 0.46, MAT.tapiz, 0.15, 0.9, -0.06); ap.rotation.x = -0.75; g.add(ap);
  g.add(viga([0.15, 0.07, -0.1], [0.15, 0.82, -0.1], 0.08, 0.08, MAT.marco));
  // brazo de palanca con agarres
  for (const s of [-1, 1]) g.add(viga([0.15 + s * 0.36, 0.72, 0.05], [0.15 + s * 0.36, 0.84, -0.4], 0.05, 0.05, MAT.gris));
  g.add(tubo([0.15 - 0.36, 0.84, -0.4], [0.15 + 0.36, 0.84, -0.4], 0.018, MAT.cromo));
  for (const s of [-1, 1]) g.add(tubo([0.15 + s * 0.2, 0.84, -0.4], [0.15 + s * 0.32, 0.84, -0.4], 0.024, MAT.caucho));
  g.add(viga([-w / 2 + 0.28, 0.5, -d / 2 + 0.3], [0.15 - 0.36, 0.72, 0.05], 0.05, 0.05, MAT.marco));
  return g;
}
function extension(w, d) {
  const g = G();
  baseMarco(g, w, d, [-0.36, 0.3]);
  const t = torre(1.8, 0.36, 0.2); t.position.set(-w / 2 + 0.28, 0, -d / 2 + 0.22); g.add(t);
  const x = 0.14;
  g.add(cojin(0.46, 0.08, 0.5, MAT.tapiz, x, 0.58, 0.05));
  const r = cojin(0.42, 0.66, 0.08, MAT.tapiz, x, 0.98, -0.34); r.rotation.x = -0.28; g.add(r);
  g.add(viga([x, 0.07, 0.05], [x, 0.54, 0.05], 0.09, 0.09, MAT.marco));
  g.add(viga([x, 0.07, -0.42], [x, 1.2, -0.52], 0.07, 0.07, MAT.marco));
  for (const s of [-1, 1]) {
    g.add(viga([x + s * 0.3, 0.52, 0.32], [x + s * 0.3, 0.2, 0.5], 0.05, 0.05, MAT.gris));
    g.add(tubo([x + s * 0.3, 0.62, -0.02], [x + s * 0.3, 0.72, 0.2], 0.017, MAT.caucho));
    g.add(viga([x + s * 0.3, 0.3, -0.02], [x + s * 0.3, 0.62, -0.02], 0.04, 0.04, MAT.marco));
  }
  for (const [y, z] of [[0.2, 0.5], [0.66, 0.66]]) {
    const c = M(new THREE.CylinderGeometry(0.075, 0.075, 0.46, 20), MAT.tapiz); c.rotation.z = Math.PI / 2; c.position.set(x, y, z); g.add(c);
    g.add(tubo([x - 0.3, y, z], [x + 0.3, y, z], 0.018, MAT.cromo, 10));
  }
  g.add(viga([x - 0.3, 0.52, 0.32], [x - 0.3, 0.66, 0.66], 0.045, 0.045, MAT.gris));
  g.add(viga([-w / 2 + 0.28, 0.4, -d / 2 + 0.32], [x - 0.3, 0.52, 0.32], 0.05, 0.05, MAT.marco));
  return g;
}
function aductor(w, d) {
  const g = G();
  baseMarco(g, w, d, [-0.34, 0.34]);
  const t = torre(1.8, 0.36, 0.2); t.position.set(0, 0, -d / 2 + 0.2); g.add(t);
  g.add(cojin(0.44, 0.08, 0.46, MAT.tapiz, 0, 0.52, 0.1));
  const r = cojin(0.4, 0.7, 0.08, MAT.tapiz, 0, 0.93, -0.28); r.rotation.x = -0.32; g.add(r);
  g.add(viga([0, 0.07, 0.1], [0, 0.48, 0.1], 0.09, 0.09, MAT.marco));
  g.add(viga([0, 0.07, -0.36], [0, 1.2, -0.5], 0.07, 0.07, MAT.marco));
  for (const s of [-1, 1]) {
    g.add(viga([s * 0.08, 0.42, 0.28], [s * 0.46, 0.42, 0.56], 0.05, 0.05, MAT.gris));
    g.add(viga([s * 0.46, 0.42, 0.56], [s * 0.46, 0.7, 0.56], 0.05, 0.05, MAT.gris));
    const p = cojin(0.09, 0.26, 0.3, MAT.tapiz, s * 0.4, 0.68, 0.5); p.rotation.y = s * 0.5; g.add(p);
    g.add(caja(0.12, 0.02, 0.26, MAT.marco2, s * 0.5, 0.2, 0.62));
    g.add(viga([s * 0.46, 0.2, 0.56], [s * 0.46, 0.42, 0.56], 0.04, 0.04, MAT.gris));
    g.add(tubo([s * 0.27, 0.56, -0.06], [s * 0.27, 0.66, 0.12], 0.017, MAT.caucho));
    g.add(viga([s * 0.27, 0.3, -0.06], [s * 0.27, 0.56, -0.06], 0.04, 0.04, MAT.marco));
  }
  return g;
}
function crossover(w, d) {
  const g = G(), h = 2.3, xT = w / 2 - 0.22;
  for (const s of [-1, 1]) {
    const x = s * xT;
    g.add(viga([x, 0.04, -d / 2 + 0.02], [x, 0.04, d / 2 - 0.02], 0.1, 0.08, MAT.marco));
    g.add(viga([x - 0.2, 0.04, -d / 2 + 0.1], [x + 0.2, 0.04, -d / 2 + 0.1], 0.08, 0.08, MAT.marco));
    for (const z of [-0.26, 0.26]) g.add(viga([x, 0.08, z], [x, h - 0.12, z], 0.075, 0.075, MAT.marco));
    const t = torre(1.95, 0.3, 0.2, 18); t.position.set(x, 0.06, 0); t.rotation.y = Math.PI / 2; g.add(t);
    // columna de regulación con polea deslizante
    const xi = x - s * 0.17;
    g.add(viga([xi, 0.08, 0.3], [xi, h - 0.2, 0.3], 0.05, 0.05, MAT.gris));
    for (let i = 0; i < 12; i++) g.add(caja(0.052, 0.012, 0.012, MAT.marco, xi, 0.4 + i * 0.13, 0.33));
    const yp = s < 0 ? 1.72 : 0.62;
    g.add(caja(0.09, 0.14, 0.1, MAT.marco2, xi, yp, 0.34));
    const pol = M(new THREE.CylinderGeometry(0.055, 0.055, 0.025, 20), MAT.marco); pol.rotation.z = Math.PI / 2; pol.position.set(xi - s * 0.05, yp, 0.4); g.add(pol);
    g.add(tubo([xi - s * 0.05, yp - 0.04, 0.42], [xi - s * 0.2, yp - 0.34, 0.48], 0.004, MAT.marco, 6));
    g.add(tubo([xi - s * 0.2 - 0.06, yp - 0.36, 0.48], [xi - s * 0.2 + 0.06, yp - 0.36, 0.48], 0.014, MAT.caucho, 8));
    g.add(caja(0.26, 0.2, 0.012, MAT.gris, x, h - 0.32, 0.268));
    g.add(caja(0.16, 0.04, 0.006, MAT.rojo, x, h - 0.3, 0.278));
  }
  // pasamanos en arco entre torres
  const n = 14, arco = (k) => h - 0.12 + 0.16 * Math.sin(Math.PI * k);
  for (const z of [-0.26, 0.26]) for (let i = 0; i < n; i++) {
    const k0 = i / n, k1 = (i + 1) / n;
    g.add(viga([-xT + 2 * xT * k0, arco(k0), z], [-xT + 2 * xT * k1, arco(k1), z], 0.07, 0.07, MAT.marco));
  }
  for (let i = 1; i < n; i++) { const k = i / n; g.add(tubo([-xT + 2 * xT * k, arco(k), -0.26], [-xT + 2 * xT * k, arco(k), 0.26], 0.016, MAT.cromo, 10)); }
  for (const s of [-1, 1]) { g.add(tubo([s * 0.38, arco(0.4) - 0.02, 0.26], [s * 0.38, arco(0.4) - 0.02, 0.5], 0.016, MAT.caucho, 10)); }
  return g;
}
function prensa(w, d) {
  const g = G();
  const zR = -d / 2 + 0.12, zF = d / 2 - 0.05;
  for (const s of [-1, 1]) {
    g.add(viga([s * 0.42, 0.04, zR], [s * 0.42, 0.04, zF], 0.09, 0.08, MAT.marco));
    g.add(viga([s * 0.42, 0.04, zR + 0.02], [s * 0.42, 1.42, zR + 0.02], 0.09, 0.09, MAT.marco));
    g.add(viga([s * 0.3, 0.22, 0.32], [s * 0.3, 1.36, zR + 0.1], 0.07, 0.09, MAT.gris));        // rieles a 45°
    g.add(viga([s * 0.42, 0.08, 0.34], [s * 0.3, 0.22, 0.32], 0.07, 0.07, MAT.marco));
    g.add(viga([s * 0.42, 1.38, zR + 0.04], [s * 0.3, 1.36, zR + 0.1], 0.07, 0.07, MAT.marco));
    // discos de reserva en la columna trasera
    g.add(tubo([s * 0.47, 0.5, zR + 0.02], [s * 0.72, 0.5, zR + 0.02], 0.024, MAT.cromo));
    discos(g, s < 0 ? [20, 10] : [25], s * 0.49, 0.5, zR + 0.02, s);
  }
  for (const y of [0.04, 1.4]) g.add(viga([-0.42, y, zR + 0.02], [0.42, y, zR + 0.02], 0.08, 0.08, MAT.marco));
  g.add(viga([-0.6, 0.04, zF - 0.05], [0.6, 0.04, zF - 0.05], 0.09, 0.08, MAT.marco));
  // carro con plataforma de pies (a mitad de recorrido)
  const k = 0.42, py = 0.22 + (1.36 - 0.22) * k, pz = 0.32 + (zR + 0.1 - 0.32) * k;
  const carro = G(); carro.position.set(0, py, pz); carro.rotation.x = -Math.atan2(1.36 - 0.22, 0.32 - (zR + 0.1));
  carro.add(caja(0.78, 0.07, 0.3, MAT.marco2, 0, 0.06, 0));
  const plat = caja(0.72, 0.56, 0.035, MAT.marco2, 0, 0.36, 0.14); carro.add(plat);
  carro.add(caja(0.66, 0.5, 0.01, MAT.pesa, 0, 0.36, 0.162));
  for (const s of [-1, 1]) { carro.add(tubo([s * 0.4, 0.12, 0], [s * 0.76, 0.12, 0], 0.025, MAT.cromo)); discos(carro, [25, 20, 10], s * 0.43, 0.12, 0, s); }
  g.add(carro);
  // asiento bajo y respaldo reclinado
  g.add(cojin(0.46, 0.08, 0.36, MAT.tapiz, 0, 0.3, 0.66));
  const r = cojin(0.46, 0.78, 0.09, MAT.tapiz, 0, 0.62, 1.0); r.rotation.x = 0.82; g.add(r);
  const cab = cojin(0.3, 0.2, 0.09, MAT.tapiz, 0, 0.93, 1.27); cab.rotation.x = 0.82; g.add(cab);
  g.add(viga([0, 0.08, 0.7], [0, 0.26, 0.7], 0.08, 0.08, MAT.marco));
  g.add(viga([0, 0.08, 1.05], [0, 0.55, 1.05], 0.08, 0.08, MAT.marco));
  g.add(viga([0, 0.04, 0.3], [0, 0.04, zF], 0.09, 0.08, MAT.marco));
  for (const s of [-1, 1]) { g.add(viga([s * 0.33, 0.08, 0.72], [s * 0.33, 0.48, 0.72], 0.04, 0.04, MAT.marco)); g.add(tubo([s * 0.33, 0.48, 0.64], [s * 0.33, 0.48, 0.82], 0.018, MAT.caucho)); }
  return g;
}
function hipThrust(w, d) {
  const g = G();
  // plataforma antideslizante y bastidor bajo
  g.add(caja(1.06, 0.035, 1.25, MAT.marco2, 0, 0.05, 0.22));
  g.add(caja(1.0, 0.006, 1.19, MAT.pesa, 0, 0.071, 0.22));
  for (const s of [-1, 1]) {
    g.add(viga([s * 0.6, 0.04, -d / 2 + 0.05], [s * 0.6, 0.04, d / 2 - 0.05], 0.08, 0.07, MAT.marco));
    g.add(viga([s * 0.6, 0.07, 0.12], [s * 0.6, 0.3, 0.12], 0.07, 0.07, MAT.marco));
    g.add(caja(0.09, 0.03, 0.2, MAT.gris, s * 0.6, 0.31, 0.12));
    g.add(tubo([s * 0.66, 0.2, -d / 2 + 0.16], [s * 0.86, 0.2, -d / 2 + 0.16], 0.024, MAT.cromo));
    discos(g, [10, 10], s * 0.68, 0.2, -d / 2 + 0.16, s);
    for (let i = 0; i < 4; i++) g.add(tubo([s * 0.6, 0.09, 0.4 + i * 0.13], [s * 0.74, 0.09, 0.4 + i * 0.13], 0.012, MAT.cromo, 8));
  }
  g.add(viga([-0.64, 0.04, -d / 2 + 0.08], [0.64, 0.04, -d / 2 + 0.08], 0.08, 0.07, MAT.marco));
  g.add(viga([-0.64, 0.04, d / 2 - 0.08], [0.64, 0.04, d / 2 - 0.08], 0.08, 0.07, MAT.marco));
  // apoyo de espalda
  g.add(cojin(0.95, 0.2, 0.3, MAT.tapiz, 0, 0.4, -0.52, 0.06));
  for (const s of [-1, 1]) g.add(viga([s * 0.36, 0.07, -0.58], [s * 0.36, 0.3, -0.54], 0.07, 0.07, MAT.marco));
  // barra cargada
  const b = barra([20, 10], 2.2); b.position.set(0, 0.37, 0.12); g.add(b);
  const al = M(new THREE.CylinderGeometry(0.05, 0.05, 0.42, 16), MAT.tapiz); al.rotation.z = Math.PI / 2; al.position.set(0, 0.37, 0.12); g.add(al);
  return g;
}
function pressPlano(w, d) {
  const g = G(), zP = -d / 2 + 0.3;
  for (const s of [-1, 1]) {
    const x = s * 0.56;
    g.add(viga([x, 0.04, -d / 2 + 0.04], [x, 0.04, 0.25], 0.08, 0.07, MAT.marco));
    g.add(viga([x, 0.07, zP], [x, 1.22, zP], 0.075, 0.075, MAT.marco));
    g.add(viga([x, 0.07, -d / 2 + 0.08], [x, 0.62, zP], 0.06, 0.06, MAT.marco));
    g.add(caja(0.09, 0.05, 0.14, MAT.gris, x, 1.0, zP + 0.09));
    g.add(caja(0.09, 0.09, 0.03, MAT.gris, x, 1.04, zP + 0.16));
    g.add(caja(0.09, 0.05, 0.12, MAT.gris, x, 0.74, zP + 0.08));
    g.add(tubo([x, 0.42, zP - 0.04], [x, 0.42, zP - 0.26], 0.024, MAT.cromo));
    discos(g, s < 0 ? [20, 15] : [10, 5], x, 0.42, zP - 0.06, -1, 'z');
  }
  g.add(viga([-0.56, 0.04, -d / 2 + 0.06], [0.56, 0.04, -d / 2 + 0.06], 0.08, 0.07, MAT.marco));
  g.add(caja(0.5, 0.02, 0.3, MAT.marco2, 0, 0.16, -d / 2 + 0.16));           // peldaño del ayudante
  // banco
  g.add(cojin(0.3, 0.075, 1.24, MAT.tapiz, 0, 0.44, 0.2));
  g.add(viga([0, 0.36, -0.36], [0, 0.36, 0.76], 0.07, 0.06, MAT.marco));
  g.add(viga([0, 0.04, 0.7], [0, 0.36, 0.7], 0.07, 0.07, MAT.marco));
  g.add(viga([-0.26, 0.04, 0.7], [0.26, 0.04, 0.7], 0.07, 0.06, MAT.marco));
  g.add(viga([0, 0.04, zP], [0, 0.36, -0.3], 0.07, 0.07, MAT.marco));
  g.add(viga([-0.56, 0.04, zP], [0.56, 0.04, zP], 0.07, 0.06, MAT.marco));
  const b = barra([20, 10], 2.2); b.position.set(0, 1.065, zP + 0.1); g.add(b);
  return g;
}
function dominadas(w, d) {
  const g = G(), h = 2.23;
  baseMarco(g, w, d, [-0.42, 0.42]);
  const t = torre(1.9, 0.36, 0.2, 16); t.position.set(0, 0, -d / 2 + 0.2); g.add(t);
  for (const s of [-1, 1]) {
    const x = s * 0.42;
    g.add(viga([x, 0.07, -0.3], [x, h - 0.1, -0.3], 0.075, 0.075, MAT.marco));
    g.add(viga([x, h - 0.1, -0.3], [x, h, 0.1], 0.07, 0.07, MAT.marco));
    g.add(tubo([x, h, 0.1], [x + s * 0.2, h - 0.08, 0.1], 0.018, MAT.caucho));        // agarre ancho
    g.add(tubo([x - s * 0.22, h, 0.1], [x - s * 0.22, h, 0.3], 0.018, MAT.caucho));   // agarre neutro
    g.add(viga([x, 1.28, -0.3], [x - s * 0.12, 1.28, 0.36], 0.05, 0.05, MAT.gris));   // fondos
    g.add(tubo([x - s * 0.12, 1.28, 0.2], [x - s * 0.12, 1.28, 0.4], 0.02, MAT.caucho));
    g.add(caja(0.2, 0.025, 0.24, MAT.marco2, s * 0.36, 0.34, 0.36));                 // peldaños
    g.add(viga([s * 0.42, 0.07, 0.3], [s * 0.42, 0.33, 0.3], 0.05, 0.05, MAT.marco));
  }
  g.add(viga([-0.42, h, 0.1], [0.42, h, 0.1], 0.06, 0.06, MAT.marco));
  g.add(cojin(0.5, 0.09, 0.3, MAT.tapiz, 0, 0.82, 0.24));                            // apoyo de rodillas
  g.add(viga([0, 0.76, 0.2], [0, 0.6, -0.3], 0.06, 0.06, MAT.gris));
  g.add(viga([-0.42, 0.6, -0.3], [0.42, 0.6, -0.3], 0.05, 0.05, MAT.marco));
  return g;
}
function banco(w, d, incl = 40) {
  const g = G();
  g.add(viga([0, 0.2, -d / 2 + 0.12], [0, 0.2, d / 2 - 0.12], 0.07, 0.07, MAT.marco));
  for (const z of [-d / 2 + 0.12, d / 2 - 0.12]) {
    g.add(viga([0, 0.04, z], [0, 0.2, z], 0.07, 0.07, MAT.marco));
    g.add(viga([-0.26, 0.04, z], [0.26, 0.04, z], 0.07, 0.06, MAT.marco));
  }
  for (const s of [-1, 1]) { const r = M(new THREE.CylinderGeometry(0.04, 0.04, 0.03, 14), MAT.caucho); r.rotation.z = Math.PI / 2; r.position.set(s * 0.2, 0.05, -d / 2 + 0.06); g.add(r); }
  const sz = cojin(0.3, 0.07, 0.36, MAT.tapiz, 0, 0.46, d / 2 - 0.3); sz.rotation.x = -0.12; g.add(sz);
  g.add(viga([0, 0.2, d / 2 - 0.3], [0, 0.42, d / 2 - 0.3], 0.06, 0.06, MAT.marco));
  const a = THREE.MathUtils.degToRad(incl), Lr = 0.84, z0 = d / 2 - 0.5;
  const r = cojin(0.3, 0.07, Lr, MAT.tapiz, 0, 0.46 + (Lr / 2) * Math.sin(a), z0 - (Lr / 2) * Math.cos(a)); r.rotation.x = a; g.add(r);
  if (incl > 3) g.add(viga([0, 0.2, z0 - 0.62], [0, 0.44 + Lr * 0.62 * Math.sin(a), z0 - Lr * 0.62 * Math.cos(a)], 0.045, 0.045, MAT.gris));
  else g.add(viga([0, 0.2, z0 - 0.5], [0, 0.42, z0 - 0.5], 0.06, 0.06, MAT.marco));
  return g;
}
const PANTALLA = std(0x13202e, 0.25, 0.2, { emissive: 0x2f8fe0, emissiveIntensity: 0.7 });
// Cinta de correr: +z = lado de entrada (atrás); la consola queda en -z
function cinta(w, d) {
  const g = G(), zF = -d / 2, zR = d / 2, xs = w / 2 - 0.09;
  g.add(caja(w - 0.06, 0.15, d - 0.44, MAT.marco, 0, 0.145, 0.21));
  g.add(caja(w - 0.32, 0.012, d - 0.5, MAT.caucho, 0, 0.226, 0.21));
  for (const s of [-1, 1]) {
    g.add(caja(0.11, 0.03, d - 0.46, MAT.gris, s * (w / 2 - 0.085), 0.236, 0.21));
    g.add(viga([s * xs, 0.26, zF + 0.3], [s * xs, 1.33, zF + 0.13], 0.07, 0.09, MAT.marco));
    g.add(tubo([s * xs, 1.14, zF + 0.17], [s * xs, 1.06, zF + 0.86], 0.022, MAT.caucho));
    g.add(tubo([s * xs, 1.06, zF + 0.86], [s * xs, 0.98, zF + 0.9], 0.022, MAT.caucho));
    g.add(caja(0.09, 0.05, 0.12, MAT.marco2, s * (w / 2 - 0.08), 0.03, zR - 0.14), caja(0.09, 0.05, 0.12, MAT.marco2, s * (w / 2 - 0.08), 0.03, zF + 0.16));
  }
  g.add(cojin(w - 0.04, 0.27, 0.52, MAT.marco2, 0, 0.205, zF + 0.28, 0.07));                 // capó del motor
  g.add(caja(w - 0.3, 0.012, 0.3, MAT.rojo, 0, 0.344, zF + 0.28));
  const con = cojin(w - 0.1, 0.36, 0.09, MAT.marco2, 0, 1.43, zF + 0.13, 0.03); con.rotation.x = -0.45; g.add(con);
  const pan = caja(w * 0.5, 0.2, 0.008, PANTALLA, 0, 1.455, zF + 0.178); pan.rotation.x = -0.45; pan.castShadow = false; g.add(pan);
  g.add(tubo([-xs, 1.2, zF + 0.22], [xs, 1.2, zF + 0.22], 0.02, MAT.caucho));
  g.add(tubo([-(w / 2 - 0.12), 0.15, zR - 0.02], [w / 2 - 0.12, 0.15, zR - 0.02], 0.045, MAT.gris, 16));
  return g;
}
// Bicicleta estática tipo spinning: +z = lado de entrada (atrás); el manubrio queda en -z
function bici(w, d) {
  const g = G(), zF = -d / 2, zR = d / 2, zV = zF + 0.34;
  for (const z of [zF + 0.1, zR - 0.1]) g.add(viga([-w / 2 + 0.03, 0.04, z], [w / 2 - 0.03, 0.04, z], 0.07, 0.06, MAT.marco));
  g.add(viga([0, 0.07, zF + 0.1], [0, 0.07, zR - 0.1], 0.07, 0.06, MAT.marco));
  const vol = M(new THREE.CylinderGeometry(0.24, 0.24, 0.05, 40), MAT.marco2); vol.rotation.z = Math.PI / 2; vol.position.set(0, 0.34, zV); g.add(vol);
  const aro = M(new THREE.CylinderGeometry(0.19, 0.19, 0.056, 36), MAT.rojo); aro.rotation.z = Math.PI / 2; aro.position.set(0, 0.34, zV); g.add(aro);
  const cub = M(new THREE.CylinderGeometry(0.06, 0.06, 0.07, 20), MAT.cromo); cub.rotation.z = Math.PI / 2; cub.position.set(0, 0.34, zV); g.add(cub);
  g.add(caja(0.09, 0.2, 0.34, MAT.marco, 0, 0.6, zV + 0.02));                                   // guarda del volante
  g.add(viga([0, 0.1, 0.1], [0, 0.66, zV + 0.16], 0.06, 0.08, MAT.marco));
  g.add(viga([0, 0.1, 0.1], [0, 0.84, 0.3], 0.055, 0.075, MAT.marco));
  g.add(viga([0, 0.66, zV + 0.16], [0, 1.0, zF + 0.3], 0.055, 0.065, MAT.marco));
  g.add(tubo([0, 0.84, 0.3], [0, 0.96, 0.34], 0.018, MAT.cromo, 10));
  g.add(cojin(0.17, 0.06, 0.27, MAT.tapiz, 0, 0.99, 0.35, 0.025));
  g.add(tubo([0, 1.0, zF + 0.3], [0, 1.1, zF + 0.27], 0.016, MAT.cromo, 10));
  g.add(tubo([-0.21, 1.1, zF + 0.27], [0.21, 1.1, zF + 0.27], 0.016, MAT.caucho, 10));
  for (const s of [-1, 1]) g.add(tubo([s * 0.21, 1.1, zF + 0.27], [s * 0.2, 1.13, zF + 0.08], 0.016, MAT.caucho, 10));
  g.add(caja(0.14, 0.09, 0.02, PANTALLA, 0, 1.17, zF + 0.24));
  g.add(tubo([-0.1, 0.3, 0.1], [0.1, 0.3, 0.1], 0.02, MAT.cromo, 10));
  for (const s of [-1, 1]) {
    g.add(viga([s * 0.1, 0.3, 0.1], [s * 0.1, 0.3 - s * 0.14, 0.1 + s * 0.09], 0.02, 0.03, MAT.cromo));
    g.add(caja(0.09, 0.02, 0.07, MAT.caucho, s * 0.15, 0.3 - s * 0.14, 0.1 + s * 0.09));
  }
  return g;
}
export function portaDiscos() {
  const g = G();
  g.add(viga([-0.28, 0.03, 0], [0.28, 0.03, 0], 0.07, 0.06, MAT.marco));
  g.add(viga([0, 0.03, -0.28], [0, 0.03, 0.28], 0.07, 0.06, MAT.marco));
  g.add(viga([0, 0.03, 0], [0, 1.15, 0], 0.07, 0.07, MAT.marco));
  const filas = [[0.28, [25, 25]], [0.62, [20, 15]], [0.95, [10, 5, 5]]];
  for (const [y, l] of filas) for (const s of [-1, 1]) { g.add(tubo([s * 0.035, y, 0], [s * 0.26, y, 0], 0.024, MAT.cromo)); discos(g, l, s * 0.05, y, 0, s); }
  return g;
}

const FAB = {
  mancuernero, porta_barras: portaBarras, triceps, biceps, extension, aductor, crossover, prensa,
  hip_thrust: hipThrust, press_plano: pressPlano, dominadas, banco, cinta, bici,
};
const GIRO = { S: 0, N: Math.PI, E: Math.PI / 2, O: -Math.PI / 2 };   // frente local +z -> dirección en planta
let _nBanco = 0;
export function crearMaquina(m) {
  const g = m.tipo === 'banco' ? banco(m.w, m.d, (_nBanco++ % 2) ? 0 : 42) : FAB[m.tipo](m.w, m.d);
  const cont = G(); cont.add(g);
  cont.position.set(m.c[0], 0, m.c[1]);
  cont.rotation.y = GIRO[m.frente];
  cont.name = m.id;
  return cont;
}

// ------------------------------------------------------------------ figuras humanas (maniquí deportivo)
const ROPA = [0xd81f26, 0x1f6f8b, 0xf2f2ef, 0x2b2d31, 0xe2b007, 0x4b3f72];
export function persona(o = {}) {
  const { pose = 'pie', polo = 0, alto = 1.7, brazoI = [0.12, 0, 0.1, 0], brazoD = [0.12, 0, 0.1, 0], mono = true } = o;
  const k = alto / 1.7, g = G();
  const mPolo = mono ? std(0xc9ccd1, 0.85, 0) : std(ROPA[polo % ROPA.length], 0.8, 0);
  const mShort = mono ? std(0x9da1a8, 0.85, 0) : std(0x1a1b1e, 0.85, 0), mZap = mono ? mShort : std(0xeeeeee, 0.7, 0);
  const piel = mono ? mPolo : MAT.piel;
  const sentado = pose === 'sentado';
  const yC = sentado ? (o.asiento ?? 0.5) + 0.1 : 0.93 * k;        // cadera
  const yH = yC + 0.5 * k;                                         // hombros
  g.add(capsula([0, yC + 0.04, 0], [0, yH - 0.07, 0], 0.145 * k, mPolo));
  g.add(capsula([-0.07 * k, yC, 0], [0.07 * k, yC, 0], 0.115 * k, mShort));
  const cab = M(new THREE.SphereGeometry(0.105 * k, 20, 16), piel); cab.position.set(0, yH + 0.2 * k, 0.01); g.add(cab);
  g.add(capsula([0, yH + 0.02, 0], [0, yH + 0.1 * k, 0], 0.045 * k, piel));
  if (!mono) { const pelo = M(new THREE.SphereGeometry(0.108 * k, 20, 12, 0, Math.PI * 2, 0, Math.PI * 0.55), std(0x1a1512, 0.9, 0)); pelo.position.set(0, yH + 0.215 * k, -0.005); g.add(pelo); }
  // piernas
  for (const s of [-1, 1]) {
    const cx = s * 0.095 * k;
    if (sentado) {
      const rod = [cx * 1.25, yC + 0.02, 0.42 * k], pie = [cx * 1.25, 0.09, 0.44 * k];
      g.add(capsula([cx, yC, 0.02], rod, 0.075 * k, mShort)); g.add(capsula(rod, pie, 0.052 * k, piel));
      g.add(cojin(0.09, 0.07, 0.24, mZap, pie[0], 0.04, pie[2] + 0.06, 0.02));
    } else {
      const zp = (o.paso ?? 0) * s, rod = [cx, 0.5 * k, zp * 0.45 + 0.02], pie = [cx, 0.09, zp];
      g.add(capsula([cx, yC, 0], [rod[0], rod[1] + 0.12 * k, rod[2]], 0.075 * k, mShort));
      g.add(capsula([rod[0], rod[1] + 0.1 * k, rod[2]], rod, 0.058 * k, piel)); g.add(capsula(rod, pie, 0.05 * k, piel));
      g.add(cojin(0.09, 0.07, 0.25, mZap, pie[0], 0.04, pie[2] + 0.06, 0.02));
    }
  }
  // brazos: [abrir, adelante] del brazo y del antebrazo (radianes desde la vertical hacia abajo)
  const brazo = (s, [ab, ad, ab2, ad2]) => {
    const h = [s * 0.2 * k, yH - 0.03, 0];
    const dir = (a, f) => [s * Math.sin(a) * Math.cos(f), -Math.cos(a) * Math.cos(f), Math.sin(f)];
    const d1 = dir(ab, ad), L1 = 0.29 * k, c = [h[0] + d1[0] * L1, h[1] + d1[1] * L1, h[2] + d1[2] * L1];
    const d2 = dir(ab2, ad2), L2 = 0.27 * k, m = [c[0] + d2[0] * L2, c[1] + d2[1] * L2, c[2] + d2[2] * L2];
    g.add(capsula(h, c, 0.047 * k, mPolo)); g.add(capsula(c, m, 0.04 * k, piel));
    const mano = M(new THREE.SphereGeometry(0.045 * k, 10, 8), piel); mano.position.set(...m); g.add(mano);
    return m;
  };
  g.userData.manoI = brazo(-1, brazoI); g.userData.manoD = brazo(1, brazoD);
  return g;
}
