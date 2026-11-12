// Vehículos low-poly con acabado de maqueta arquitectónica (archviz), en metros.
//
// Interfaz (la usa main.js):
//   DIMENSIONES[tipo] = {largo, ancho, alto}
//   COLORES_AUTOS = [...]
//   crearVehiculo(tipo, {color, seed, sombra = true}) -> THREE.Group
//     - sombra: false omite la sombra de contacto propia (huella + neumáticos, y = 0.014).
//     - frente hacia +X, centrado en su huella, ruedas apoyadas en y = 0.
//     - group.userData.ruedas = grupos de rueda; cada uno gira sobre su eje Z local.
//
// Los autos se modelan como un "loft": una sucesión de secciones transversales a lo largo
// de X (perfil lateral de techo, piso con pasos de rueda, línea de cintura, redondeo en planta
// y caída del techo hacia los lados). Cada cara del loft se clasifica por material (pintura,
// vidrio, faros, plástico negro...), de modo que parabrisas, ventanas, pilares y faros salen
// de la misma superficie. Las geometrías se cachean por tipo/variante y los materiales por color.
import * as THREE from 'three';
import { mergeGeometries, toCreasedNormals } from 'three/addons/utils/BufferGeometryUtils.js';
import { rng } from './texturas.js';

export const DIMENSIONES = {
  sedan: { largo: 4.50, ancho: 1.75, alto: 1.45 },
  hatchback: { largo: 4.00, ancho: 1.70, alto: 1.50 },
  suv: { largo: 4.70, ancho: 1.85, alto: 1.75 },
  pickup: { largo: 5.30, ancho: 1.85, alto: 1.82 },
  van: { largo: 5.30, ancho: 1.90, alto: 2.30 },
  moto: { largo: 2.00, ancho: 0.75, alto: 1.10 },
  mototaxi: { largo: 2.80, ancho: 1.35, alto: 1.75 },
};

// blanco, plata, gris, grafito, negro, rojo vino, rojo, azul, champagne, azul acero
export const COLORES_AUTOS = ['#ebebe7', '#c3c6c9', '#868b90', '#45494e', '#141516', '#6a1016', '#9c1a17', '#1b3260',
  '#cfc5ae', '#34495b'];

// ===================================================================== materiales
const MATS = new Map();
function cache(clave, crear) {
  let m = MATS.get(clave);
  if (!m) { m = crear(); m.name = clave; MATS.set(clave, m); }
  return m;
}

// acabado [metalness, roughness] de los colores de catálogo (sólidos vs. metalizados)
const ACABADO = {
  ebebe7: [0.0, 0.25], c3c6c9: [0.75, 0.3], '868b90': [0.7, 0.32], '45494e': [0.6, 0.32], '141516': [0.15, 0.2],
  '6a1016': [0.45, 0.3], '9c1a17': [0.0, 0.25], '1b3260': [0.5, 0.3], cfc5ae: [0.55, 0.32], '34495b': [0.55, 0.32],
};
// La escena tiene sol fuerte + cielo como luz ambiental: se calibra el albedo de la pintura para que los colores
// se lean como pintura automotriz real (sin esto los rojos/azules saturados se ven pastel). Calibrado con la
// iluminación de main.js (sol 2.7, hemisferio 0.42, exposición 0.86, entorno con suelo).
const ALBEDO_PINTURA = 0.63;

function matPintura(color) {
  const c = new THREE.Color(color);
  const hex = c.getHexString();
  return cache('pintura_' + hex, () => {
    let ac = ACABADO[hex];
    if (!ac) {
      const hsl = {};
      c.getHSL(hsl, THREE.SRGBColorSpace);
      ac = (hsl.l > 0.8 || hsl.l < 0.12 || hsl.s > 0.5) ? [0.0, 0.27] : [0.45, 0.32];
    }
    return new THREE.MeshPhysicalMaterial({ color: c.clone().multiplyScalar(ALBEDO_PINTURA), metalness: ac[0],
      roughness: ac[1], clearcoat: 1.0, clearcoatRoughness: 0.06, envMapIntensity: 0.65 });
  });
}

const BASE = {
  vidrio: () => new THREE.MeshPhysicalMaterial({ color: 0x0d1218, metalness: 0.0, roughness: 0.03, ior: 1.5,
    clearcoat: 1.0, clearcoatRoughness: 0.02, envMapIntensity: 1.0 }),
  mica: () => new THREE.MeshPhysicalMaterial({ color: 0x8d99a3, metalness: 0.0, roughness: 0.06, clearcoat: 1,
    transparent: true, opacity: 0.32, depthWrite: false }),
  negro: () => new THREE.MeshStandardMaterial({ color: 0x151617, roughness: 0.45, metalness: 0.15 }),
  negroMate: () => new THREE.MeshStandardMaterial({ color: 0x111213, roughness: 0.9, metalness: 0.0 }),
  cromo: () => new THREE.MeshStandardMaterial({ color: 0xdadde0, roughness: 0.14, metalness: 1.0 }),
  aluminio: () => new THREE.MeshStandardMaterial({ color: 0xb0b4b8, roughness: 0.34, metalness: 0.9 }),
  motor: () => new THREE.MeshStandardMaterial({ color: 0x7c8085, roughness: 0.42, metalness: 0.85 }),
  stop: () => new THREE.MeshPhysicalMaterial({ color: 0x6a080c, metalness: 0.1, roughness: 0.32, clearcoat: 0.4,
    clearcoatRoughness: 0.06, emissive: 0x320204, envMapIntensity: 0.6 }),
  ambar: () => new THREE.MeshPhysicalMaterial({ color: 0xd9861a, metalness: 0.1, roughness: 0.25, clearcoat: 1,
    emissive: 0x2a1300 }),
  cuero: () => new THREE.MeshStandardMaterial({ color: 0x1b1b1c, roughness: 0.62, metalness: 0.0 }),
  lona: () => new THREE.MeshStandardMaterial({ color: 0x24282d, roughness: 0.95, metalness: 0.0 }),
};

function lienzo(w, h) {
  const c = document.createElement('canvas');
  c.width = w; c.height = h;
  return [c, c.getContext('2d')];
}

// --- placa peruana (blanca, borde y caracteres negros)
function texPlaca(i) {
  const R = rng(9001 + i * 31);
  const LET = 'ABCDFGHKLMPRSTUVWXZ';
  const ch = () => LET[Math.floor(R() * LET.length)];
  const dg = () => String(Math.floor(R() * 10));
  const txt = `${ch()}${dg()}${ch()}-${dg()}${dg()}${dg()}`;
  const [cv, x] = lienzo(256, 128);
  x.fillStyle = '#f4f4f0'; x.fillRect(0, 0, 256, 128);
  x.strokeStyle = '#1b1b1b'; x.lineWidth = 6;
  x.beginPath(); x.roundRect(4, 4, 248, 120, 10); x.stroke();
  x.fillStyle = '#1d3f8a'; x.font = 'bold 20px "Liberation Sans", Arial, sans-serif';
  x.textAlign = 'center'; x.textBaseline = 'middle';
  x.fillText('PERÚ', 128, 24);
  x.fillStyle = '#121212'; x.font = 'bold 62px "Liberation Sans Narrow", "Liberation Sans", Arial, sans-serif';
  x.fillText(txt, 128, 80);
  const t = new THREE.CanvasTexture(cv);
  t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 4;
  return t;
}
function matPlaca(i) {
  return cache('placa_' + i, () => new THREE.MeshStandardMaterial({ map: texPlaca(i), roughness: 0.5, metalness: 0.1 }));
}

// --- aros: textura de color + textura rugosidad(G)/metal(B); el caucho usa la esquina del lienzo
const PAL_COLOR = { caucho: '#141414', labio: '#c9ccce', hueco: '#0c0c0d', metal: '#c4c7ca', oscuro: '#55595e',
  negro: '#1f2022', acero: '#a3a7ab', tapa: '#cfd2d5', tuerca: '#8d9195', freno: '#56585a' };
const PAL_MR = { caucho: 'rgb(0,232,0)', labio: 'rgb(0,77,255)', hueco: 'rgb(0,230,70)', metal: 'rgb(0,82,242)',
  oscuro: 'rgb(0,100,215)', negro: 'rgb(0,110,150)', acero: 'rgb(0,115,205)', tapa: 'rgb(0,90,150)',
  tuerca: 'rgb(0,77,255)', freno: 'rgb(0,150,205)' };

function dibujarAro(x, d, P) {
  const C = 128, R = 128;
  const circ = (r, col) => { x.fillStyle = col; x.beginPath(); x.arc(C, C, r, 0, Math.PI * 2); x.fill(); };
  const anillo = (r, w, col) => { x.strokeStyle = col; x.lineWidth = w; x.beginPath(); x.arc(C, C, r, 0, Math.PI * 2); x.stroke(); };
  const rayo = (a, r0, r1, w0, w1, col) => {
    const ca = Math.cos(a), sa = Math.sin(a), tx = -sa, ty = ca;
    x.fillStyle = col;
    x.beginPath();
    x.moveTo(C + ca * r0 + tx * w0, C + sa * r0 + ty * w0);
    x.lineTo(C + ca * r1 + tx * w1, C + sa * r1 + ty * w1);
    x.lineTo(C + ca * r1 - tx * w1, C + sa * r1 - ty * w1);
    x.lineTo(C + ca * r0 - tx * w0, C + sa * r0 - ty * w0);
    x.closePath(); x.fill();
  };
  const tuercas = (n, rr, col) => {
    for (let i = 0; i < n; i++) {
      const a = i * Math.PI * 2 / n;
      x.fillStyle = col; x.beginPath(); x.arc(C + Math.cos(a) * rr, C + Math.sin(a) * rr, R * 0.035, 0, Math.PI * 2); x.fill();
    }
  };
  x.fillStyle = P.caucho; x.fillRect(0, 0, 256, 256);
  circ(R, P.labio);
  if (d === 'acero') {
    circ(R * 0.9, P.acero);
    anillo(R * 0.8, 3, P.hueco);
    for (let i = 0; i < 8; i++) {
      const a = i * Math.PI / 4 + Math.PI / 8;
      x.save(); x.translate(C + Math.cos(a) * R * 0.62, C + Math.sin(a) * R * 0.62); x.rotate(a);
      x.fillStyle = P.hueco; x.beginPath(); x.roundRect(-R * 0.06, -R * 0.12, R * 0.12, R * 0.24, R * 0.05); x.fill();
      x.restore();
    }
    circ(R * 0.36, P.tapa);
    anillo(R * 0.33, 2, P.tuerca);
    circ(R * 0.1, P.tuerca);
    return;
  }
  if (d === 'rayos') {
    circ(R * 0.88, P.hueco);
    anillo(R * 0.84, R * 0.09, P.metal);
    x.strokeStyle = P.metal; x.lineWidth = 2;
    for (let i = 0; i < 36; i++) {
      const a = i * Math.PI * 2 / 36, b = a + (i % 2 ? 0.5 : -0.5);
      x.beginPath(); x.moveTo(C + Math.cos(a) * R * 0.16, C + Math.sin(a) * R * 0.16);
      x.lineTo(C + Math.cos(b) * R * 0.8, C + Math.sin(b) * R * 0.8); x.stroke();
    }
    circ(R * 0.2, P.metal); circ(R * 0.1, P.oscuro);
    return;
  }
  // aros de aleación
  circ(R * 0.9, P.hueco);
  circ(R * 0.58, P.freno); circ(R * 0.3, P.hueco);
  const n = d === 'multi10' ? 10 : (d === 'oscura6' || d === 'aleacion6') ? 6 : 5;
  const col = d === 'oscura6' ? P.oscuro : d === 'moto' ? P.negro : P.metal;
  const doble = d === 'aleacion5' || d === 'moto';
  for (let i = 0; i < n; i++) {
    const a = i * Math.PI * 2 / n - Math.PI / 2;
    if (doble) {
      rayo(a - 0.1, R * 0.2, R * 0.9, R * 0.05, R * 0.04, col);
      rayo(a + 0.1, R * 0.2, R * 0.9, R * 0.05, R * 0.04, col);
    } else if (n === 10) rayo(a, R * 0.2, R * 0.9, R * 0.045, R * 0.035, col);
    else rayo(a, R * 0.2, R * 0.9, R * 0.1, R * 0.07, col);
  }
  anillo(R * 0.86, R * 0.07, col);
  circ(R * 0.27, col);
  tuercas(d === 'moto' ? 0 : n === 6 ? 6 : 5, R * 0.17, P.tuerca);
  circ(R * 0.09, d === 'moto' ? P.metal : P.tapa);
}

function matAro(d) {
  return cache('aro_' + d, () => {
    const [c1, x1] = lienzo(256, 256); dibujarAro(x1, d, PAL_COLOR);
    const [c2, x2] = lienzo(256, 256); dibujarAro(x2, d, PAL_MR);
    const map = new THREE.CanvasTexture(c1); map.colorSpace = THREE.SRGBColorSpace; map.anisotropy = 4;
    const mr = new THREE.CanvasTexture(c2);
    return new THREE.MeshStandardMaterial({ map, roughnessMap: mr, metalnessMap: mr, roughness: 1, metalness: 1 });
  });
}

// --- parrilla: lamas horizontales (textura repetible)
function matParrilla(cromada) {
  return cache(cromada ? 'parrillaCromo' : 'parrilla', () => {
    const [cv, x] = lienzo(64, 64);
    x.fillStyle = '#0b0b0c'; x.fillRect(0, 0, 64, 64);
    x.fillStyle = cromada ? '#b9bdc1' : '#3b3e42';
    for (let i = 0; i < 3; i++) x.fillRect(0, 4 + i * 21, 64, 9);
    x.fillStyle = cromada ? '#e6e8ea' : '#55585c';
    for (let i = 0; i < 3; i++) x.fillRect(0, 4 + i * 21, 64, 2);
    const t = new THREE.CanvasTexture(cv);
    t.colorSpace = THREE.SRGBColorSpace;
    t.wrapS = t.wrapT = THREE.RepeatWrapping;
    return new THREE.MeshStandardMaterial({ map: t, roughness: 0.35, metalness: cromada ? 0.8 : 0.4 });
  });
}

// --- sombra de contacto (oclusión ambiental): huella del vehículo + manchas bajo cada neumático. Es una sombra
// "ajustada": no sale más de ~10 cm de la huella, de modo que se puede sumar a una sombra ambiental amplia y
// difusa (p. ej. la de main.js) sin formar un halo oscuro. Se desactiva con crearVehiculo(tipo, {sombra: false}).
//   L, A: tamaño del plano (m); cuerpo: [[x0, x1, z0, z1, alfa]]; ruedas: [[x, z, rx, rz, alfa]]
function sombraContacto(clave, L, A, cuerpo, ruedas) {
  const mat = cache('sombra_' + clave, () => {
    const [cv, x] = lienzo(256, 128);
    const kx = 256 / L, kz = 128 / A;
    const X = (v) => 128 + v * kx, Z = (v) => 64 + v * kz;
    x.filter = `blur(${(0.11 * kx).toFixed(1)}px)`;
    for (const [x0, x1, z0, z1, a] of cuerpo) {
      x.fillStyle = `rgba(0,0,0,${a})`;
      x.beginPath(); x.roundRect(X(x0), Z(z0), (x1 - x0) * kx, (z1 - z0) * kz, Math.min(0.25 * kz, (z1 - z0) * kz / 2)); x.fill();
    }
    x.filter = `blur(${(0.035 * kx).toFixed(1)}px)`;
    for (const [cx, cz, rx, rz, a] of ruedas) {
      x.fillStyle = `rgba(0,0,0,${a})`;
      x.beginPath(); x.ellipse(X(cx), Z(cz), rx * kx, rz * kz, 0, 0, Math.PI * 2); x.fill();
    }
    const t = new THREE.CanvasTexture(cv);
    t.colorSpace = THREE.SRGBColorSpace;
    return new THREE.MeshBasicMaterial({ color: 0x000000, map: t, transparent: true, depthWrite: false,
      polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -4, toneMapped: false });
  });
  const g = geoUnidad(`sombra${L}|${A}`, () => new THREE.PlaneGeometry(L, A).rotateX(-Math.PI / 2));
  const m = new THREE.Mesh(g, mat);
  m.position.set(0, 0.014, 0);   // sobre las líneas de plaza (0.008) y el símbolo accesible (0.012)
  m.renderOrder = 1;
  m.name = 'sombraContacto';
  return m;
}

// --- faro: carcasa oscura, reflector cromado, proyector y tira LED (u: de adentro hacia afuera)
function matFaro() {
  return cache('faro', () => {
    const [cv, x] = lienzo(128, 64);
    const gr = x.createLinearGradient(0, 0, 0, 64);
    gr.addColorStop(0, '#2c3237'); gr.addColorStop(0.5, '#181c20'); gr.addColorStop(1, '#3d454c');
    x.fillStyle = gr; x.fillRect(0, 0, 128, 64);
    const cr = x.createLinearGradient(0, 22, 0, 52);
    cr.addColorStop(0, '#59626a'); cr.addColorStop(0.5, '#aeb7be'); cr.addColorStop(1, '#3b4249');
    x.fillStyle = cr; x.beginPath(); x.roundRect(10, 24, 108, 26, 8); x.fill();
    x.fillStyle = '#f2f6ff'; x.beginPath(); x.roundRect(8, 9, 112, 7, 3); x.fill();
    const rg = x.createRadialGradient(40, 37, 1, 40, 37, 11);
    rg.addColorStop(0, '#101214'); rg.addColorStop(0.6, '#3a4248'); rg.addColorStop(1, '#8e98a0');
    x.fillStyle = rg; x.beginPath(); x.arc(40, 37, 11, 0, Math.PI * 2); x.fill();
    x.fillStyle = '#353c42'; x.fillRect(0, 58, 128, 6);
    const t = new THREE.CanvasTexture(cv);
    t.colorSpace = THREE.SRGBColorSpace;
    t.anisotropy = 4;
    return new THREE.MeshPhysicalMaterial({ map: t, metalness: 0.35, roughness: 0.18, clearcoat: 1,
      clearcoatRoughness: 0.02, emissive: 0x0d0e10 });
  });
}

function resolverMat(clave, color, v) {
  if (clave === 'pintura') return matPintura(color);
  if (clave === 'faro') return matFaro();
  if (clave === 'parrilla') return matParrilla(false);
  if (clave === 'parrillaCromo') return matParrilla(true);
  if (clave === 'franja') return matPintura(v.franja || '#b3261e');
  if (clave === 'placa') return matPlaca(v.placa);
  return cache(clave, BASE[clave]);
}

// ===================================================================== utilidades
const UV0 = [0, 0];

function mtx(x, y, z, rx = 0, ry = 0, rz = 0, sx = 1, sy = 1, sz = 1) {
  return new THREE.Matrix4().compose(new THREE.Vector3(x, y, z),
    new THREE.Quaternion().setFromEuler(new THREE.Euler(rx, ry, rz)), new THREE.Vector3(sx, sy, sz));
}

function normalCara(a, b, c) {
  const ux = b[0] - a[0], uy = b[1] - a[1], uz = b[2] - a[2];
  const vx = c[0] - a[0], vy = c[1] - a[1], vz = c[2] - a[2];
  const nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx;
  const l = Math.hypot(nx, ny, nz);
  if (l < 1e-10) return null;
  return [nx / l, ny / l, nz / l];
}

/** Polilínea con esquinas redondeadas: pts = [[x, y, radio?], ...] -> [[x, y], ...] ordenada por x */
function filete(pts, nArc = 3) {
  const out = [[pts[0][0], pts[0][1]]];
  for (let i = 1; i < pts.length - 1; i++) {
    const [px, py, r = 0] = pts[i];
    if (!r) { out.push([px, py]); continue; }
    const [ax, ay] = pts[i - 1], [bx, by] = pts[i + 1];
    let v1x = ax - px, v1y = ay - py, v2x = bx - px, v2y = by - py;
    const l1 = Math.hypot(v1x, v1y), l2 = Math.hypot(v2x, v2y);
    v1x /= l1; v1y /= l1; v2x /= l2; v2y /= l2;
    const ang = Math.acos(Math.max(-1, Math.min(1, v1x * v2x + v1y * v2y)));
    if (ang > Math.PI - 1e-3) { out.push([px, py]); continue; }
    const t = Math.min(r / Math.tan(ang / 2), 0.45 * l1, 0.45 * l2);
    const rr = t * Math.tan(ang / 2);
    const tax = px + v1x * t, tay = py + v1y * t, tbx = px + v2x * t, tby = py + v2y * t;
    let bix = v1x + v2x, biy = v1y + v2y;
    const bl = Math.hypot(bix, biy); bix /= bl; biy /= bl;
    const d = rr / Math.sin(ang / 2);
    const cx = px + bix * d, cy = py + biy * d;
    const a0 = Math.atan2(tay - cy, tax - cx), a1 = Math.atan2(tby - cy, tbx - cx);
    let da = a1 - a0;
    while (da > Math.PI) da -= 2 * Math.PI;
    while (da < -Math.PI) da += 2 * Math.PI;
    for (let k = 0; k <= nArc; k++) { const a = a0 + da * k / nArc; out.push([cx + rr * Math.cos(a), cy + rr * Math.sin(a)]); }
  }
  out.push([pts[pts.length - 1][0], pts[pts.length - 1][1]]);
  out.sort((p, q) => p[0] - q[0]);
  return out;
}

function interp(poly, x) {
  const n = poly.length;
  if (x <= poly[0][0]) return poly[0][1];
  if (x >= poly[n - 1][0]) return poly[n - 1][1];
  let lo = 0, hi = n - 1;
  while (hi - lo > 1) { const m = (lo + hi) >> 1; if (poly[m][0] <= x) lo = m; else hi = m; }
  const [x0, y0] = poly[lo], [x1, y1] = poly[hi];
  return x1 - x0 < 1e-9 ? Math.max(y0, y1) : y0 + (y1 - y0) * (x - x0) / (x1 - x0);
}

/** borde inferior con pasos de rueda (arco de radio ra centrado en el eje, a la altura r) */
function fondo(poly, ejes, r, ra) {
  return (x, lado = 0) => {
    let y = interp(poly, x);
    for (const xa of ejes) {
      const dx = x - xa;
      const dentro = (dx > -ra + 1e-7 && dx < ra - 1e-7) || (Math.abs(dx + ra) <= 1e-7 && lado > 0) ||
        (Math.abs(dx - ra) <= 1e-7 && lado < 0);
      if (dentro) y = Math.max(y, r + Math.sqrt(Math.max(0, ra * ra - dx * dx)));
    }
    return y;
  };
}

/** semiancho en planta con esquinas redondeadas (radio Rr atrás, Rf adelante) */
function planta(w2, x0, x1, Rr, Rf) {
  return (x) => {
    let w = w2;
    if (x > x1 - Rf) { const d = x - (x1 - Rf); w -= Rf - Math.sqrt(Math.max(0, Rf * Rf - d * d)); }
    if (x < x0 + Rr) { const d = x0 + Rr - x; w -= Rr - Math.sqrt(Math.max(0, Rr * Rr - d * d)); }
    return w;
  };
}

/** posiciones X de las secciones del loft (con prioridades y pares de quiebre en los pasos de rueda) */
function estaciones(o) {
  const { x0, x1 } = o;
  const C = [];
  const add = (x, p, lado = 0) => {
    if (x < x0 - 1e-6 || x > x1 + 1e-6) return;
    if (lado && (Math.abs(x - x0) < 1e-6 || Math.abs(x - x1) < 1e-6)) return;
    C.push({ x, p, lado });
  };
  for (let i = 0; i <= 4; i++) {
    const f = Math.sin(i / 4 * Math.PI / 2);
    add(x1 - o.Rf + o.Rf * f, 1); add(x0 + o.Rr - o.Rr * f, 1);
  }
  for (const poly of o.perfiles || []) for (const p of poly) add(p[0], 0);
  for (const xa of o.ejes || []) {
    const nA = o.nArco || 16;
    for (let i = 1; i < nA; i++) add(xa + o.ra * Math.cos(Math.PI * i / nA), 1);
    add(xa - o.ra, 2, -1); add(xa - o.ra, 2, 1); add(xa + o.ra, 2, -1); add(xa + o.ra, 2, 1);
  }
  for (const x of o.fijos || []) if (x !== undefined && x !== null) add(x, 1);
  for (const s of o.costuras || []) { add(s - 0.006, 2); add(s + 0.006, 2); }
  add(x0, 3); add(x1, 3);
  C.sort((a, b) => b.p - a.p);
  const K = [];
  const tol = (a, b) => (a.p >= 2 && b.p >= 2 ? 0.004 : a.p >= 1 && b.p >= 1 ? 0.012 : 0.045);
  for (const e of C) {
    let ok = true;
    for (const k of K) {
      const d = Math.abs(e.x - k.x);
      if (e.lado && k.lado && d < 1e-6) { if (e.lado === k.lado) { ok = false; break; } continue; }
      if (d < tol(e, k)) { ok = false; break; }
    }
    if (ok) K.push(e);
  }
  K.sort((a, b) => a.x - b.x || a.lado - b.lado);
  const R = [K[0]];
  for (let i = 1; i < K.length; i++) {
    const a = R[R.length - 1], b = K[i];
    const d = b.x - a.x;
    const n = Math.ceil(d / (o.paso || 0.28));
    for (let j = 1; j < n; j++) R.push({ x: a.x + d * j / n, p: 0, lado: 0 });
    R.push(b);
  }
  return R;
}

// ===================================================================== constructor de mallas
const _geoCache = new Map();
function geoUnidad(clave, crear) {
  let g = _geoCache.get(clave);
  if (!g) { g = crear(); _geoCache.set(clave, g); }
  return g;
}
const _Y = new THREE.Vector3(0, 1, 0);

/** caja con aristas achaflanadas (44 triángulos, normales planas) */
function geoCajaBisel(sx, sy, sz, b) {
  const X = sx / 2, Y = sy / 2, Z = sz / 2;
  b = Math.min(b, X * 0.45, Y * 0.45, Z * 0.45);
  const M = new Malla();
  const P = (i, j, k, e) => [i * (e === 0 ? X : X - b), j * (e === 1 ? Y : Y - b), k * (e === 2 ? Z : Z - b)];
  const cara = (pts) => {
    const c = [0, 0, 0];
    pts.forEach((p) => { c[0] += p[0]; c[1] += p[1]; c[2] += p[2]; });
    for (let i = 1; i < pts.length - 1; i++) {
      const n = normalCara(pts[0], pts[i], pts[i + 1]);
      if (!n) continue;
      if (n[0] * c[0] + n[1] * c[1] + n[2] * c[2] >= 0) M.tri('x', pts[0], pts[i], pts[i + 1], n, n, n);
      else { const m = [-n[0], -n[1], -n[2]]; M.tri('x', pts[0], pts[i + 1], pts[i], m, m, m); }
    }
  };
  for (const s of [-1, 1]) {
    cara([P(s, -1, -1, 0), P(s, 1, -1, 0), P(s, 1, 1, 0), P(s, -1, 1, 0)]);
    cara([P(-1, s, -1, 1), P(1, s, -1, 1), P(1, s, 1, 1), P(-1, s, 1, 1)]);
    cara([P(-1, -1, s, 2), P(1, -1, s, 2), P(1, 1, s, 2), P(-1, 1, s, 2)]);
  }
  for (const i of [-1, 1]) {
    for (const j of [-1, 1]) {
      cara([P(i, j, -1, 0), P(i, j, 1, 0), P(i, j, 1, 1), P(i, j, -1, 1)]);
      cara([P(i, -1, j, 0), P(i, 1, j, 0), P(i, 1, j, 2), P(i, -1, j, 2)]);
      cara([P(-1, i, j, 1), P(1, i, j, 1), P(1, i, j, 2), P(-1, i, j, 2)]);
      for (const k of [-1, 1]) cara([P(i, j, k, 0), P(i, j, k, 1), P(i, j, k, 2)]);
    }
  }
  return M.construir().geo;
}

class Malla {
  constructor() { this.cubos = new Map(); }
  cubo(m) {
    let c = this.cubos.get(m);
    if (!c) { c = { p: [], n: [], u: [] }; this.cubos.set(m, c); }
    return c;
  }
  tri(m, a, b, c, na, nb, nc, ua = UV0, ub = UV0, uc = UV0) {
    const k = this.cubo(m);
    k.p.push(a[0], a[1], a[2], b[0], b[1], b[2], c[0], c[1], c[2]);
    k.n.push(na[0], na[1], na[2], nb[0], nb[1], nb[2], nc[0], nc[1], nc[2]);
    k.u.push(ua[0], ua[1], ub[0], ub[1], uc[0], uc[1]);
  }
  triPlano(m, a, b, c, ua, ub, uc) {
    const n = normalCara(a, b, c);
    if (n) this.tri(m, a, b, c, n, n, n, ua, ub, uc);
  }
  /** triángulo orientado según las normales de vértice dadas */
  triOrient(m, a, b, c, na, nb, nc, ua, ub, uc) {
    const n = normalCara(a, b, c);
    if (!n) return;
    const s = n[0] * (na[0] + nb[0] + nc[0]) + n[1] * (na[1] + nb[1] + nc[1]) + n[2] * (na[2] + nb[2] + nc[2]);
    if (s >= 0) this.tri(m, a, b, c, na, nb, nc, ua, ub, uc);
    else this.tri(m, a, c, b, na, nc, nb, ua, uc, ub);
  }
  geo(m, g, matrix) {
    const gg = g.index ? g.toNonIndexed() : g.clone();
    if (matrix) gg.applyMatrix4(matrix);
    if (!gg.attributes.normal) gg.computeVertexNormals();
    const k = this.cubo(m);
    const P = gg.attributes.position.array, N = gg.attributes.normal.array, U = gg.attributes.uv ? gg.attributes.uv.array : null;
    for (let i = 0; i < P.length; i++) { k.p.push(P[i]); k.n.push(N[i]); }
    if (U) for (let i = 0; i < U.length; i++) k.u.push(U[i]);
    else for (let i = 0; i < P.length / 3; i++) k.u.push(0, 0);
    gg.dispose();
  }
  caja(m, sx, sy, sz, matrix, radio = 0) {
    const g = radio > 0
      ? geoUnidad(`cb${sx}|${sy}|${sz}|${radio}`, () => geoCajaBisel(sx, sy, sz, radio))
      : geoUnidad(`bx${sx}|${sy}|${sz}`, () => new THREE.BoxGeometry(sx, sy, sz));
    this.geo(m, g, matrix);
  }
  tubo(m, a, b, r, seg = 8, tapas = true) {
    const va = new THREE.Vector3(...a), vb = new THREE.Vector3(...b);
    const d = vb.clone().sub(va);
    const len = d.length();
    if (len < 1e-6) return;
    const q = new THREE.Quaternion().setFromUnitVectors(_Y, d.normalize());
    const g = geoUnidad(`cy${seg}|${tapas}`, () => new THREE.CylinderGeometry(1, 1, 1, seg, 1, !tapas));
    this.geo(m, g, new THREE.Matrix4().compose(va.add(vb).multiplyScalar(0.5), q, new THREE.Vector3(r, len, r)));
  }
  /** polilínea de tubos */
  tubos(m, pts, r, seg = 8, tapas = false) {
    for (let i = 0; i < pts.length - 1; i++) this.tubo(m, pts[i], pts[i + 1], r, seg, tapas);
  }
  /** extrusión de una forma (plano XY) centrada en Z, con bisel suave */
  extruir(m, shape, prof, bisel, matrix, curvas = 6, segBisel = 2) {
    let g = new THREE.ExtrudeGeometry(shape, { depth: prof, bevelEnabled: bisel > 0, bevelThickness: bisel,
      bevelSize: bisel * 0.85, bevelSegments: segBisel, curveSegments: curvas, steps: 1 });
    g.translate(0, 0, -prof / 2);
    g = toCreasedNormals(g, 0.75);
    this.geo(m, g, matrix);
    g.dispose();
  }
  construir() {
    const geos = [], claves = [];
    for (const [m, k] of this.cubos) {
      if (!k.p.length) continue;
      const g = new THREE.BufferGeometry();
      g.setAttribute('position', new THREE.Float32BufferAttribute(k.p, 3));
      g.setAttribute('normal', new THREE.Float32BufferAttribute(k.n, 3));
      g.setAttribute('uv', new THREE.Float32BufferAttribute(k.u, 2));
      geos.push(g); claves.push(m);
    }
    const geo = mergeGeometries(geos, true);
    geos.forEach((g) => g.dispose());
    geo.computeBoundingBox();
    geo.computeBoundingSphere();
    return { geo, claves };
  }
}

const FASE = -Math.PI / 2;   // un vértice de cada anillo queda justo abajo (apoyo exacto en y = 0)

/** sólido de revolución alrededor del eje Z: perfil [{r, a, uv}] (a = coordenada axial) */
function torno(M, m, perfil, seg, quiebre = 60) {
  const cq = Math.cos(quiebre * Math.PI / 180);
  const n = perfil.length;
  const sn = [];
  for (let i = 0; i < n - 1; i++) {
    const dr = perfil[i + 1].r - perfil[i].r, da = perfil[i + 1].a - perfil[i].a;
    const l = Math.hypot(dr, da);
    sn.push(l < 1e-9 ? null : [da / l, -dr / l]);
  }
  const nPunto = (i, s) => {
    const own = sn[s];
    let j = i === s ? s - 1 : s + 1;
    while (j >= 0 && j < sn.length && !sn[j]) j += i === s ? -1 : 1;
    const o = sn[j];
    if (!o || own[0] * o[0] + own[1] * o[1] < cq) return own;
    const x = own[0] + o[0], y = own[1] + o[1], l = Math.hypot(x, y);
    return [x / l, y / l];
  };
  for (let s = 0; s < n - 1; s++) {
    if (!sn[s]) continue;
    const p0 = perfil[s], p1 = perfil[s + 1];
    const n0 = nPunto(s, s), n1 = nPunto(s + 1, s);
    for (let j = 0; j < seg; j++) {
      const t0 = FASE + j / seg * Math.PI * 2, t1 = FASE + (j + 1) / seg * Math.PI * 2;
      const c0 = Math.cos(t0), s0 = Math.sin(t0), c1 = Math.cos(t1), s1 = Math.sin(t1);
      const A = [p0.r * c0, p0.r * s0, p0.a], B = [p1.r * c0, p1.r * s0, p1.a];
      const C = [p1.r * c1, p1.r * s1, p1.a], D = [p0.r * c1, p0.r * s1, p0.a];
      const nA = [n0[0] * c0, n0[0] * s0, n0[1]], nB = [n1[0] * c0, n1[0] * s0, n1[1]];
      const nC = [n1[0] * c1, n1[0] * s1, n1[1]], nD = [n0[0] * c1, n0[0] * s1, n0[1]];
      M.triOrient(m, A, B, C, nA, nB, nC, p0.uv, p1.uv, p1.uv);
      M.triOrient(m, A, C, D, nA, nC, nD, p0.uv, p1.uv, p0.uv);
    }
  }
}

/** disco del aro (cara hacia +Z o -Z) con leve abombado; UV = círculo completo de la textura */
function discoAro(M, m, rd, z, seg, signo = 1, domo = 0.022) {
  const anillos = [[rd, 0], [rd * 0.45, domo * 0.75], [0, domo]];
  for (let k = 0; k < anillos.length - 1; k++) {
    const [ra, za] = anillos[k], [rb, zb] = anillos[k + 1];
    for (let j = 0; j < seg; j++) {
      const t0 = FASE + j / seg * Math.PI * 2, t1 = FASE + (j + 1) / seg * Math.PI * 2;
      const P = (r, t, dz) => [r * Math.cos(t), r * Math.sin(t), z + signo * dz];
      const U = (r, t) => [0.5 + 0.5 * (r / rd) * Math.cos(t) * signo, 0.5 + 0.5 * (r / rd) * Math.sin(t)];
      const a = P(ra, t0, za), b = P(ra, t1, za), c = P(rb, t1, zb), d = P(rb, t0, zb);
      const nrm = [0, 0, signo];
      M.triOrient(m, a, b, c, nrm, nrm, nrm, U(ra, t0), U(ra, t1), U(rb, t1));
      if (rb > 0) M.triOrient(m, a, c, d, nrm, nrm, nrm, U(ra, t0), U(rb, t1), U(rb, t0));
    }
  }
}

const UV_CAUCHO = [0.02, 0.02], UV_LABIO = [0.975, 0.5];

/** geometría de rueda (eje Z, cara exterior hacia +Z). dosCaras: aro visible por ambos lados (motos) */
function geoRueda(r, ancho, kr, { seg = 18, dosCaras = false } = {}) {
  const clave = `rueda${r}|${ancho}|${kr}|${seg}|${dosCaras}`;
  return geoUnidad(clave, () => {
    const M = new Malla();
    const h = ancho / 2, rr = r * kr, hund = Math.min(0.03, h * 0.45);
    const flanco = rr + (r - rr) * 0.55;
    const P = [];
    if (dosCaras) {
      P.push({ r: rr * 0.97, a: -h + hund, uv: UV_LABIO }, { r: rr * 1.03, a: -h * 0.9, uv: UV_LABIO },
        { r: rr * 1.03, a: -h * 0.9, uv: UV_CAUCHO }, { r: flanco, a: -h, uv: UV_CAUCHO },
        { r: r - 0.022, a: -h * 0.62, uv: UV_CAUCHO }, { r, a: 0, uv: UV_CAUCHO },
        { r: r - 0.022, a: h * 0.62, uv: UV_CAUCHO }, { r: flanco, a: h, uv: UV_CAUCHO },
        { r: rr * 1.03, a: h * 0.9, uv: UV_CAUCHO }, { r: rr * 1.03, a: h * 0.9, uv: UV_LABIO },
        { r: rr * 0.97, a: h - hund, uv: UV_LABIO });
    } else {
      // el flanco interior (no visible desde fuera) va en un solo tramo
      P.push({ r: rr * 1.0, a: -h * 0.92, uv: UV_CAUCHO },
        { r, a: -h * 0.6, uv: UV_CAUCHO }, { r, a: h * 0.6, uv: UV_CAUCHO },
        { r: flanco, a: h, uv: UV_CAUCHO }, { r: rr * 1.03, a: h * 0.93, uv: UV_CAUCHO },
        { r: rr * 1.03, a: h * 0.93, uv: UV_LABIO }, { r: rr * 0.97, a: h - hund, uv: UV_LABIO });
    }
    torno(M, 'aro', P, seg);
    discoAro(M, 'aro', rr * 0.97, h - hund, seg, 1);
    if (dosCaras) discoAro(M, 'aro', rr * 0.97, -h + hund, seg, -1);
    else {
      // tapa interior oscura (cierra la rueda por dentro)
      const nrm = [0, 0, -1];
      for (let j = 0; j < seg; j++) {
        const t0 = FASE + j / seg * Math.PI * 2, t1 = FASE + (j + 1) / seg * Math.PI * 2;
        M.triOrient('aro', [0, 0, -h * 0.9], [rr * Math.cos(t0), rr * Math.sin(t0), -h * 0.92],
          [rr * Math.cos(t1), rr * Math.sin(t1), -h * 0.92], nrm, nrm, nrm, UV_CAUCHO, UV_CAUCHO, UV_CAUCHO);
      }
    }
    return M.construir().geo;
  });
}

function rueda(geo, mat, x, y, z, lado) {
  const g = new THREE.Group();
  g.name = 'rueda';
  g.position.set(x, y, z);
  const m = new THREE.Mesh(geo, mat);
  if (lado < 0) m.rotation.y = Math.PI;
  m.castShadow = true;
  m.receiveShadow = true;
  g.add(m);
  return g;
}

// ===================================================================== loft
/**
 * ests: [{x, lado}] ascendente en X. anillo(est) -> semi-sección [[z, y], ...] desde el centro inferior
 * hasta el centro superior (z >= 0). duros[h]: punto con arista viva. clasif(k, q) -> material del
 * segmento k (entre los puntos k y k+1) para el tramo q. tapas.frente / tapas.atras: {cols, fn} (escalera,
 * requiere sección monótona en Y) o {earcut: material}.
 */
function loft(M, ests, anillo, duros, clasif, tapas = {}) {
  const anillos = ests.map((e) => anillo(e));
  const H = anillos[0].length;
  const full = [];
  for (let h = 0; h < H; h++) full.push([h, 1]);
  for (let h = H - 2; h >= 1; h--) full.push([h, -1]);
  const N = full.length;
  const colIn = new Array(N), colOut = new Array(N), colPt = [];
  let nc = 0;
  for (let j = 0; j < N; j++) {
    if (duros[full[j][0]]) { colIn[j] = nc++; colOut[j] = nc++; } else colIn[j] = colOut[j] = nc++;
    colPt[colIn[j]] = j; colPt[colOut[j]] = j;
  }
  const punto = (s, col) => { const [h, sg] = full[colPt[col]]; const [z, y] = anillos[s][h]; return [ests[s].x, y, z * sg]; };

  const tramo = (s0, s1, plano) => {
    if (s1 <= s0) return;
    const nS = s1 - s0 + 1;
    const P = new Float32Array(nS * nc * 3);
    for (let s = s0; s <= s1; s++) for (let c = 0; c < nc; c++) P.set(punto(s, c), ((s - s0) * nc + c) * 3);
    const idx = (s, c) => (s - s0) * nc + c;
    const tris = [];
    const area = (a, b, c) => normalCara([P[a * 3], P[a * 3 + 1], P[a * 3 + 2]], [P[b * 3], P[b * 3 + 1], P[b * 3 + 2]],
      [P[c * 3], P[c * 3 + 1], P[c * 3 + 2]]);
    for (let s = s0; s < s1; s++) {
      const xa = ests[s].x, xb = ests[s + 1].x;
      for (let j = 0; j < N; j++) {
        const j2 = (j + 1) % N;
        const k = Math.min(full[j][0], full[j2][0]);
        const A = idx(s, colOut[j]), B = idx(s, colIn[j2]), C = idx(s + 1, colIn[j2]), D = idx(s + 1, colOut[j]);
        const yc = (P[A * 3 + 1] + P[B * 3 + 1] + P[C * 3 + 1] + P[D * 3 + 1]) / 4;
        const m = clasif(k, { xa, xb, xm: (xa + xb) / 2, yc, ancho: Math.abs(xb - xa) });
        if (!m) continue;
        if (area(A, C, B)) tris.push(m, A, C, B);
        if (area(A, D, C)) tris.push(m, A, D, C);
      }
    }
    let Nn = null;
    if (!plano) {
      const g = new THREE.BufferGeometry();
      g.setAttribute('position', new THREE.BufferAttribute(P, 3));
      const ind = [];
      for (let i = 0; i < tris.length; i += 4) ind.push(tris[i + 1], tris[i + 2], tris[i + 3]);
      g.setIndex(ind);
      g.computeVertexNormals();
      Nn = g.attributes.normal.array;
    }
    const v = (i) => [P[i * 3], P[i * 3 + 1], P[i * 3 + 2]];
    const n = (i) => [Nn[i * 3], Nn[i * 3 + 1], Nn[i * 3 + 2]];
    for (let i = 0; i < tris.length; i += 4) {
      const [m, a, b, c] = [tris[i], tris[i + 1], tris[i + 2], tris[i + 3]];
      if (plano) M.triPlano(m, v(a), v(b), v(c));
      else M.tri(m, v(a), v(b), v(c), n(a), n(b), n(c));
    }
  };

  let s0 = 0;
  for (let s = 0; s < ests.length - 1; s++) {
    if (Math.abs(ests[s + 1].x - ests[s].x) < 1e-6) { tramo(s0, s, false); tramo(s, s + 1, true); s0 = s + 1; }
  }
  tramo(s0, ests.length - 1, false);

  const cortes = (zE, cols) => {
    const r = [-zE];
    for (let i = cols.length - 1; i >= 0; i--) r.push(-Math.min(cols[i], zE));
    r.push(0);
    for (const c of cols) r.push(Math.min(c, zE));
    r.push(zE);
    return r;
  };
  const tapa = (s, t, signo) => {
    const R = anillos[s], x = ests[s].x;
    if (t.earcut) {
      const cont = full.map(([h, sg]) => new THREE.Vector2(R[h][0] * sg, R[h][1]));
      const lim = [cont[0]];
      for (let i = 1; i < cont.length; i++) if (cont[i].distanceTo(lim[lim.length - 1]) > 1e-5) lim.push(cont[i]);
      for (const [a, b, c] of THREE.ShapeUtils.triangulateShape(lim, [])) {
        const pa = [x, lim[a].y, lim[a].x], pb = [x, lim[b].y, lim[b].x], pc = [x, lim[c].y, lim[c].x];
        const nn = normalCara(pa, pb, pc);
        if (!nn) continue;
        if (nn[0] * signo > 0) M.triPlano(t.earcut, pa, pb, pc); else M.triPlano(t.earcut, pa, pc, pb);
      }
      return;
    }
    for (let h = 0; h < H - 1; h++) {
      const [z0, y0] = R[h], [z1, y1] = R[h + 1];
      if (y1 - y0 < 1e-5) continue;
      const a = cortes(z0, t.cols), b = cortes(z1, t.cols);
      for (let i = 0; i < a.length - 1; i++) {
        const p1 = [x, y0, a[i]], p2 = [x, y0, a[i + 1]], p3 = [x, y1, b[i + 1]], p4 = [x, y1, b[i]];
        const zc = Math.abs((a[i] + a[i + 1] + b[i] + b[i + 1]) / 4);
        const r = t.fn((y0 + y1) / 2, zc, Math.min(z0, z1), h);
        const m = typeof r === 'string' ? r : r.m;
        const uv = (p) => (r.uv ? r.uv(p[2], p[1]) : UV0);
        if (signo > 0) { M.triPlano(m, p1, p3, p2, uv(p1), uv(p3), uv(p2)); M.triPlano(m, p1, p4, p3, uv(p1), uv(p4), uv(p3)); }
        else { M.triPlano(m, p1, p2, p3, uv(p1), uv(p2), uv(p3)); M.triPlano(m, p1, p3, p4, uv(p1), uv(p3), uv(p4)); }
      }
    }
  };
  if (tapas.frente) tapa(ests.length - 1, tapas.frente, 1);
  if (tapas.atras) tapa(0, tapas.atras, -1);
  return anillos;
}

// ===================================================================== autos
// Perfiles: techo/piso = [[x, y, radio de empalme?], ...] (x: +frente). gh = tramo con cabina (vidrios),
// cintura = línea inferior de ventanas. niv = franjas horizontales (placas, faros, stops).
const AUTOS = {
  sedan: {
    L: 4.50, W: 1.75, r: 0.315, tw: 0.195, kr: 0.6, ejes: [1.36, -1.25], ra: 0.37,
    techo: [[2.25, 0.71], [2.15, 0.80, 0.12], [1.6, 0.885, 0.6], [0.96, 0.985, 0.05], [0.14, 1.39, 0.24],
      [-0.35, 1.42, 0.8], [-0.82, 1.375, 0.28], [-1.56, 1.045, 0.07], [-2.15, 1.0, 0.07], [-2.25, 0.93]],
    piso: [[2.25, 0.35], [2.12, 0.27, 0.1], [1.8, 0.24], [0.98, 0.205], [-0.86, 0.205], [-1.65, 0.24],
      [-2.06, 0.29, 0.1], [-2.25, 0.43]],
    gh: [-1.56, 0.96], cintura: [[-1.56, 1.045], [0.96, 0.985]],
    planta: [0.30, 0.22], rb: 0.06, rs: 0.06, ledge: 0.075, tumble: 0.34, rr: 0.09, crown: 0.03, bulge: 0.018,
    niv: { placaF: [0.40, 0.55], faro: [0.56, 0.64], placaT: [0.63, 0.78], stop: [0.76, 0.855] },
    parabrisas: [0.20, 0.93], luneta: [-1.52, -0.86],
    laterales: [[-1.32, 0.94]], pilares: [[-0.34, -0.25]],
    costuras: [0.90, -0.295, -1.12], manijas: [0.24, -0.70], manijaMat: 'cromo',
    faroLat: 2.0, stopLat: -2.07,
    frente: { parrilla: 0.33, toma: 0.40, faroIn: 0.40 },
    atras: { stopIn: 0.30 },
    escape: [-2.20, 0.29, -0.50], llantas: ['aleacion5', 'multi10', 'acero', 'aleacion5'],
  },
  hatchback: {
    L: 4.00, W: 1.70, r: 0.30, tw: 0.185, kr: 0.63, ejes: [1.20, -1.30], ra: 0.355,
    techo: [[2.0, 0.72], [1.90, 0.81, 0.12], [1.5, 0.89, 0.6], [0.95, 0.975, 0.05], [0.10, 1.44, 0.24],
      [-0.6, 1.47, 1.0], [-1.55, 1.45, 0.14], [-1.93, 1.06, 0.05], [-2.0, 0.99]],
    piso: [[2.0, 0.37], [1.88, 0.28, 0.08], [1.58, 0.23], [0.82, 0.20], [-0.92, 0.20], [-1.68, 0.24],
      [-1.9, 0.30, 0.08], [-2.0, 0.42]],
    gh: [-1.93, 0.95], cintura: [[-1.93, 1.06], [0.95, 0.975]],
    planta: [0.28, 0.18], rb: 0.06, rs: 0.06, ledge: 0.075, tumble: 0.32, rr: 0.09, crown: 0.03, bulge: 0.016,
    niv: { placaF: [0.40, 0.55], faro: [0.57, 0.65], placaT: [0.58, 0.73], stop: [0.79, 0.915] },
    parabrisas: [0.18, 0.92], luneta: [-1.90, -1.60],
    laterales: [[-1.32, 0.94]], pilares: [[-0.36, -0.27]],
    costuras: [0.88, -0.315, -1.08], manijas: [0.20, -0.76], manijaMat: 'negro',
    faroLat: 1.78, stopLat: -1.90,
    frente: { parrilla: 0.30, toma: 0.38, faroIn: 0.37 },
    atras: { stopIn: 0.42, vidrio: true, pilar: 0.12 },
    escape: [-1.95, 0.30, -0.45], llantas: ['acero', 'aleacion5', 'multi10', 'acero'],
  },
  suv: {
    L: 4.70, W: 1.85, r: 0.355, tw: 0.225, kr: 0.61, ejes: [1.40, -1.29], ra: 0.41,
    techo: [[2.35, 0.98], [2.25, 1.04, 0.08], [1.7, 1.10, 0.6], [1.06, 1.15, 0.05], [0.22, 1.665, 0.24],
      [-0.6, 1.70, 1.0], [-1.86, 1.685, 0.14], [-2.28, 1.23, 0.06], [-2.35, 1.17]],
    piso: [[2.35, 0.47], [2.2, 0.36, 0.08], [1.85, 0.32], [0.95, 0.29], [-0.84, 0.29], [-1.75, 0.33],
      [-2.15, 0.38, 0.1], [-2.35, 0.50]],
    gh: [-2.28, 1.06], cintura: [[-2.28, 1.23], [-1.9, 1.225], [1.06, 1.15]],
    planta: [0.32, 0.20], rb: 0.07, rs: 0.065, ledge: 0.08, tumble: 0.28, rr: 0.1, crown: 0.035, bulge: 0.02,
    niv: { placaF: [0.50, 0.65], faro: [0.79, 0.90], placaT: [0.70, 0.85], stop: [0.97, 1.09] },
    revest: 0.47,
    parabrisas: [0.27, 1.03], luneta: [-2.25, -1.93],
    laterales: [[-1.80, 1.05]], pilares: [[-0.18, -0.09], [-1.20, -1.12]],
    costuras: [1.02, -0.135, -1.10], manijas: [0.32, -0.75], manijaMat: 'negro',
    faroLat: 2.10, stopLat: -2.20,
    frente: { parrilla: 0.38, toma: 0.55, faroIn: 0.44 },
    atras: { stopIn: 0.50, vidrio: true, pilar: 0.12 },
    rieles: [-1.70, 0.20], escape: [-2.30, 0.36, -0.55], llantas: ['aleacion5', 'oscura6', 'multi10', 'aleacion5'],
  },
  pickup: {
    L: 5.30, W: 1.85, r: 0.385, tw: 0.265, kr: 0.56, ejes: [1.72, -1.365], ra: 0.445, cabina: -0.92,
    techo: [[2.65, 1.05], [2.56, 1.11, 0.07], [2.0, 1.165, 0.8], [1.40, 1.19, 0.05], [0.55, 1.765, 0.2],
      [-0.2, 1.79, 1.0], [-0.84, 1.775, 0.07], [-0.92, 1.72]],
    piso: [[2.65, 0.56], [2.5, 0.46, 0.08], [2.2, 0.44], [1.2, 0.46], [-0.92, 0.46]],
    gh: [-0.92, 1.40], cintura: [[-0.92, 1.22], [1.40, 1.19]],
    planta: [0.24, 0.05], rb: 0.07, rs: 0.07, ledge: 0.08, tumble: 0.26, rr: 0.1, crown: 0.03, bulge: 0.02,
    niv: { placaF: [0.58, 0.73], faro: [0.86, 0.965], stop: [0.84, 1.12] },
    revest: 0.52,
    parabrisas: [0.62, 1.37], luneta: null,
    laterales: [[-0.82, 1.38]], pilares: [[0.04, 0.14]],
    costuras: [1.24, 0.09, -0.86], manijas: [0.42, -0.52], manijaMat: 'cromo',
    faroLat: 2.42, stopLat: -99,
    frente: { parrilla: 0.52, toma: 0.55, faroIn: 0.56, alta: true, cromo: true },
    atras: { vidrio: true, pilar: 0.22, stopIn: 9 },
    caja: { x0: -2.57, x1: -0.96, yRiel: 1.20, yPiso: 0.87, t: 0.07, yb: 0.64, Rr: 0.04, Rf: 0.025 },
    llantas: ['oscura6', 'aleacion6', 'oscura6', 'aleacion6'],
  },
  van: {
    L: 5.30, W: 1.90, r: 0.335, tw: 0.195, kr: 0.57, ejes: [1.70, -1.41], ra: 0.39,
    techo: [[2.65, 1.03], [2.58, 1.09, 0.06], [2.10, 1.15, 0.05], [1.25, 1.95, 0.12], [0.95, 2.245, 0.25],
      [0.5, 2.275, 1.0], [-2.56, 2.27, 0.08], [-2.65, 2.19]],
    piso: [[2.65, 0.45], [2.52, 0.36, 0.08], [2.15, 0.31], [1.25, 0.29], [-0.98, 0.29], [-1.85, 0.32],
      [-2.40, 0.36, 0.08], [-2.65, 0.44]],
    gh: [-2.65, 2.10], cintura: [[-2.65, 1.18], [2.10, 1.15]], yVentana: 1.80,
    planta: [0.22, 0.12], rb: 0.06, rs: 0.06, ledge: 0.04, tumble: 0.10, rr: 0.12, crown: 0.025, bulge: 0.015,
    niv: { placaF: [0.46, 0.61], faro: [0.80, 0.95], placaT: [0.58, 0.73], stop: [0.76, 1.12], franja: [0.98, 1.07] },
    revest: 0.40,
    parabrisas: [1.30, 2.07], luneta: null,
    laterales: [[-2.52, 2.06]], pilares: [[1.02, 1.14], [-0.08, 0.0], [-1.26, -1.18]],
    costuras: [1.98, 1.08, 0.96, -0.04], manijas: [1.25, 0.10], manijaMat: 'negro',
    faroLat: 2.45, stopLat: -2.55,
    frente: { parrilla: 0.40, toma: 0.50, faroIn: 0.47 },
    atras: { stopIn: 0.68, vidrio: true, pilar: 0.12 },
    franja: true, llantas: ['acero', 'acero', 'aleacion5', 'acero'],
    paso: 0.45, nArco: 12,   // carrocería prismática: el tramo central no necesita secciones intermedias
  },
};

const _prep = new Map();
function prepAuto(tipo) {
  if (_prep.has(tipo)) return _prep.get(tipo);
  const c = Object.assign({}, AUTOS[tipo]);
  c.techoP = filete(c.techo, 3);
  c.pisoP = filete(c.piso, 2);
  c.YT = (x) => interp(c.techoP, x);
  c.YB = fondo(c.pisoP, c.ejes, c.r, c.ra);
  c.cinturaP = c.cintura.slice().sort((a, b) => a[0] - b[0]);
  c.BELT = (x) => interp(c.cinturaP, x);
  const s = new Set();
  for (const k in c.niv) { s.add(c.niv[k][0]); s.add(c.niv[k][1]); }
  c.siempre = new Set();
  if (c.revest) { s.add(c.revest); c.siempre.add(c.revest); }
  if (c.franja && c.niv.franja) c.niv.franja.forEach((l) => c.siempre.add(l));
  // niveles que necesita cada extremo (el resto se colapsa allí): adelante placa y faros, atrás placa y stops
  c.nivF = new Set([...c.siempre, ...(c.niv.placaF || []), ...(c.niv.faro || [])]);
  c.nivT = new Set([...c.siempre, ...(c.niv.placaT || []), ...(c.niv.stop || [])]);
  c.lista = [...s].sort((a, b) => a - b);
  const nL = c.lista.length;
  c.I = { BC: 0, B3: 3, S5: 4 + nL, S6: 5 + nL, S7: 6 + nL, L8: 7 + nL, W9: 8 + nL, R10: 9 + nL, R11: 10 + nL,
    R12: 11 + nL, C13: 12 + nL, C14: 13 + nL, H: 14 + nL };
  c.zr = c.W / 2 - 0.03 - c.tw / 2;
  // las luces que doblan la esquina deben caber bajo el hombro de la última sección (si no, nivelesEn las
  // recorta solo ahí y la franja queda escalonada)
  const x0 = c.cabina ?? -c.L / 2;
  if (c.YT(c.L / 2) - c.rs < c.niv.faro[1] + 0.01 - 1e-6) {
    console.warn(`vehiculos: ${tipo}: faro [${c.niv.faro}] sobre el hombro frontal ${(c.YT(c.L / 2) - c.rs).toFixed(3)}`);
  }
  if (c.stopLat > x0 && c.YT(x0) - c.rs < c.niv.stop[1] + 0.01 - 1e-6) {
    console.warn(`vehiculos: ${tipo}: stop [${c.niv.stop}] sobre el hombro posterior ${(c.YT(x0) - c.rs).toFixed(3)}`);
  }
  _prep.set(tipo, c);
  return c;
}

const clamp = THREE.MathUtils.clamp;
const en = (r, v) => !!r && v >= r[0] && v <= r[1];
const enL = (rs, v) => !!rs && rs.some((r) => en(r, v));

/**
 * Alturas de los niveles auxiliares de la sección en la estación x. Lejos de los extremos (donde no hay
 * faros, placas ni stops) los niveles se colapsan en un único punto medio (que conserva el abombado del
 * costado) y en los niveles "siempre activos" (revestimiento, franja); en cada extremo se conservan solo los
 * niveles de ese extremo. Los niveles colapsados generan caras degeneradas, que el loft descarta.
 * La asignación de cada nivel colapsado a su "ranura" se decide con valores nominales (sin recortar por el paso
 * de rueda; el punto medio se mide desde el zócalo base y0b), así es la misma en estaciones vecinas y las
 * franjas del loft no se retuercen sobre los arcos.
 */
function nivelesEn(c, x, y0, y1, y0b = y0) {
  const cl = (v) => clamp(v, y0, y1);
  const frente = x > c.faroLat - 0.25, atras = x < c.stopLat + 0.25;
  const keep = frente ? c.nivF : atras ? c.nivT : c.siempre;
  const K = [];   // [nominal, real]
  if (!frente && !atras) { const m = (y0b + y1) / 2; K.push([m, cl(m)]); }
  for (const l of c.lista) if (keep.has(l)) K.push([l, cl(l)]);
  if (!K.length) { const m = (y0b + y1) / 2; K.push([m, cl(m)]); }
  K.sort((a, b) => a[0] - b[0]);
  return c.lista.map((l) => {
    if (keep.has(l)) return cl(l);
    let r = K[0][1];
    for (const [nom, val] of K) if (nom <= l + 1e-9) r = val;
    return r;
  });
}

function anilloAuto(c, W) {
  return (e) => {
    const x = e.x;
    const yb = c.YB(x, e.lado), yt = c.YT(x), w = W(x);
    const enGh = x >= c.gh[0] - 1e-6 && x <= c.gh[1] + 1e-6;
    const ySh = enGh ? Math.min(c.BELT(x), yt) : yt;
    const g = yt - ySh;
    const alto = ySh - yb;
    const rb = Math.min(c.rb, alto * 0.3), rs = Math.min(c.rs, alto * 0.3);
    const y0 = yb + rb, y1 = ySh - rs;
    // El abombado del costado se mide desde el zócalo "sin pasos de rueda": sobre el arco la superficie es la
    // misma que en la puerta vecina, recortada por el arco (si no, el abombado se comprime y el panel mira al suelo).
    const y0b = Math.min(y0, interp(c.pisoP, x) + rb);
    const bz = (y) => w + c.bulge * Math.sin(Math.PI * clamp((y - y0b) / Math.max(1e-6, y1 - y0b), 0, 1));
    const z3 = bz(y0);
    const P = [[0, yb]];
    for (let i = 0; i <= 2; i++) {
      const a = -Math.PI / 2 + i * Math.PI / 4;
      P.push([z3 - rb + rb * Math.cos(a), yb + rb + rb * Math.sin(a)]);
    }
    for (const y of nivelesEn(c, x, y0, Math.max(y0, y1), y0b)) P.push([bz(y), y]);
    P.push([w, Math.max(y0, y1)]);
    for (let i = 1; i <= 2; i++) {
      const a = i * Math.PI / 4;
      P.push([w - rs + rs * Math.cos(a), Math.max(y0, y1) + rs * Math.sin(a)]);
    }
    const ledge = Math.max(c.ledge, rs);
    const wb = w - ledge;
    P.push([wb, ySh]);
    const rr = Math.min(c.rr, g * 0.45);
    const zAt = (y) => wb - c.tumble * (y - ySh);
    const yW = Math.max(ySh, Math.min(c.yVentana ?? 99, yt - rr));
    P.push([zAt(yW), yW]);
    const zR = zAt(yt - rr);
    P.push([zR, yt - rr]);
    P.push([zR - rr + rr * Math.cos(Math.PI / 4), yt - rr + rr * Math.sin(Math.PI / 4)]);
    P.push([zR - rr, yt]);
    P.push([(zR - rr) * 0.5, yt + c.crown * 0.75]);
    P.push([0, yt + c.crown]);
    return P;
  };
}

function clasifAuto(c) {
  const I = c.I, N = c.niv;
  return (k, q) => {
    if (k === 0) return 'negroMate';
    const costura = q.ancho < 0.02 && (c.costuras || []).some((s) => Math.abs(q.xm - s) < 0.008);
    if (k <= 2) return c.revest ? 'negro' : (costura ? 'negroMate' : 'pintura');
    if (k < I.S7) {
      if (costura) return 'negroMate';
      if (c.revest && q.yc < c.revest) return 'negro';
      if (en(N.faro, q.yc) && q.xm > c.faroLat) return 'faro';
      if (en(N.stop, q.yc) && q.xm < c.stopLat) return 'stop';
      if (c.franja && en(N.franja, q.yc) && q.xm < c.faroLat - 0.12 && q.xm > c.stopLat + 0.12) return 'franja';
      return 'pintura';
    }
    if (k === I.S7) return enL(c.laterales, q.xm) ? 'negro' : 'pintura';
    if (k === I.L8) return enL(c.pilares, q.xm) ? 'negro' : enL(c.laterales, q.xm) ? 'vidrio' : 'pintura';
    if (k < I.R12) return 'pintura';
    if (en(c.parabrisas, q.xm) || en(c.luneta, q.xm)) return 'vidrio';
    return 'pintura';
  };
}

function tapaFrente(c, wFin) {
  const N = c.niv, f = c.frente;
  const faro = { m: 'faro', uv: (z, y) => [clamp((Math.abs(z) - f.faroIn) / Math.max(0.05, wFin - f.faroIn), 0, 1),
    clamp((y - N.faro[0]) / (N.faro[1] - N.faro[0]), 0, 1)] };
  const uv = (z, y) => [0.5 - z / 0.31, (y - N.placaF[0]) / (N.placaF[1] - N.placaF[0])];
  const parr = { m: f.cromo ? 'parrillaCromo' : 'parrilla', uv: (z, y) => [z * 2.5, y * 5.2] };
  const cols = [...new Set([0.155, f.parrilla, f.toma, f.faroIn])].sort((a, b) => a - b);
  return {
    cols,
    fn: (yc, zc, zE, h) => {
      if (h < 3) return 'negro';
      if (c.revest && yc < c.revest - 0.04) return 'negro';
      if (en(N.placaF, yc)) {
        if (zc < 0.155) return { m: 'placa', uv };
        return zc < f.toma ? 'negro' : 'pintura';
      }
      if (en(N.faro, yc)) {
        if (zc < f.parrilla) return parr;
        return zc > f.faroIn ? faro : 'pintura';
      }
      if (f.alta && yc > N.placaF[1] && yc < N.faro[0] && zc < f.parrilla) return parr;
      return 'pintura';
    },
  };
}

function tapaAtras(c, wFin) {
  const N = c.niv, t = c.atras, I = c.I;
  const uv = N.placaT ? (z, y) => [0.5 + z / 0.31, (y - N.placaT[0]) / (N.placaT[1] - N.placaT[0])] : null;
  const cols = [0.155];
  if (t.stopIn < wFin) cols.push(t.stopIn);
  if (t.vidrio) cols.push(Math.max(0.2, wFin - t.pilar - c.ledge - 0.05));
  cols.sort((a, b) => a - b);
  return {
    cols,
    fn: (yc, zc, zE, h) => {
      if (h < 3) return 'negro';
      if (t.vidrio && h === I.L8 && zc < zE - t.pilar) return 'vidrio';
      if (c.revest && yc < c.revest - 0.04) return 'negro';
      if (N.placaT && en(N.placaT, yc) && zc < 0.155) return { m: 'placa', uv };
      if (en(N.stop, yc) && zc > t.stopIn) return 'stop';
      return 'pintura';
    },
  };
}

/** z de la superficie lateral a la altura y (para apoyar manijas, molduras) */
function zLado(anillo, c, x, y) {
  const P = anillo({ x, lado: 0 });
  for (let i = 3; i < c.I.S7; i++) {
    const [za, ya] = P[i], [zb, yb] = P[i + 1];
    if (y >= ya && y <= yb && yb - ya > 1e-6) return za + (zb - za) * (y - ya) / (yb - ya);
  }
  return P[c.I.S5][0];
}

function construirAuto(tipo, v) {
  const c = prepAuto(tipo);
  const M = new Malla();
  const L2 = c.L / 2;
  const x0 = c.cabina ?? -L2;
  const W = planta(c.W / 2, x0, L2, c.planta[1], c.planta[0]);
  const fijos = [c.faroLat, c.stopLat, c.gh[0], c.gh[1]];
  for (const r of [c.parabrisas, c.luneta, ...(c.laterales || []), ...(c.pilares || [])]) if (r) fijos.push(r[0], r[1]);
  const ests = estaciones({ x0, x1: L2, Rf: c.planta[0], Rr: c.planta[1], perfiles: [c.techoP, c.pisoP],
    ejes: c.ejes, ra: c.ra, fijos, costuras: c.costuras, paso: c.paso ?? 0.28, nArco: c.nArco ?? 14 });
  const anillo = anilloAuto(c, W);
  // aristas vivas: pie de las ventanas (L8) y arranque del costado sobre el redondeo inferior (3), para que el
  // panel no promedie normales con el zócalo, que sobre los pasos de rueda mira hacia abajo
  const duros = []; duros[c.I.L8] = true; duros[c.I.B3] = true;
  loft(M, ests, anillo, duros, clasifAuto(c), { frente: tapaFrente(c, W(L2)), atras: tapaAtras(c, W(x0)) });

  // ---- chasis / pasos de rueda (bloque oscuro entre ruedas)
  const zi = c.zr - c.tw / 2 - 0.03;
  const xa0 = Math.min(...c.ejes) - c.ra * 0.85, xa1 = Math.max(...c.ejes) + c.ra * 0.85;
  const ySill = c.YB(0) - 0.05, yTop = c.r + c.ra - 0.05;
  M.caja('negroMate', xa1 - xa0, yTop - ySill, 2 * zi, mtx((xa0 + xa1) / 2, (yTop + ySill) / 2, 0));

  // ---- espejos retrovisores
  const xm = c.gh[1] - 0.14;
  const yE = c.BELT(xm), wE = W(xm) - c.ledge;
  const esc = tipo === 'van' || tipo === 'pickup' ? 1.2 : 1;
  for (const s of [1, -1]) {
    const Mh = mtx(xm - 0.03, yE + 0.09 * esc, s * (wE + 0.15 * esc), 0, s * 0.12, 0, esc, esc, esc);
    M.caja('pintura', 0.10, 0.11, 0.17, Mh, 0.035);
    M.caja('cromo', 0.006, 0.084, 0.135, Mh.clone().multiply(mtx(-0.051, 0, 0)));
    M.caja('negro', 0.08, 0.035, 0.11, mtx(xm, yE + 0.045 * esc, s * (wE + 0.06 * esc)));
  }
  // ---- limpiaparabrisas (apoyados al pie del parabrisas)
  {
    const xw = c.gh[1] - 0.07, yw = c.YT(xw) + 0.012;
    const ang = Math.atan2(c.YT(c.gh[1]) - c.YT(c.gh[1] - 0.2), 0.2);
    for (const [z0, z1] of [[-0.58, -0.04], [0.02, 0.5]]) {
      M.caja('negro', 0.014, 0.012, z1 - z0, mtx(xw, yw, (z0 + z1) / 2, 0.06, 0, ang));
    }
  }
  // ---- manijas
  for (const xh of c.manijas || []) {
    const yh = c.BELT(xh) - 0.075;
    const zh = zLado(anillo, c, xh, yh);
    for (const s of [1, -1]) M.caja(c.manijaMat, 0.15, 0.028, 0.03, mtx(xh, yh, s * (zh + 0.004)), 0.012);
  }
  // ---- tubo de escape
  if (c.escape) {
    // la punta asoma como máximo 2.5 cm por detrás del contorno inferior del parachoques a la altura del eje
    // del tubo (punto más atrasado donde el piso de la carrocería queda por debajo de esa altura)
    let [ex, ey, ez] = c.escape;
    let xc = 0;
    for (let x = x0; x < 0; x += 0.0025) if (interp(c.pisoP, x) <= ey) { xc = x; break; }
    ex = Math.max(ex, xc - 0.025);
    M.tubo('cromo', [ex + 0.2, ey, ez], [ex, ey, ez], 0.032, 10);
    M.tubo('negroMate', [ex + 0.01, ey, ez], [ex - 0.003, ey, ez], 0.024, 10, false);
  }
  // ---- rieles de techo (SUV)
  if (c.rieles && v.rieles) {
    const [r0, r1] = c.rieles;
    let ymax = 0;
    for (let x = r0; x <= r1; x += 0.1) ymax = Math.max(ymax, c.YT(x));
    const zr = W((r0 + r1) / 2) - c.ledge - c.tumble * (c.YT(-0.6) - c.BELT(-0.6)) - c.rr - 0.06;
    for (const s of [1, -1]) {
      M.caja('negro', r1 - r0, 0.028, 0.045, mtx((r0 + r1) / 2, ymax + 0.027, s * zr), 0.012);
      for (const xp of [r0 + 0.05, r1 - 0.05]) M.caja('negro', 0.12, 0.05, 0.05, mtx(xp, c.YT(xp) + 0.012, s * zr), 0.015);
    }
  }
  // ---- específicos
  if (tipo === 'pickup') cajaPickup(M, c, v);
  if (tipo === 'pickup' || tipo === 'suv') {
    // estribos laterales
    const ex0 = Math.min(...c.ejes) + c.ra + 0.06, ex1 = Math.max(...c.ejes) - c.ra - 0.06;
    for (const s of [1, -1]) {
      M.caja('negro', ex1 - ex0, 0.04, 0.13, mtx((ex0 + ex1) / 2, c.YB(0) - 0.07, s * (c.W / 2 - 0.07)), 0.015);
      for (const xp of [ex0 + 0.25, ex1 - 0.25]) M.caja('negroMate', 0.05, 0.08, 0.1, mtx(xp, c.YB(0) - 0.02, s * (c.W / 2 - 0.16)));
    }
  }
  if (tipo === 'van') {
    // parachoques y peldaño posterior, riel de puerta corrediza
    M.caja('negro', 0.16, 0.16, 1.80, mtx(-L2 + 0.075, 0.45, 0), 0.03);
    M.caja('negro', 0.12, 0.13, 1.76, mtx(L2 - 0.045, 0.40, 0), 0.03);
    for (const s of [1, -1]) M.caja('negro', 1.15, 0.025, 0.02, mtx(-0.62, 1.2, s * (W(-0.62) - c.ledge + 0.002)));
  }
  return M.construir();
}

/** tolva abierta de la pickup: paredes en U con paso de rueda, compuerta, parachoques, luces */
function cajaPickup(M, c, v) {
  const k = c.caja;
  const W = planta(c.W / 2, k.x0, k.x1, k.Rr, k.Rf);
  const YB = fondo([[k.x0, k.yb], [k.x1, k.yb]], c.ejes, c.r, c.ra);
  const cruces = [];
  for (const xa of c.ejes) {
    const dy = k.yb - c.r;
    if (dy < c.ra) { const dx = Math.sqrt(c.ra * c.ra - dy * dy); cruces.push(xa - dx, xa + dx); }
  }
  const ests = estaciones({ x0: k.x0, x1: k.x1, Rf: k.Rf, Rr: k.Rr, ejes: c.ejes, ra: c.ra, fijos: cruces, paso: 0.28,
    nArco: 14 });
  const nL = c.lista.length;
  const J = { S7: 6 + nL, L8: 7 + nL, I1: 8 + nL };
  const anillo = (e) => {
    const x = e.x, yb = YB(x, e.lado), w = W(x), yR = k.yRiel, yF = k.yPiso, t = k.t;
    const alto = yR - yb, rb = Math.min(c.rb, alto * 0.3), rs = Math.min(0.03, alto * 0.3);
    const y0 = yb + rb, y1 = yR - rs;
    const y0b = Math.min(y0, k.yb + rb);   // abombado medido desde el zócalo sin paso de rueda (ver anilloAuto)
    const bz = (y) => w + c.bulge * Math.sin(Math.PI * clamp((y - y0b) / Math.max(1e-6, y1 - y0b), 0, 1));
    const z3 = bz(y0);
    const P = [[0, yb]];
    for (let i = 0; i <= 2; i++) {
      const a = -Math.PI / 2 + i * Math.PI / 4;
      P.push([z3 - rb + rb * Math.cos(a), yb + rb + rb * Math.sin(a)]);
    }
    for (const y of nivelesEn(c, x, y0, y1, y0b)) P.push([bz(y), y]);
    P.push([w, y1]);
    for (let i = 1; i <= 2; i++) { const a = i * Math.PI / 4; P.push([w - rs + rs * Math.cos(a), y1 + rs * Math.sin(a)]); }
    P.push([w - t, yR]);
    P.push([w - t, yF + 0.03]);
    P.push([w - t - 0.03, yF]);
    P.push([(w - t - 0.03) * 0.5, yF]);
    P.push([0, yF]);
    return P;
  };
  const duros = []; duros[3] = true; duros[J.L8] = true; duros[J.I1] = true;
  const clasif = (kk, q) => {
    if (kk === 0) return 'negroMate';
    if (kk <= 2) return 'negro';
    if (kk < J.S7) return (c.revest && q.yc < c.revest) ? 'negro' : 'pintura';
    if (kk === J.S7) return 'negro';
    return 'negroMate';
  };
  loft(M, ests, anillo, duros, clasif, { frente: { earcut: 'pintura' }, atras: { earcut: 'pintura' } });

  const wF = W(k.x0), wi = wF - k.t;
  // pared frontal interior de la tolva y cajones de rueda
  M.caja('negroMate', 0.04, k.yRiel - k.yPiso - 0.01, 2 * (W(k.x1) - k.t), mtx(k.x1 - 0.02, (k.yRiel + k.yPiso) / 2, 0));
  for (const s of [1, -1]) {
    M.caja('negroMate', 0.84, 0.2, 0.2, mtx(c.ejes[1], k.yPiso + 0.08, s * (W(c.ejes[1]) - k.t - 0.1)), 0.06);
  }
  // compuerta
  const yc0 = k.yPiso - 0.1, yc1 = k.yRiel - 0.012;
  M.caja('pintura', 0.05, yc1 - yc0, 2 * wi - 0.006, mtx(k.x0 + 0.021, (yc0 + yc1) / 2, 0), 0.012);
  M.caja('negro', 0.02, 0.05, 0.22, mtx(k.x0 - 0.006, yc1 - 0.07, 0), 0.01);
  // luces posteriores verticales en las esquinas
  for (const s of [1, -1]) {
    M.caja('stop', 0.10, 0.30, 0.13, mtx(k.x0 + 0.045, 0.99, s * (wF - 0.045)), 0.02);
    M.caja('faro', 0.012, 0.06, 0.09, mtx(k.x0 - 0.006, 0.90, s * (wF - 0.05)));
  }
  // parachoques posterior con peldaño y placa
  const xb = -c.L / 2;
  M.caja('cromo', 0.17, 0.18, 1.78, mtx(xb + 0.085, 0.585, 0), 0.04);
  M.caja('negro', 0.12, 0.012, 0.6, mtx(xb + 0.09, 0.678, 0));
  const placa = geoUnidad('placaG', () => new THREE.PlaneGeometry(0.30, 0.15).rotateY(-Math.PI / 2));
  M.geo('placa', placa, mtx(xb - 0.002, 0.585, 0));
  M.caja('negroMate', 0.16, 0.06, 1.2, mtx(xb + 0.24, 0.50, 0));
  // escape bajo la tolva (lado derecho)
  M.tubo('cromo', [-2.25, 0.47, -0.62], [-2.42, 0.47, -0.62], 0.032, 10);
  M.tubo('negroMate', [-2.415, 0.47, -0.62], [-2.425, 0.47, -0.62], 0.024, 10, false);
  // barra antivuelco
  if (v.antivuelco) {
    const xr = k.x1 - 0.14, mat = 'cromo', yT = 1.78;
    for (const s of [1, -1]) {
      const z = s * (W(xr) - k.t / 2);
      M.tubos(mat, [[xr, k.yRiel, z], [xr, yT - 0.08, z * 0.98], [xr - 0.03, yT, z * 0.9]], 0.03, 10);
      M.tubo(mat, [xr, yT - 0.12, z * 0.97], [xr - 0.42, k.yRiel, z], 0.025, 8);
    }
    M.tubo(mat, [xr - 0.03, yT, 0.83], [xr - 0.03, yT, -0.83], 0.03, 10);
  }
}

function crearAuto(tipo, color, v) {
  const c = prepAuto(tipo);
  const clave = `${tipo}|${v.rieles ? 1 : 0}|${v.antivuelco ? 1 : 0}`;
  let cuerpo = _geoCache.get(clave);
  if (!cuerpo) { cuerpo = construirAuto(tipo, v); _geoCache.set(clave, cuerpo); }
  const g = new THREE.Group();
  const malla = new THREE.Mesh(cuerpo.geo, cuerpo.claves.map((k) => resolverMat(k, color, v)));
  malla.castShadow = true;
  malla.receiveShadow = true;
  g.add(malla);
  const geoR = geoRueda(c.r, c.tw, c.kr, { seg: 24 });
  const matR = matAro(v.llanta || c.llantas[0]);
  const ruedas = [];
  for (const xa of c.ejes) {
    for (const s of [1, -1]) {
      const w = rueda(geoR, matR, xa, c.r, s * c.zr, s);
      g.add(w);
      ruedas.push(w);
    }
  }
  if (v.sombra) {
    const L2 = c.L / 2, W2 = c.W / 2;
    const manchas = [];
    for (const xa of c.ejes) for (const s of [1, -1]) manchas.push([xa, s * c.zr, c.r * 0.55, c.tw * 0.62, 0.55]);
    g.add(sombraContacto(tipo, c.L + 0.5, c.W + 0.4, [[-L2 + 0.06, L2 - 0.06, -W2 + 0.05, W2 - 0.05, 0.42]], manchas));
  }
  g.userData.ruedas = ruedas;
  return g;
}

// ===================================================================== moto lineal (150 cc)
function cuerpoMoto(M) {
  const P = 'pintura';
  const F = [0.66, 0.295];
  const rake = 25 * Math.PI / 180, u = [-Math.sin(rake), Math.cos(rake)];
  const fk = (t) => [F[0] + u[0] * t, F[1] + u[1] * t];
  // horquilla
  for (const z of [0.075, -0.075]) {
    M.tubo('negro', [...fk(-0.02), z], [...fk(0.30), z], 0.024, 7, false);
    M.tubo('cromo', [...fk(0.30), z], [...fk(0.63), z], 0.018, 7, false);
  }
  for (const t of [0.50, 0.64]) M.caja('negro', 0.07, 0.03, 0.2, mtx(...fk(t), 0, 0, 0, rake), 0.012);
  M.tubo('negro', [...fk(0.46), 0], [...fk(0.68), 0], 0.032, 7, false);
  // guardabarro delantero
  {
    const s = new THREE.Shape();
    const ro = 0.345, ri = 0.33, a0 = 0.35, a1 = 2.35;
    s.absarc(0, 0, ro, a0, a1, false);
    s.absarc(0, 0, ri, a1, a0, true);
    M.extruir(P, s, 0.1, 0, mtx(F[0], F[1], 0), 8);
  }
  // faro, carenado y tablero
  M.caja('negro', 0.13, 0.15, 0.19, mtx(0.48, 0.84, 0, 0, 0, -0.25), 0.04);
  M.caja('faro', 0.03, 0.115, 0.15, mtx(0.545, 0.845, 0, 0, 0, -0.25), 0.012);
  M.caja(P, 0.16, 0.05, 0.2, mtx(0.46, 0.93, 0, 0, 0, -0.35), 0.02);
  M.caja('negro', 0.08, 0.045, 0.13, mtx(0.36, 1.0, 0, 0, 0, 0.3), 0.012);
  for (const s of [1, -1]) M.caja('ambar', 0.05, 0.03, 0.03, mtx(0.48, 0.79, s * 0.13));
  // manubrio, puños, espejos
  M.tubo('negro', [0.33, 0.975, 0.13], [0.33, 0.975, -0.13], 0.012, 6, false);
  for (const s of [1, -1]) {
    M.tubo('negro', [0.33, 0.975, s * 0.13], [0.29, 0.99, s * 0.30], 0.012, 6, false);
    M.tubo('cuero', [0.29, 0.99, s * 0.28], [0.283, 0.993, s * 0.375], 0.018, 7);
    M.caja('negro', 0.05, 0.012, 0.13, mtx(0.32, 0.99, s * 0.30, 0, s * 0.25, 0));
    M.tubo('negro', [0.31, 0.985, s * 0.24], [0.285, 1.05, s * 0.27], 0.006, 4, false);
    M.caja('negro', 0.03, 0.055, 0.1, mtx(0.28, 1.06, s * 0.29), 0.012);
    M.caja('cromo', 0.004, 0.045, 0.085, mtx(0.264, 1.06, s * 0.29));
  }
  // chasis
  M.tubos('negro', [[0.40, 0.84, 0], [0.22, 0.32, 0], [-0.10, 0.27, 0], [-0.18, 0.78, 0]], 0.022, 6);
  M.tubo('negro', [0.40, 0.90, 0], [-0.20, 0.80, 0], 0.026, 6, false);
  for (const s of [1, -1]) M.tubo('negro', [-0.18, 0.78, s * 0.07], [-0.80, 0.84, s * 0.07], 0.016, 5, false);
  // motor
  M.caja('motor', 0.40, 0.22, 0.24, mtx(0.03, 0.38, 0), 0.05);
  M.caja('motor', 0.14, 0.21, 0.16, mtx(0.17, 0.56, 0, 0, 0, -0.35), 0.03);
  for (let i = 0; i < 4; i++) M.caja('motor', 0.18, 0.012, 0.2, mtx(0.15 + 0.035 * i * 0.94, 0.5 + 0.035 * i, 0, 0, 0, -0.35));
  M.caja('negro', 0.13, 0.05, 0.17, mtx(0.225, 0.66, 0, 0, 0, -0.35), 0.015);
  M.tubo('aluminio', [0.03, 0.40, 0.12], [0.03, 0.40, 0.15], 0.09, 10);
  M.tubo('negro', [-0.04, 0.40, -0.12], [-0.04, 0.40, -0.15], 0.075, 8);
  // escape (lado derecho, +z)
  M.tubos('cromo', [[0.23, 0.62, 0.05], [0.29, 0.42, 0.08], [0.18, 0.23, 0.12], [-0.20, 0.26, 0.15]], 0.02, 6);
  M.tubo('negro', [-0.18, 0.29, 0.17], [-0.78, 0.48, 0.17], 0.055, 9, false);
  M.tubo('cromo', [-0.79, 0.483, 0.17], [-0.84, 0.5, 0.17], 0.035, 8);
  // basculante, amortiguadores, cubrecadena
  for (const s of [1, -1]) {
    M.tubo('negro', [-0.14, 0.40, s * 0.095], [-0.66, 0.295, s * 0.095], 0.022, 6, false);
    M.tubo('cromo', [-0.56, 0.34, s * 0.115], [-0.44, 0.80, s * 0.115], 0.012, 5, false);
    M.tubo('negro', [-0.535, 0.43, s * 0.115], [-0.46, 0.72, s * 0.115], 0.028, 7, false);
  }
  M.caja('negro', 0.52, 0.05, 0.015, mtx(-0.38, 0.40, -0.125, 0, 0, 0.14));
  // tanque
  {
    const s = new THREE.Shape();
    s.moveTo(0.32, 0.84); s.lineTo(0.35, 0.92);
    s.quadraticCurveTo(0.29, 1.0, 0.15, 1.0);
    s.quadraticCurveTo(-0.02, 0.995, -0.09, 0.92);
    s.lineTo(-0.11, 0.84);
    s.quadraticCurveTo(0.10, 0.80, 0.32, 0.84);
    M.extruir(P, s, 0.2, 0.04, null, 5);
    M.tubo('aluminio', [0.12, 1.0, 0], [0.12, 1.025, 0], 0.03, 8);
  }
  // asiento
  {
    const s = new THREE.Shape();
    s.moveTo(-0.10, 0.855);
    s.quadraticCurveTo(-0.16, 0.885, -0.30, 0.875);
    s.lineTo(-0.56, 0.885);
    s.quadraticCurveTo(-0.70, 0.895, -0.72, 0.87);
    s.lineTo(-0.70, 0.83); s.lineTo(-0.10, 0.82);
    s.closePath();
    M.extruir('cuero', s, 0.17, 0.035, null, 4, 2);
  }
  // colín / tapas laterales
  {
    const s = new THREE.Shape();
    s.moveTo(-0.12, 0.83); s.lineTo(-0.70, 0.84); s.lineTo(-0.89, 0.875); s.lineTo(-0.91, 0.84);
    s.quadraticCurveTo(-0.70, 0.74, -0.42, 0.70);
    s.lineTo(-0.16, 0.62);
    s.closePath();
    M.extruir(P, s, 0.15, 0.03, null, 4, 1);
  }
  // luz posterior, porta placa y placa, direccionales
  M.caja('stop', 0.04, 0.05, 0.1, mtx(-0.925, 0.855, 0), 0.012);
  M.caja('negro', 0.025, 0.30, 0.06, mtx(-0.93, 0.68, 0, 0, 0, -0.35));
  const placa = geoUnidad('placaMoto', () => new THREE.PlaneGeometry(0.2, 0.13).rotateY(-Math.PI / 2));
  M.caja('negro', 0.012, 0.15, 0.22, mtx(-0.978, 0.585, 0, 0, 0, -0.2));
  M.geo('placa', placa, mtx(-0.986, 0.585, 0, 0, 0, -0.2));
  for (const s of [1, -1]) M.caja('ambar', 0.05, 0.03, 0.03, mtx(-0.89, 0.79, s * 0.11));
  // pedales / reposapiés
  for (const s of [1, -1]) {
    M.tubo('negro', [-0.02, 0.33, s * 0.1], [-0.02, 0.33, s * 0.2], 0.012, 5);
    M.tubo('negro', [-0.40, 0.42, s * 0.1], [-0.40, 0.42, s * 0.19], 0.011, 5);
  }
}

function crearMoto(color, v) {
  const clave = 'moto';
  let cuerpo = _geoCache.get(clave);
  if (!cuerpo) {
    const M = new Malla();
    cuerpoMoto(M);
    // pata lateral (izquierda, -z): pie en el suelo con la moto inclinada
    const incl = -0.13;
    const pie = new THREE.Vector3(-0.2, 0.013, -0.3).applyAxisAngle(new THREE.Vector3(1, 0, 0), -incl);
    M.tubo('negro', [-0.05, 0.30, -0.1], [pie.x, pie.y, pie.z], 0.012, 5);
    cuerpo = M.construir();
    cuerpo.incl = incl;
    _geoCache.set(clave, cuerpo);
  }
  const g = new THREE.Group();
  const inclinada = new THREE.Group();
  inclinada.rotation.x = cuerpo.incl;
  g.add(inclinada);
  const malla = new THREE.Mesh(cuerpo.geo, cuerpo.claves.map((k) => resolverMat(k, color, v)));
  malla.castShadow = true;
  malla.receiveShadow = true;
  inclinada.add(malla);
  const mat = matAro('moto');
  const rd = rueda(geoRueda(0.295, 0.09, 0.72, { seg: 16, dosCaras: true }), mat, 0.66, 0.295, 0, 1);
  const rt = rueda(geoRueda(0.30, 0.11, 0.70, { seg: 16, dosCaras: true }), mat, -0.66, 0.30, 0, 1);
  inclinada.add(rd, rt);
  if (cuerpo.alza === undefined) {
    // la inclinación hunde levemente el borde del neumático: se levanta el conjunto lo justo
    inclinada.updateMatrixWorld(true);
    const caja = new THREE.Box3();
    for (const w of [rd, rt]) caja.union(new THREE.Box3().setFromObject(w, true));
    cuerpo.alza = -caja.min.y;
  }
  inclinada.position.y = cuerpo.alza;
  if (v.sombra) {
    g.add(sombraContacto('moto', 2.5, 0.9, [[-0.92, 0.74, -0.16, 0.12, 0.34]],
      [[0.66, 0.0, 0.17, 0.065, 0.55], [-0.66, 0.0, 0.17, 0.075, 0.55]]));
  }
  g.userData.ruedas = [rd, rt];
  return g;
}

// ===================================================================== mototaxi peruano
function cuerpoMototaxi(M) {
  const P = 'pintura';
  // ---------------- parte delantera (moto)
  const F = [1.08, 0.27];
  const rake = 24 * Math.PI / 180, u = [-Math.sin(rake), Math.cos(rake)];
  const fk = (t) => [F[0] + u[0] * t, F[1] + u[1] * t];
  for (const z of [0.075, -0.075]) {
    M.tubo('negro', [...fk(-0.02), z], [...fk(0.30), z], 0.024, 7, false);
    M.tubo('cromo', [...fk(0.30), z], [...fk(0.66), z], 0.018, 7, false);
  }
  for (const t of [0.52, 0.66]) M.caja('negro', 0.07, 0.03, 0.2, mtx(...fk(t), 0, 0, 0, rake), 0.012);
  {
    const s = new THREE.Shape();
    s.absarc(0, 0, 0.32, 0.3, 2.4, false);
    s.absarc(0, 0, 0.305, 2.4, 0.3, true);
    M.extruir(P, s, 0.11, 0, mtx(F[0], F[1], 0), 8);
  }
  // faro en carenado
  M.caja(P, 0.15, 0.17, 0.24, mtx(0.86, 0.90, 0, 0, 0, -0.3), 0.05);
  M.caja('faro', 0.03, 0.12, 0.17, mtx(0.935, 0.89, 0, 0, 0, -0.3), 0.015);
  for (const s of [1, -1]) M.caja('ambar', 0.05, 0.03, 0.035, mtx(0.88, 0.83, s * 0.15));
  // manubrio y espejos
  M.tubo('negro', [0.76, 1.0, 0.13], [0.76, 1.0, -0.13], 0.012, 6, false);
  for (const s of [1, -1]) {
    M.tubo('negro', [0.76, 1.0, s * 0.13], [0.72, 1.015, s * 0.30], 0.012, 6, false);
    M.tubo('cuero', [0.72, 1.015, s * 0.27], [0.713, 1.018, s * 0.36], 0.018, 7);
    M.tubo('negro', [0.74, 1.01, s * 0.24], [0.72, 1.13, s * 0.28], 0.006, 4, false);
    M.caja('negro', 0.03, 0.06, 0.11, mtx(0.715, 1.14, s * 0.30));
    M.caja('cromo', 0.004, 0.048, 0.09, mtx(0.698, 1.14, s * 0.30));
  }
  // tanque, asiento del conductor, motor
  {
    const s = new THREE.Shape();
    s.moveTo(0.82, 0.80); s.lineTo(0.84, 0.86);
    s.quadraticCurveTo(0.78, 0.93, 0.66, 0.93);
    s.quadraticCurveTo(0.52, 0.925, 0.48, 0.86);
    s.lineTo(0.47, 0.79);
    s.quadraticCurveTo(0.65, 0.76, 0.82, 0.80);
    M.extruir(P, s, 0.2, 0.035, null, 4);
  }
  {
    const s = new THREE.Shape();
    s.moveTo(0.50, 0.80); s.quadraticCurveTo(0.45, 0.825, 0.36, 0.82);
    s.lineTo(0.20, 0.83); s.lineTo(0.18, 0.77); s.lineTo(0.50, 0.76); s.closePath();
    M.extruir('cuero', s, 0.2, 0.03, null, 3, 1);
  }
  M.caja(P, 0.34, 0.16, 0.22, mtx(0.34, 0.68, 0), 0.03);
  M.tubos('negro', [[0.84, 0.86, 0], [0.66, 0.36, 0], [0.18, 0.34, 0]], 0.022, 6);
  M.tubo('negro', [0.84, 0.90, 0], [0.42, 0.76, 0], 0.026, 6, false);
  M.caja('motor', 0.36, 0.2, 0.24, mtx(0.46, 0.38, 0), 0.05);
  M.caja('motor', 0.13, 0.2, 0.15, mtx(0.62, 0.53, 0, 0, 0, -0.5), 0.03);
  M.tubo('aluminio', [0.46, 0.39, 0.12], [0.46, 0.39, 0.15], 0.08, 8);
  // escape (derecha) bajo la cabina
  M.tubos('cromo', [[0.66, 0.56, 0.05], [0.72, 0.38, 0.09], [0.55, 0.22, 0.16], [0.18, 0.22, 0.28]], 0.02, 6);
  M.tubo('negro', [0.18, 0.22, 0.30], [-0.28, 0.22, 0.30], 0.045, 8);
  // reposapiés del conductor
  for (const s of [1, -1]) M.tubo('negro', [0.50, 0.30, s * 0.12], [0.50, 0.30, s * 0.24], 0.014, 5);

  // ---------------- cabina posterior
  const zc = 0.645;
  M.caja('negro', 1.56, 0.06, 1.24, mtx(-0.60, 0.33, 0));                       // piso
  for (const s of [1, -1]) {
    // costado inferior con paso de rueda
    const sh = new THREE.Shape();
    sh.moveTo(-1.37, 0.33); sh.lineTo(-0.96, 0.33);
    sh.absarc(-0.62, 0.26, 0.34, Math.PI - 0.21, 0.21, true);
    sh.lineTo(-0.22, 0.33); sh.lineTo(0.16, 0.33); sh.lineTo(0.16, 0.47);
    sh.quadraticCurveTo(-0.22, 0.47, -0.28, 0.62);
    sh.lineTo(-0.31, 0.86); sh.lineTo(-1.37, 0.86); sh.closePath();
    M.extruir(P, sh, 0.024, 0.01, mtx(0, 0, s * zc), 6, 1);
    // franja decorativa
    // (la cara exterior del costado extruido queda en zc + 0.022: la franja va por fuera)
    M.caja('franja', 1.0, 0.035, 0.006, mtx(-0.82, 0.76, s * (zc + 0.026)));
  }
  M.caja(P, 0.04, 0.62, 1.32, mtx(-1.38, 0.64, 0), 0.015);                      // panel posterior
  M.caja(P, 0.04, 0.14, 1.26, mtx(0.15, 0.40, 0), 0.01);                        // zócalo frontal
  for (const s of [1, -1]) {
    M.caja('stop', 0.02, 0.09, 0.15, mtx(-1.405, 0.84, s * 0.53), 0.008);
    M.caja('ambar', 0.02, 0.05, 0.08, mtx(-1.405, 0.74, s * 0.55));
  }
  const placa = geoUnidad('placaMoto', () => new THREE.PlaneGeometry(0.2, 0.13).rotateY(-Math.PI / 2));
  M.geo('placa', placa, mtx(-1.403, 0.56, 0));
  M.tubo('cromo', [-1.418, 0.42, 0.6], [-1.418, 0.42, -0.6], 0.018, 6);          // defensa
  // guardafangos de jebe detrás de las ruedas traseras, colgando del piso de la cabina
  for (const s of [1, -1]) M.caja('negroMate', 0.008, 0.18, 0.15, mtx(-0.93, 0.21, s * 0.52));
  // asiento de pasajeros
  M.caja('negro', 0.40, 0.2, 1.1, mtx(-1.03, 0.45, 0));
  M.caja('cuero', 0.44, 0.1, 1.18, mtx(-1.03, 0.6, 0), 0.04);
  M.caja('cuero', 0.1, 0.44, 1.18, mtx(-1.27, 0.86, 0, 0, 0, 0.12), 0.04);
  // parantes del techo
  for (const s of [1, -1]) {
    M.tubo('negro', [-1.37, 0.86, s * 0.63], [-1.37, 1.68, s * 0.63], 0.02, 6, false);
    M.tubo('negro', [-0.31, 0.86, s * 0.63], [-0.31, 1.68, s * 0.63], 0.02, 6, false);
    M.tubo('negro', [0.15, 0.47, s * 0.62], [0.15, 1.68, s * 0.62], 0.02, 6, false);
  }
  // lona posterior con ventana de mica y costados superiores con cortina enrollada
  M.caja('lona', 0.025, 0.74, 1.30, mtx(-1.385, 1.31, 0));
  M.caja('mica', 0.006, 0.3, 0.8, mtx(-1.40, 1.34, 0));
  for (const s of [1, -1]) {
    M.caja('lona', 1.06, 0.25, 0.012, mtx(-0.84, 1.555, s * 0.655));
    M.tubo('lona', [-1.36, 1.41, s * 0.655], [-0.33, 1.41, s * 0.655], 0.035, 7);
  }
  // techo de lona (cubre también al conductor) con faldón pintado
  M.caja('lona', 2.24, 0.07, 1.34, mtx(-0.28, 1.715, 0), 0.03);
  for (const s of [1, -1]) M.caja(P, 2.22, 0.05, 0.02, mtx(-0.28, 1.665, s * 0.665));
  M.caja(P, 0.02, 0.05, 1.32, mtx(0.83, 1.665, 0));
  M.caja(P, 0.02, 0.05, 1.32, mtx(-1.39, 1.665, 0));
  // parabrisas delantero con marco y tirantes al manubrio
  {
    const a = [0.80, 1.64], b = [0.88, 1.17];
    const ang = Math.atan2(b[0] - a[0], a[1] - b[1]);
    const len = Math.hypot(b[0] - a[0], a[1] - b[1]);
    M.caja('mica', 0.008, len, 1.04, mtx((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, 0, 0, 0, ang));
    for (const s of [1, -1]) {
      M.tubo('negro', [a[0], a[1] + 0.03, s * 0.53], [b[0], b[1], s * 0.53], 0.014, 5, false);
      M.tubo('negro', [b[0], b[1], s * 0.53], [0.80, 1.0, s * 0.18], 0.012, 5, false);
    }
    M.tubo('negro', [b[0], b[1], 0.53], [b[0], b[1], -0.53], 0.014, 5, false);
    M.caja('negro', 0.04, 0.01, 0.4, mtx(b[0] - 0.02, b[1] + 0.12, 0.05, 0, 0, ang));   // plumilla
  }
}

const DX_MOTOTAXI = 0.025;

function crearMototaxi(color, v) {
  let cuerpo = _geoCache.get('mototaxi');
  if (!cuerpo) {
    const M = new Malla();
    cuerpoMototaxi(M);
    cuerpo = M.construir();
    cuerpo.geo.translate(DX_MOTOTAXI, 0, 0);
    _geoCache.set('mototaxi', cuerpo);
  }
  const g = new THREE.Group();
  const malla = new THREE.Mesh(cuerpo.geo, cuerpo.claves.map((k) => resolverMat(k, color, v)));
  malla.castShadow = true;
  malla.receiveShadow = true;
  g.add(malla);
  const matD = matAro('moto'), matT = matAro('rayos');
  const dx = DX_MOTOTAXI;
  const rd = rueda(geoRueda(0.27, 0.09, 0.7, { seg: 14, dosCaras: true }), matD, 1.08 + dx, 0.27, 0, 1);
  const gT = geoRueda(0.26, 0.11, 0.62, { seg: 14 });
  const r1 = rueda(gT, matT, -0.62 + dx, 0.26, 0.52, 1);
  const r2 = rueda(gT, matT, -0.62 + dx, 0.26, -0.52, -1);
  g.add(rd, r1, r2);
  if (v.sombra) {
    g.add(sombraContacto('mototaxi', 3.3, 1.75, [[-1.40 + dx, 0.18 + dx, -0.64, 0.64, 0.40], [0.18 + dx, 1.25 + dx, -0.16, 0.16, 0.30]],
      [[1.08 + dx, 0, 0.15, 0.06, 0.55], [-0.62 + dx, 0.52, 0.15, 0.07, 0.55], [-0.62 + dx, -0.52, 0.15, 0.07, 0.55]]));
  }
  g.userData.ruedas = [rd, r1, r2];
  return g;
}

// ===================================================================== interfaz pública
function variante(tipo, seed) {
  const R = rng(((seed | 0) >>> 0) * 7919 + 17);
  const a = R(), b = R(), c = R(), d = R();
  const ll = AUTOS[tipo] ? AUTOS[tipo].llantas : null;
  return {
    placa: Math.floor(a * 8),
    llanta: ll ? ll[Math.floor(b * ll.length)] : null,
    rieles: tipo === 'suv' ? c < 0.75 : false,
    antivuelco: tipo === 'pickup' ? c < 0.5 : false,
    franja: ['#b3261e', '#1d4f91', '#2e6b30', '#d9a21b', '#1d4f91'][Math.floor(d * 5)],
  };
}

export function crearVehiculo(tipo, { color = '#cccccc', seed = 1, sombra = true } = {}) {
  if (!DIMENSIONES[tipo]) tipo = 'sedan';
  const v = variante(tipo, seed);
  v.sombra = sombra;
  let g;
  if (tipo === 'moto') {
    v.franja = color;
    g = crearMoto(color, v);
  } else if (tipo === 'mototaxi') {
    v.franja = new THREE.Color(color).getHSL({}).l < 0.5 ? '#f2f2ef' : '#1b1b1b';
    g = crearMototaxi(color, v);
  } else {
    g = crearAuto(tipo, color, v);
  }
  g.name = 'vehiculo_' + tipo;
  g.userData.tipo = tipo;
  return g;
}
