// Entorno urbano alrededor del lote (Mendoza, prov. Rodríguez de Mendoza, Amazonas, ~1600 m s.n.m.).
// Suelo y cerros del valle, Jr. Rodríguez de Mendoza (asfalto) y calle lateral (losas de concreto),
// veredas con sardinel y rebajes vehiculares frente a los portones, casas vecinas de 1-2 pisos
// (tarrajeo pintado, ladrillo, calamina, teja, rejas, aleros), vegetación (árboles, eucaliptos,
// palmeras, plátanos, arbustos), postes de concreto con cables y caseríos lejanos.
// Todo procedural (CanvasTexture) y determinista (semillas fijas).
// Interfaz: crearEntorno(scene, datos, opciones) -> { grupo: THREE.Group, actualizar(t) }
import * as THREE from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { ImprovedNoise } from 'three/addons/math/ImprovedNoise.js';
import { rng } from './texturas.js';

// ================================================================ parámetros generales
const LIM_L = [-140, 150];      // límites del pueblo medidos como distancia a la recta A-D (+ hacia el norte)
const LIM_J = [-150, 165];      // límites del pueblo medidos como distancia a la recta A-B (+ hacia el oeste)
const FONDO_ESQ = 12;           // fondo de las casas de esquina (las filas transversales empiezan detrás)
const R_CERCA = 85;             // radio (desde el centro del lote) del nivel de detalle alto con sombras
const R_MEDIO = 290;            // radio del nivel de detalle medio
const Y_VEREDA = 0.15;

// ================================================================ utilidades 2D / ruido
const sub = (a, b) => [a[0] - b[0], a[1] - b[1]];
const add = (a, b) => [a[0] + b[0], a[1] + b[1]];
const mul = (a, k) => [a[0] * k, a[1] * k];
const dot = (a, b) => a[0] * b[0] + a[1] * b[1];
const len = (a) => Math.hypot(a[0], a[1]);
const nrm = (a) => { const l = len(a) || 1; return [a[0] / l, a[1] / l]; };
const perp = (a) => [-a[1], a[0]];
const lerp = (a, b, t) => a + (b - a) * t;
const lerp2 = (a, b, t) => [lerp(a[0], b[0], t), lerp(a[1], b[1], t)];
const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
const suave = (x) => { x = clamp(x, 0, 1); return x * x * (3 - 2 * x); };
const cruz3 = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const nrm3 = (a) => { const l = Math.hypot(a[0], a[1], a[2]) || 1; return [a[0] / l, a[1] / l, a[2] / l]; };
const ARRIBA = [0, 1, 0], ABAJO = [0, -1, 0];

const PERLIN = new ImprovedNoise();
function fbm(x, y, oct = 4, z = 0.37) {
  let s = 0, a = 1, f = 1, n = 0;
  for (let i = 0; i < oct; i++) { s += a * PERLIN.noise(x * f, y * f, z + i * 7.13); n += a; a *= 0.5; f *= 2.03; }
  return s / n * 1.6;
}
const hash2 = (i, j) => { const s = Math.sin(i * 127.1 + j * 311.7) * 43758.5453; return s - Math.floor(s); };

function enPoly(p, poly) {
  let dentro = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const xi = poly[i][0], zi = poly[i][1], xj = poly[j][0], zj = poly[j][1];
    if ((zi > p[1]) !== (zj > p[1]) && p[0] < ((xj - xi) * (p[1] - zi)) / (zj - zi) + xi) dentro = !dentro;
  }
  return dentro;
}
function cruzan(p1, p2, p3, p4) {
  const d = (a, b, c) => (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]);
  const d1 = d(p3, p4, p1), d2 = d(p3, p4, p2), d3 = d(p1, p2, p3), d4 = d(p1, p2, p4);
  return ((d1 > 0) !== (d2 > 0)) && ((d3 > 0) !== (d4 > 0));
}
function chocan(P, Q) {
  for (const p of P) if (enPoly(p, Q)) return true;
  for (const q of Q) if (enPoly(q, P)) return true;
  for (let i = 0; i < P.length; i++) for (let j = 0; j < Q.length; j++)
    if (cruzan(P[i], P[(i + 1) % P.length], Q[j], Q[(j + 1) % Q.length])) return true;
  return false;
}
function distSeg(p, a, b) {
  const ab = sub(b, a); const t = clamp(dot(sub(p, a), ab) / (dot(ab, ab) || 1), 0, 1);
  return len(sub(p, add(a, mul(ab, t))));
}
function distPoly(p, poly) {
  let m = Infinity;
  for (let i = 0; i < poly.length; i++) m = Math.min(m, distSeg(p, poly[i], poly[(i + 1) % poly.length]));
  return enPoly(p, poly) ? -m : m;
}
const centroide = (poly) => poly.reduce((s, p) => [s[0] + p[0] / poly.length, s[1] + p[1] / poly.length], [0, 0]);
function encoger(poly, k) {
  const c = centroide(poly);
  return poly.map((p) => { const d = sub(p, c); const l = len(d) || 1; return add(c, mul(d, Math.max(0, l - k) / l)); });
}

/** Marco de una calle: origen o, dirección t (a lo largo), normal n. s = abscisa, e = desplazamiento */
class Marco {
  constructor(o, t, n) { this.o = o; this.t = t; this.n = n; }
  p(s, e) { return [this.o[0] + this.t[0] * s + this.n[0] * e, this.o[1] + this.t[1] * s + this.n[1] * e]; }
  s(P) { return (P[0] - this.o[0]) * this.t[0] + (P[1] - this.o[1]) * this.t[1]; }
  e(P) { return (P[0] - this.o[0]) * this.n[0] + (P[1] - this.o[1]) * this.n[1]; }
  linea(e) { return { p: this.p(0, e), d: this.t }; }
}
/** Punto donde la recta {m1.e = e1} corta a {m2.e = e2} */
function cruce(m1, e1, m2, e2) {
  const b1 = e1 + dot(m1.n, m1.o), b2 = e2 + dot(m2.n, m2.o);
  const det = m1.n[0] * m2.n[1] - m1.n[1] * m2.n[0];
  return [(b1 * m2.n[1] - m1.n[1] * b2) / det, (m1.n[0] * b2 - b1 * m2.n[0]) / det];
}
function interLineas(L1, L2) {
  const den = L1.d[0] * L2.d[1] - L1.d[1] * L2.d[0];
  if (Math.abs(den) < 1e-9) return null;
  const w = sub(L2.p, L1.p);
  const t = (w[0] * L2.d[1] - w[1] * L2.d[0]) / den;
  return add(L1.p, mul(L1.d, t));
}

// colores (hex sRGB -> lineal)
const _col = new THREE.Color();
const col = (hex, k = 1) => { _col.set(hex); return [_col.r * k, _col.g * k, _col.b * k]; };
const mezclar = (a, b, t) => [lerp(a[0], b[0], t), lerp(a[1], b[1], t), lerp(a[2], b[2], t)];
const escalar = (a, k) => [a[0] * k, a[1] * k, a[2] * k];
const elegir = (rnd, lista) => lista[Math.floor(rnd() * lista.length) % lista.length];
function elegirPeso(rnd, lista) {
  const tot = lista.reduce((s, x) => s + x[1], 0);
  let r = rnd() * tot;
  for (const x of lista) { r -= x[1]; if (r <= 0) return x[0]; }
  return lista[lista.length - 1][0];
}

// ================================================================ constructor de geometría
class GB {
  constructor() { this.p = []; this.n = []; this.t = []; this.c = []; this.i = []; this.nv = 0; }
  vert(P, N, U, C) {
    this.p.push(P[0], P[1], P[2]); this.n.push(N[0], N[1], N[2]); this.t.push(U[0], U[1]); this.c.push(C[0], C[1], C[2]);
    return this.nv++;
  }
  /** Polígono plano convexo. 'hacia' orienta la cara (normal hacia ese lado). col: [r,g,b] o lista por vértice */
  poly(pts, uvs, colr, hacia = null) {
    let nx = 0, ny = 0, nz = 0;
    for (let k = 0; k < pts.length; k++) {
      const a = pts[k], b = pts[(k + 1) % pts.length];
      nx += (a[1] - b[1]) * (a[2] + b[2]); ny += (a[2] - b[2]) * (a[0] + b[0]); nz += (a[0] - b[0]) * (a[1] + b[1]);
    }
    const l = Math.hypot(nx, ny, nz);
    if (l < 1e-7) return;
    nx /= l; ny /= l; nz /= l;
    const orden = pts.map((_, k) => k);
    if (hacia && nx * hacia[0] + ny * hacia[1] + nz * hacia[2] < 0) { nx = -nx; ny = -ny; nz = -nz; orden.reverse(); }
    const porVertice = Array.isArray(colr[0]);
    const base = this.nv;
    for (const k of orden) this.vert(pts[k], [nx, ny, nz], uvs ? uvs[k] : [0, 0], porVertice ? colr[k] : colr);
    for (let k = 1; k < pts.length - 1; k++) this.i.push(base, base + k, base + k + 1);
  }
  /** Agrega una BufferGeometry transformada */
  geo(g, m, colr, uvEsc = 1) {
    const pos = g.attributes.position, nor = g.attributes.normal, uv = g.attributes.uv;
    const nm = new THREE.Matrix3().getNormalMatrix(m);
    const v = new THREE.Vector3(), nn = new THREE.Vector3();
    const base = this.nv;
    for (let k = 0; k < pos.count; k++) {
      v.fromBufferAttribute(pos, k).applyMatrix4(m);
      nn.fromBufferAttribute(nor, k).applyMatrix3(nm).normalize();
      this.vert([v.x, v.y, v.z], [nn.x, nn.y, nn.z], uv ? [uv.getX(k) * uvEsc, uv.getY(k) * uvEsc] : [0, 0], colr);
    }
    if (g.index) for (let k = 0; k < g.index.count; k++) this.i.push(base + g.index.getX(k));
    else for (let k = 0; k < pos.count; k++) this.i.push(base + k);
  }
  /** Caja orientada (centro, ejes unitarios 3D, semi-dimensiones) */
  caja(c, ex, ey, ez, hx, hy, hz, colr, sinBase = false) {
    const P = (a, b, d) => [c[0] + ex[0] * a * hx + ey[0] * b * hy + ez[0] * d * hz,
      c[1] + ex[1] * a * hx + ey[1] * b * hy + ez[1] * d * hz, c[2] + ex[2] * a * hx + ey[2] * b * hy + ez[2] * d * hz];
    const neg = (q) => [-q[0], -q[1], -q[2]];
    const cara = (pts, h, du, dv) => this.poly(pts, [[0, 0], [du, 0], [du, dv], [0, dv]], colr, h);
    cara([P(1, -1, -1), P(1, -1, 1), P(1, 1, 1), P(1, 1, -1)], ex, 2 * hz, 2 * hy);
    cara([P(-1, -1, 1), P(-1, -1, -1), P(-1, 1, -1), P(-1, 1, 1)], neg(ex), 2 * hz, 2 * hy);
    cara([P(-1, 1, -1), P(1, 1, -1), P(1, 1, 1), P(-1, 1, 1)], ey, 2 * hx, 2 * hz);
    if (!sinBase) cara([P(-1, -1, 1), P(1, -1, 1), P(1, -1, -1), P(-1, -1, -1)], neg(ey), 2 * hx, 2 * hz);
    cara([P(-1, -1, 1), P(1, -1, 1), P(1, 1, 1), P(-1, 1, 1)], ez, 2 * hx, 2 * hy);
    cara([P(1, -1, -1), P(-1, -1, -1), P(-1, 1, -1), P(1, 1, -1)], neg(ez), 2 * hx, 2 * hy);
  }
  /** Caja entre dos puntos 3D (eje a lo largo), ancho horizontal y alto */
  cajaSeg(A, B, ancho, alto, colr, arriba = ARRIBA, sinBase = false) {
    const d = [B[0] - A[0], B[1] - A[1], B[2] - A[2]];
    const L = Math.hypot(d[0], d[1], d[2]);
    if (L < 1e-4) return;
    const ex = [d[0] / L, d[1] / L, d[2] / L];
    let ez = cruz3(ex, arriba);
    if (Math.hypot(ez[0], ez[1], ez[2]) < 1e-4) ez = cruz3(ex, [1, 0, 0]);
    ez = nrm3(ez);
    const ey = nrm3(cruz3(ez, ex));
    this.caja([(A[0] + B[0]) / 2, (A[1] + B[1]) / 2, (A[2] + B[2]) / 2], ex, ey, ez, L / 2, alto / 2, ancho / 2, colr, sinBase);
  }
  /** Prisma vertical sobre un polígono convexo 2D (mundo) */
  prisma(pts, y0, y1, colr, { tapa = true, fondo = false, colTapa = null } = {}) {
    const c = centroide(pts);
    let u = 0;
    for (let k = 0; k < pts.length; k++) {
      const a = pts[k], b = pts[(k + 1) % pts.length];
      const L = len(sub(b, a));
      const m = lerp2(a, b, 0.5); const o = nrm(sub(m, c));
      this.poly([[a[0], y0, a[1]], [b[0], y0, b[1]], [b[0], y1, b[1]], [a[0], y1, a[1]]],
        [[u, y0], [u + L, y0], [u + L, y1], [u, y1]], colr, [o[0], 0, o[1]]);
      u += L;
    }
    if (tapa) this.poly(pts.map((p) => [p[0], y1, p[1]]), pts.map((p) => [p[0], p[1]]), colTapa || colr, ARRIBA);
    if (fondo) this.poly(pts.map((p) => [p[0], y0, p[1]]), pts.map((p) => [p[0], p[1]]), colTapa || colr, ABAJO);
  }
  vacio() { return this.nv === 0; }
  build() {
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(this.p, 3));
    g.setAttribute('normal', new THREE.Float32BufferAttribute(this.n, 3));
    g.setAttribute('uv', new THREE.Float32BufferAttribute(this.t, 2));
    g.setAttribute('color', new THREE.Float32BufferAttribute(this.c, 3));
    g.setIndex(this.i);
    g.computeBoundingSphere();
    return g;
  }
}
const juego = () => ({ muro: new GB(), ladrillo: new GB(), calamina: new GB(), teja: new GB(), ventana: new GB(),
  puerta: new GB(), oscuro: new GB(), letrero: new GB(), losa: new GB() });

// ================================================================ texturas procedurales
function lienzo(w, h) { const c = document.createElement('canvas'); c.width = w; c.height = h; return [c, c.getContext('2d')]; }
function texDe(c, srgb = true, aniso = 8) {
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.anisotropy = aniso;
  if (srgb) t.colorSpace = THREE.SRGBColorSpace;
  return t;
}
const rep = (t, rx, ry) => { t.repeat.set(rx, ry); return t; };
/** Mancha radial con envoltura (textura continua al repetirse) */
function mancha(x, W, H, px, py, rad, c0, sx = 1, sy = 1) {
  for (const ox of [-W, 0, W]) for (const oy of [-H, 0, H]) {
    const cx = px + ox, cy = py + oy;
    if (cx + rad * sx < 0 || cx - rad * sx > W || cy + rad * sy < 0 || cy - rad * sy > H) continue;
    x.save(); x.translate(cx, cy); x.scale(sx, sy);
    const g = x.createRadialGradient(0, 0, 0, 0, 0, rad);
    g.addColorStop(0, c0); g.addColorStop(1, 'rgba(0,0,0,0)');
    x.fillStyle = g; x.fillRect(-rad, -rad, 2 * rad, 2 * rad);
    x.restore();
  }
}
function granulado(x, W, H, r, amp, motas = 0, motaAmp = 0, tinte = 0) {
  const img = x.getImageData(0, 0, W, H); const d = img.data;
  for (let i = 0; i < d.length; i += 4) {
    let n = (r() - 0.5) * amp;
    if (motas && r() < motas) n += (r() - 0.5) * motaAmp;
    const t = tinte ? (r() - 0.5) * tinte : 0;
    d[i] += n + t; d[i + 1] += n; d[i + 2] += n - t;
  }
  x.putImageData(img, 0, 0);
}
function grieta(x, r, px, py, pasos, paso, ang, ancho, colr) {
  x.strokeStyle = colr; x.lineWidth = ancho; x.beginPath(); x.moveTo(px, py);
  for (let k = 0; k < pasos; k++) { ang += (r() - 0.5) * 0.9; px += Math.cos(ang) * paso; py += Math.sin(ang) * paso; x.lineTo(px, py); }
  x.stroke();
}

/** Pasto/tierra neutro (el tono lo dan los colores de vértice) – 512 px = 7 m */
function genPasto(r) {
  const W = 512; const [c, x] = lienzo(W, W);
  x.fillStyle = '#d4d8c8'; x.fillRect(0, 0, W, W);
  for (let i = 0; i < 70; i++) mancha(x, W, W, r() * W, r() * W, 18 + r() * 50, r() < 0.5 ? 'rgba(150,140,115,0.22)' : 'rgba(235,240,215,0.2)');
  for (let i = 0; i < 15000; i++) {
    const L = 150 + r() * 105;
    x.fillStyle = `rgba(${(L * (0.9 + r() * 0.08)) | 0},${L | 0},${(L * (0.72 + r() * 0.12)) | 0},${0.3 + r() * 0.45})`;
    x.save(); x.translate(r() * W, r() * W); x.rotate((r() - 0.5) * 1.1); x.fillRect(0, 0, 1.3, 3 + r() * 5); x.restore();
  }
  for (let i = 0; i < 900; i++) { x.fillStyle = `rgba(110,100,80,${0.25 + r() * 0.3})`; x.fillRect(r() * W, r() * W, 1 + r() * 2, 1 + r() * 2); }
  granulado(x, W, W, r, 16);
  return texDe(c);
}
/** Afirmado (vía de tierra compactada) – 512 px = 6 m (u: ancho, v: largo) */
function genAfirmado(r) {
  const W = 512; const [c, x] = lienzo(W, W);
  x.fillStyle = '#9e8a69'; x.fillRect(0, 0, W, W);
  for (let i = 0; i < 90; i++) mancha(x, W, W, r() * W, r() * W, 15 + r() * 60, r() < 0.5 ? 'rgba(110,92,66,0.3)' : 'rgba(190,175,145,0.22)');
  for (const u of [0.24, 0.76]) for (let k = 0; k < 7; k++) { x.fillStyle = 'rgba(80,66,48,0.05)'; x.fillRect(u * W - (14 + 5 * k), 0, 2 * (14 + 5 * k), W); }
  for (let i = 0; i < 8; i++) mancha(x, W, W, (r() < 0.5 ? 0.24 : 0.76) * W, r() * W, 10 + r() * 22, 'rgba(60,52,42,0.45)', 1, 2.5);
  for (let i = 0; i < 2500; i++) { const g = 120 + r() * 110; x.fillStyle = `rgba(${g | 0},${(g * 0.95) | 0},${(g * 0.88) | 0},0.8)`; x.fillRect(r() * W, r() * W, 1 + r() * 3, 1 + r() * 3); }
  for (const lado of [0, 1]) {
    const g = x.createLinearGradient(lado ? W : 0, 0, lado ? W - 50 : 50, 0);
    g.addColorStop(0, 'rgba(95,120,60,0.75)'); g.addColorStop(1, 'rgba(95,120,60,0)');
    x.fillStyle = g; x.fillRect(lado ? W - 50 : 0, 0, 50, W);
  }
  granulado(x, W, W, r, 22, 0.02, 50, 6);
  return texDe(c);
}
/** Asfalto del jirón con desgaste y eje amarillo discontinuo – 512 x 2048 px = 7 x 32 m */
function genAsfalto(r) {
  const W = 512, H = 2048, pxm = W / 7, pyv = H / 32; const [c, x] = lienzo(W, H);
  x.fillStyle = '#58595b'; x.fillRect(0, 0, W, H);
  for (let i = 0; i < 260; i++) mancha(x, W, H, r() * W, r() * H, 25 + r() * 110, r() < 0.55 ? 'rgba(32,32,34,0.13)' : 'rgba(128,128,124,0.10)', 1, 1 + r());
  for (const um of [0.95, 2.6, 4.4, 6.05]) for (let k = 0; k < 7; k++) { x.fillStyle = 'rgba(24,24,26,0.035)'; x.fillRect(um * pxm - (10 + 5 * k), 0, 2 * (10 + 5 * k), H); }
  for (let i = 0; i < 70; i++) mancha(x, W, H, (r() < 0.5 ? 1.75 : 5.25) * pxm + (r() - 0.5) * 30, r() * H, 4 + r() * 12, 'rgba(15,15,15,0.28)', 1, 1.6);
  for (const lado of [0, 1]) {
    const g = x.createLinearGradient(lado ? W : 0, 0, lado ? W - 34 : 34, 0);
    g.addColorStop(0, 'rgba(150,136,110,0.55)'); g.addColorStop(1, 'rgba(150,136,110,0)');
    x.fillStyle = g; x.fillRect(lado ? W - 34 : 0, 0, 34, H);
  }
  for (let i = 0; i < 4; i++) {
    const pw = 60 + r() * 140, ph = 70 + r() * 200, px = 30 + r() * (W - 60 - pw), py = r() * (H - ph);
    x.fillStyle = r() < 0.5 ? 'rgba(40,40,42,0.22)' : 'rgba(110,110,108,0.16)'; x.fillRect(px, py, pw, ph);
    x.strokeStyle = 'rgba(30,30,30,0.28)'; x.lineWidth = 2; x.strokeRect(px, py, pw, ph);
  }
  for (let i = 0; i < 22; i++) grieta(x, r, r() * W, r() * H, 6 + (r() * 8 | 0), 9, Math.PI / 2 + (r() - 0.5), 1 + r() * 0.8, 'rgba(28,28,28,0.32)');
  const lw = 0.12 * pxm;
  for (let v0 = 0; v0 < H; v0 += 8 * pyv) { x.fillStyle = '#dcb944'; x.fillRect(W / 2 - lw / 2, v0 + 20, lw, 3 * pyv); }
  for (let i = 0; i < 700; i++) { x.fillStyle = `rgba(95,95,92,${0.3 + r() * 0.3})`; x.fillRect(W / 2 - lw / 2 + r() * lw, r() * H, 1 + r() * 2, 1 + r() * 2); }
  granulado(x, W, H, r, 26, 0.03, 70);
  return texDe(c);
}
/** Losas de concreto de la calle lateral – 512 x 2048 px = 6 x 24 m (juntas c/4 m y junta central) */
function genLosas(r) {
  const W = 512, H = 2048, pxm = W / 6; const [c, x] = lienzo(W, H);
  x.fillStyle = '#9a978f'; x.fillRect(0, 0, W, H);
  const losa = 4 * pxm;
  for (let j = 0; j < 6; j++) for (let i = 0; i < 2; i++) {
    const d = (r() - 0.5) * 22; x.fillStyle = `rgb(${(146 + d) | 0},${(142 + d) | 0},${(134 + d) | 0})`;
    x.fillRect(i * W / 2, j * losa, W / 2, losa);
  }
  for (let i = 0; i < 220; i++) mancha(x, W, H, r() * W, r() * H, 20 + r() * 90, r() < 0.7 ? 'rgba(62,60,54,0.13)' : 'rgba(190,185,175,0.09)');
  for (const um of [0.9, 2.2, 3.8, 5.1]) for (let k = 0; k < 6; k++) { x.fillStyle = 'rgba(40,40,40,0.03)'; x.fillRect(um * pxm - (9 + 5 * k), 0, 2 * (9 + 5 * k), H); }
  for (const lado of [0, 1]) {
    const g = x.createLinearGradient(lado ? W : 0, 0, lado ? W - 30 : 30, 0);
    g.addColorStop(0, 'rgba(95,95,70,0.5)'); g.addColorStop(1, 'rgba(95,95,70,0)');
    x.fillStyle = g; x.fillRect(lado ? W - 30 : 0, 0, 30, H);
  }
  for (let i = 0; i < 16; i++) grieta(x, r, r() * W, Math.floor(r() * 6) * losa, 6 + (r() * 8 | 0), 12, Math.PI / 2 + (r() - 0.5), 1.2, 'rgba(50,50,48,0.55)');
  x.fillStyle = 'rgba(55,54,52,0.9)';
  for (let j = 0; j <= 6; j++) x.fillRect(0, j * losa - 1.5, W, 3);
  x.fillRect(W / 2 - 1.5, 0, 3, H);
  granulado(x, W, H, r, 18, 0.02, 40);
  return texDe(c);
}
/** Vereda de concreto con bruñas – 256 x 512 px = 1.2 x 2.4 m */
function genVereda(r) {
  const W = 256, H = 512; const [c, x] = lienzo(W, H);
  x.fillStyle = '#c4c0b6'; x.fillRect(0, 0, W, H);
  for (let j = 0; j < 2; j++) { const d = (r() - 0.5) * 16; x.fillStyle = `rgba(${(190 + d) | 0},${(186 + d) | 0},${(178 + d) | 0},0.7)`; x.fillRect(0, j * 256, W, 256); }
  for (let i = 0; i < 40; i++) mancha(x, W, H, r() * W, r() * H, 10 + r() * 40, r() < 0.6 ? 'rgba(90,86,78,0.12)' : 'rgba(225,222,215,0.12)');
  for (let y = 0; y < H; y += 2 + r() * 2) { x.fillStyle = `rgba(${r() < 0.5 ? '255,255,255' : '60,60,60'},0.035)`; x.fillRect(0, y, W, 1); }
  x.fillStyle = 'rgba(80,77,70,0.85)'; x.fillRect(0, 0, W, 2.5); x.fillRect(0, 256 - 1, W, 2.5);
  x.fillStyle = 'rgba(235,232,225,0.4)'; x.fillRect(0, 3, W, 1.5); x.fillRect(0, 257.5, W, 1.5);
  granulado(x, W, H, r, 16, 0.02, 30);
  return texDe(c);
}
/** Tarrajeo casi blanco (se tiñe con colores de vértice) – 512 px = 3 m */
function genMuro(r) {
  const W = 512; const [c, x] = lienzo(W, W);
  x.fillStyle = '#efede7'; x.fillRect(0, 0, W, W);
  for (let i = 0; i < 120; i++) mancha(x, W, W, r() * W, r() * W, 12 + r() * 60, r() < 0.5 ? 'rgba(170,165,150,0.09)' : 'rgba(255,255,255,0.1)', 1, 0.6 + r());
  for (let i = 0; i < 30; i++) {
    const px = r() * W, py = r() * W, L = 80 + r() * 260, w = 2 + r() * 8;
    for (const oy of [0, -W]) {
      const g = x.createLinearGradient(0, py + oy, 0, py + oy + L);
      g.addColorStop(0, 'rgba(110,105,95,0.09)'); g.addColorStop(1, 'rgba(110,105,95,0)');
      x.fillStyle = g; x.fillRect(px, py + oy, w, L);
    }
  }
  granulado(x, W, W, r, 9);
  return texDe(c);
}
/** Ladrillo caravista (King Kong) – 512 px = 1.02 x 1.05 m (4 ladrillos x 10 hiladas) */
function genLadrillo(r) {
  const W = 512; const [c, x] = lienzo(W, W);
  x.fillStyle = '#a8998a'; x.fillRect(0, 0, W, W);
  const ch = W / 10, bw = W / 4;
  for (let j = 0; j < 10; j++) for (let i = -1; i < 5; i++) {
    const off = (j % 2) * bw / 2;
    const quem = r() < 0.12;
    const d = (r() - 0.5) * 30;
    const R = quem ? 125 + d : 178 + d, G = quem ? 66 + d * 0.6 : 98 + d * 0.7, B = quem ? 46 + d * 0.4 : 66 + d * 0.5;
    x.fillStyle = `rgb(${R | 0},${G | 0},${B | 0})`;
    x.fillRect(i * bw + off + 3.8, j * ch + 3.6, bw - 7.5, ch - 7.2);
    x.fillStyle = 'rgba(255,230,210,0.07)'; x.fillRect(i * bw + off + 3.8, j * ch + 3.6, bw - 7.5, 3);
    x.fillStyle = 'rgba(40,20,10,0.10)'; x.fillRect(i * bw + off + 3.8, j * ch + ch - 7, bw - 7.5, 3.4);
  }
  for (let i = 0; i < 400; i++) { x.fillStyle = `rgba(60,35,25,${0.2 + r() * 0.3})`; x.fillRect(r() * W, r() * W, 1 + r() * 2, 1 + r() * 2); }
  granulado(x, W, W, r, 16, 0, 0, 8);
  return texDe(c);
}
/** Calamina ondulada (mapa gris claro + normal) – 256 x 512 px = 0.80 x 1.80 m, 10 ondas */
function genCalamina(r) {
  const W = 256, H = 512, ondas = 10;
  const [c, x] = lienzo(W, H);
  const img = x.createImageData(W, H); const d = img.data;
  for (let j = 0; j < H; j++) for (let i = 0; i < W; i++) {
    const s = Math.sin((i / W) * ondas * Math.PI * 2);
    const v = 214 + 10 * s + (r() - 0.5) * 8;
    const k = (j * W + i) * 4; d[k] = v; d[k + 1] = v + 1; d[k + 2] = v + 3; d[k + 3] = 255;
  }
  x.putImageData(img, 0, 0);
  for (let i = 0; i < 26; i++) {
    const px = ((Math.floor(r() * ondas) + 0.75) / ondas) * W + (r() - 0.5) * 4, L = 40 + r() * 320, w = 2 + r() * 6;
    const g = x.createLinearGradient(0, 0, 0, L);
    g.addColorStop(0, 'rgba(125,72,38,0.32)'); g.addColorStop(1, 'rgba(125,72,38,0)');
    x.fillStyle = g; x.fillRect(px - w / 2, 0, w, L);
  }
  for (let i = 0; i < 40; i++) mancha(x, W, H, r() * W, r() * H, 8 + r() * 40, r() < 0.5 ? 'rgba(120,100,80,0.10)' : 'rgba(90,92,95,0.10)');
  x.fillStyle = 'rgba(70,70,72,0.5)'; x.fillRect(0, 0, W, 4);
  for (let i = 0; i < ondas; i += 1) { x.fillStyle = 'rgba(235,235,235,0.8)'; x.beginPath(); x.arc(((i + 0.25) / ondas) * W, 12, 2.2, 0, 7); x.fill(); }
  const [cn, xn] = lienzo(W, H);
  const imn = xn.createImageData(W, H); const dn = imn.data;
  for (let j = 0; j < H; j++) for (let i = 0; i < W; i++) {
    const ph = (i / W) * ondas * Math.PI * 2;
    let nx = -Math.cos(ph) * 0.85, ny = 0;
    if (j < 6) ny = 0.6;
    const l = Math.hypot(nx, ny, 1);
    const k = (j * W + i) * 4;
    dn[k] = (nx / l * 0.5 + 0.5) * 255; dn[k + 1] = (ny / l * 0.5 + 0.5) * 255; dn[k + 2] = (1 / l * 0.5 + 0.5) * 255; dn[k + 3] = 255;
  }
  xn.putImageData(imn, 0, 0);
  return [texDe(c), texDe(cn, false)];
}
/** Teja andina (cobijas curvas) – 512 px = 1.0 x 1.0 m: 4 tejas x 3 hiladas */
function genTeja(r) {
  const W = 512, cols = 4, filas = 3, tw = W / cols, th = W / filas;
  const [c, x] = lienzo(W, W);
  const img = x.createImageData(W, W); const d = img.data;
  const tonos = [];
  for (let j = 0; j < filas; j++) for (let i = 0; i < cols; i++) tonos.push([(r() - 0.5) * 34, r() < 0.15 ? 1 : 0]);
  const alto = new Float32Array(W * W);
  for (let j = 0; j < W; j++) for (let i = 0; i < W; i++) {
    const fi = Math.floor(j / th), ci = Math.floor(i / tw);
    const uc = (i % tw) / tw, vc = (j % th) / th;
    const perfil = Math.sin(Math.PI * uc);
    alto[j * W + i] = perfil * 0.8 + vc * 0.35;
    const [dt, oscura] = tonos[(fi % filas) * cols + (ci % cols)];
    const sombra = 0.62 + 0.38 * perfil - (vc > 0.9 ? 0.25 : 0);
    const k = (j * W + i) * 4;
    const R = (oscura ? 140 : 182) + dt, G = (oscura ? 72 : 96) + dt * 0.6, B = (oscura ? 52 : 62) + dt * 0.4;
    const n = (r() - 0.5) * 14;
    d[k] = R * sombra + n; d[k + 1] = G * sombra + n; d[k + 2] = B * sombra + n; d[k + 3] = 255;
  }
  x.putImageData(img, 0, 0);
  for (let i = 0; i < 70; i++) mancha(x, W, W, r() * W, r() * W, 6 + r() * 26, r() < 0.6 ? 'rgba(40,42,30,0.25)' : 'rgba(80,95,50,0.2)');
  const [cn, xn] = lienzo(W, W);
  const imn = xn.createImageData(W, W); const dn = imn.data;
  for (let j = 0; j < W; j++) for (let i = 0; i < W; i++) {
    const h0 = alto[j * W + i], hx = alto[j * W + ((i + 1) % W)], hy = alto[((j + 1) % W) * W + i];
    const nx = -(hx - h0) * 18, ny = (hy - h0) * 18;
    const l = Math.hypot(nx, ny, 1); const k = (j * W + i) * 4;
    dn[k] = (nx / l * 0.5 + 0.5) * 255; dn[k + 1] = (ny / l * 0.5 + 0.5) * 255; dn[k + 2] = (1 / l * 0.5 + 0.5) * 255; dn[k + 3] = 255;
  }
  xn.putImageData(imn, 0, 0);
  return [texDe(c), texDe(cn, false)];
}
/** Atlas de ventanas (4 x 2 celdas de 256 px) + mapa de rugosidad */
function genVentanas(r) {
  const W = 1024, H = 512, S = 256;
  const [c, x] = lienzo(W, H); const [cr, xr] = lienzo(W, H);
  const marcos = ['#ecebe6', '#6b4a32', '#b9bcbd', '#3f5e3a', '#2a2a2a', '#c9cbcc', '#efefea', '#3a3a3a'];
  for (let k = 0; k < 8; k++) {
    const ox = (k % 4) * S, oy = Math.floor(k / 4) * S;
    const g = x.createLinearGradient(0, oy, 0, oy + S);
    g.addColorStop(0, '#a9bccb'); g.addColorStop(0.5, '#5f7280'); g.addColorStop(1, '#36424b');
    x.fillStyle = g; x.fillRect(ox, oy, S, S);
    xr.fillStyle = 'rgb(28,28,28)'; xr.fillRect(ox, oy, S, S);
    if (k === 1 || k === 2 || k === 5) {
      const tela = k === 1 ? ['#b2452f', '#8e2f22'] : k === 2 ? ['#e8e2d2', '#c9c1ad'] : ['#3d5f8c', '#2b456b'];
      for (let i = 0; i < S; i += 12) { x.fillStyle = i % 24 ? tela[0] : tela[1]; x.fillRect(ox + i, oy + 18, 12, S - 36); }
      x.fillStyle = 'rgba(70,90,105,0.38)'; x.fillRect(ox, oy, S, S);
    }
    if (k === 7) { x.fillStyle = 'rgba(20,26,30,0.55)'; x.fillRect(ox, oy, S, S); }
    for (let i = 0; i < 3; i++) { x.fillStyle = 'rgba(255,255,255,0.07)'; x.beginPath(); const a = ox + r() * S; x.moveTo(a, oy); x.lineTo(a + 40, oy); x.lineTo(a - 60, oy + S); x.lineTo(a - 100, oy + S); x.fill(); }
    const fc = marcos[k], fw = 16;
    const rect = (px, py, pw, ph) => { x.fillStyle = fc; x.fillRect(px, py, pw, ph); xr.fillStyle = 'rgb(150,150,150)'; xr.fillRect(px, py, pw, ph); };
    if (k === 3) { // postigos de madera cerrados
      x.fillStyle = '#4c6b45'; x.fillRect(ox, oy, S, S);
      for (let j = 0; j < S; j += 14) { x.fillStyle = 'rgba(0,0,0,0.22)'; x.fillRect(ox, oy + j, S, 3); x.fillStyle = 'rgba(255,255,255,0.08)'; x.fillRect(ox, oy + j + 3, S, 2); }
      xr.fillStyle = 'rgb(170,170,170)'; xr.fillRect(ox, oy, S, S);
      rect(ox + S / 2 - 3, oy, 6, S);
    }
    rect(ox, oy, S, fw); rect(ox, oy + S - fw, S, fw); rect(ox, oy, fw, S); rect(ox + S - fw, oy, fw, S);
    if (k !== 3 && k !== 7) rect(ox + S / 2 - 5, oy, 10, S);
    if (k === 5) { rect(ox + S / 4 - 4, oy, 8, S); rect(ox + 3 * S / 4 - 4, oy, 8, S); }
    if (k === 2) rect(ox, oy + S * 0.3, S, 8);
    const reja = (colr, paso, horiz, rombo) => {
      for (let i = fw + 8; i < S - fw; i += paso) { x.fillStyle = colr; x.fillRect(ox + i, oy + 4, 5, S - 8); x.fillStyle = 'rgba(255,255,255,0.18)'; x.fillRect(ox + i + 1, oy + 4, 1, S - 8); xr.fillStyle = 'rgb(120,120,120)'; xr.fillRect(ox + i, oy + 4, 5, S - 8); }
      for (const t of horiz) { x.fillStyle = colr; x.fillRect(ox + 4, oy + t * S, S - 8, 6); xr.fillRect(ox + 4, oy + t * S, S - 8, 6); }
      if (rombo) { x.strokeStyle = colr; x.lineWidth = 4; for (let i = 0; i < 4; i++) { const cx = ox + (i + 0.5) * S / 4, cy = oy + S / 2; x.beginPath(); x.moveTo(cx, cy - 26); x.lineTo(cx + 26, cy); x.lineTo(cx, cy + 26); x.lineTo(cx - 26, cy); x.closePath(); x.stroke(); } }
    };
    if (k === 0) reja('#1f1f1f', 24, [0.12, 0.88], false);
    if (k === 1) reja('#262626', 30, [0.12, 0.36, 0.62, 0.88], false);
    if (k === 4) reja('#1b1b1b', 32, [0.1, 0.9], true);
    if (k === 6) reja('#f2f2ee', 22, [0.12, 0.88], false);
  }
  const t = texDe(c); t.wrapS = t.wrapT = THREE.ClampToEdgeWrapping;
  const tr = texDe(cr, false); tr.wrapS = tr.wrapT = THREE.ClampToEdgeWrapping;
  return [t, tr];
}
/** Atlas de puertas (4 celdas de 256 x 512): madera, metálica, enrollable, metal con vidrio (se tiñen) */
function genPuertas(r) {
  const W = 1024, H = 512, S = 256; const [c, x] = lienzo(W, H);
  for (let k = 0; k < 4; k++) {
    const ox = k * S;
    x.fillStyle = k === 0 ? '#d9cbb7' : '#d2d3d2'; x.fillRect(ox, 0, S, H);
    if (k === 0) {
      for (let i = 0; i < 260; i++) { x.fillStyle = `rgba(90,60,30,${0.05 + r() * 0.07})`; x.fillRect(ox + r() * S, 0, 1 + r() * 2, H); }
      x.fillStyle = 'rgba(0,0,0,0.35)'; x.fillRect(ox + S / 2 - 2, 0, 4, H);
      for (const [px, py, pw, ph] of [[18, 22, 92, 140], [146, 22, 92, 140], [18, 190, 92, 140], [146, 190, 92, 140], [18, 358, 92, 130], [146, 358, 92, 130]]) {
        x.fillStyle = 'rgba(0,0,0,0.22)'; x.fillRect(ox + px, py, pw, ph);
        x.fillStyle = 'rgba(255,255,255,0.16)'; x.fillRect(ox + px + 4, py + 4, pw - 8, ph - 8);
        x.fillStyle = 'rgba(0,0,0,0.06)'; x.fillRect(ox + px + 10, py + 10, pw - 20, ph - 20);
      }
      x.fillStyle = '#c8a44a'; x.fillRect(ox + S / 2 - 16, 250, 6, 22); x.fillRect(ox + S / 2 + 10, 250, 6, 22);
    } else if (k === 1) {
      for (let j = 0; j < H; j += 32) { x.fillStyle = 'rgba(0,0,0,0.16)'; x.fillRect(ox, j, S, 4); x.fillStyle = 'rgba(255,255,255,0.18)'; x.fillRect(ox, j + 4, S, 3); }
      x.fillStyle = '#2f3b44'; x.fillRect(ox + 40, 40, S - 80, 110);
      for (let i = ox + 52; i < ox + S - 46; i += 20) { x.fillStyle = '#1d1d1d'; x.fillRect(i, 40, 5, 110); }
      x.fillStyle = 'rgba(0,0,0,0.4)'; x.fillRect(ox + 6, 0, 4, H); x.fillRect(ox + S - 10, 0, 4, H);
      x.fillStyle = '#9a9a9a'; x.fillRect(ox + S - 40, 260, 10, 30);
    } else if (k === 2) {
      for (let j = 0; j < H; j += 9) { x.fillStyle = 'rgba(0,0,0,0.20)'; x.fillRect(ox, j, S, 2); x.fillStyle = 'rgba(255,255,255,0.20)'; x.fillRect(ox, j + 2, S, 2); }
      x.fillStyle = 'rgba(0,0,0,0.45)'; x.fillRect(ox, H - 16, S, 16);
      for (let i = 0; i < 30; i++) mancha(x, W, H, ox + r() * S, r() * H, 10 + r() * 30, 'rgba(120,110,95,0.12)');
    } else {
      x.fillStyle = '#26323a'; x.fillRect(ox + 26, 26, S - 52, 300);
      for (let i = ox + 36; i < ox + S - 30; i += 22) { x.fillStyle = '#202020'; x.fillRect(i, 26, 5, 300); }
      x.fillStyle = 'rgba(0,0,0,0.25)'; x.fillRect(ox + 26, 360, S - 52, 120);
      x.fillStyle = 'rgba(255,255,255,0.18)'; x.fillRect(ox + 30, 364, S - 60, 112);
    }
    x.fillStyle = 'rgba(0,0,0,0.3)'; x.fillRect(ox, 0, S, 6); x.fillRect(ox, 0, 6, H); x.fillRect(ox + S - 6, 0, 6, H);
  }
  granulado(x, W, H, r, 10);
  const t = texDe(c); t.wrapS = t.wrapT = THREE.ClampToEdgeWrapping;
  return t;
}
/** Atlas de letreros de tiendas (2 x 4 celdas de 512 x 128) */
function genLetreros() {
  const W = 1024, H = 512; const [c, x] = lienzo(W, H);
  const items = [['BODEGA', '#b8312f', '#ffffff'], ['LIBRERÍA · BAZAR', '#1f5aa6', '#ffffff'], ['FERRETERÍA', '#e8c22a', '#1d1d1d'],
    ['RESTAURANTE', '#f3efe4', '#9a2a22'], ['PANADERÍA', '#7b4a2a', '#f5e6c8'], ['BOTICA', '#1e7a4c', '#ffffff'],
    ['MULTISERVICIOS', '#f3f1ea', '#1f4f8a'], ['HOSPEDAJE', '#2b3f5c', '#f2d27a']];
  items.forEach(([txt, fondo, letra], k) => {
    const ox = (k % 2) * 512, oy = Math.floor(k / 2) * 128;
    x.fillStyle = fondo; x.fillRect(ox, oy, 512, 128);
    x.strokeStyle = 'rgba(0,0,0,0.35)'; x.lineWidth = 8; x.strokeRect(ox + 4, oy + 4, 504, 120);
    x.fillStyle = letra; x.font = `bold ${txt.length > 12 ? 54 : 68}px "Liberation Sans", Arial, sans-serif`;
    x.textAlign = 'center'; x.textBaseline = 'middle'; x.fillText(txt, ox + 256, oy + 68);
  });
  const t = texDe(c); t.wrapS = t.wrapT = THREE.ClampToEdgeWrapping;
  return t;
}
/** Follaje: racimos de hojas – 256 px */
function genHojas(r) {
  const W = 256; const [c, x] = lienzo(W, W);
  x.fillStyle = '#3e5f2c'; x.fillRect(0, 0, W, W);
  for (let i = 0; i < 2600; i++) {
    const L = r();
    x.fillStyle = L < 0.3 ? `rgba(28,46,22,${0.6 + r() * 0.3})` : L < 0.8 ? `rgba(${70 + r() * 30 | 0},${105 + r() * 35 | 0},${45 + r() * 20 | 0},0.85)` : `rgba(${120 + r() * 30 | 0},${150 + r() * 30 | 0},${70 + r() * 20 | 0},0.8)`;
    const px = r() * W, py = r() * W;
    for (const ox of [0, -W, W]) for (const oy of [0, -W, W]) {
      if (px + ox < -10 || px + ox > W + 10 || py + oy < -10 || py + oy > W + 10) continue;
      x.save(); x.translate(px + ox, py + oy); x.rotate(r() * 6.3); x.beginPath(); x.ellipse(0, 0, 2.2 + r() * 2.5, 1.1 + r() * 1.2, 0, 0, 7); x.fill(); x.restore();
    }
  }
  return texDe(c);
}

/** Losa de concreto de azotea con manchas de humedad, musgo e impermeabilizante – 512 px = 4 m */
function genLosaTecho(r) {
  const W = 512; const [c, x] = lienzo(W, W);
  x.fillStyle = '#d8d5ce'; x.fillRect(0, 0, W, W);
  for (let i = 0; i < 90; i++) mancha(x, W, W, r() * W, r() * W, 15 + r() * 70, r() < 0.55 ? 'rgba(95,93,85,0.11)' : 'rgba(245,243,236,0.08)', 1, 0.6 + r() * 0.8);
  for (let i = 0; i < 22; i++) mancha(x, W, W, r() * W, r() * W, 8 + r() * 30, 'rgba(78,92,58,0.13)');
  for (let i = 0; i < 4; i++) mancha(x, W, W, r() * W, r() * W, 20 + r() * 40, 'rgba(45,45,45,0.16)', 1.5, 0.7);
  for (let i = 0; i < 12; i++) grieta(x, r, r() * W, r() * W, 6, 10, r() * 6.3, 1, 'rgba(60,58,52,0.4)');
  granulado(x, W, W, r, 18);
  return texDe(c);
}

function texturas() {
  const T = {};
  T.pasto = rep(genPasto(rng(11)), 1 / 7, 1 / 7);
  T.afirmado = rep(genAfirmado(rng(12)), 1 / 6, 1 / 6);
  T.asfalto = rep(genAsfalto(rng(13)), 1 / 7, 1 / 32);
  T.losas = rep(genLosas(rng(14)), 1 / 6, 1 / 24);
  T.vereda = rep(genVereda(rng(15)), 1 / 1.2, 1 / 2.4);
  T.muro = rep(genMuro(rng(16)), 1 / 3, 1 / 3);
  T.ladrillo = rep(genLadrillo(rng(17)), 1 / 1.02, 1 / 1.05);
  const [cal, calN] = genCalamina(rng(18));
  T.calamina = rep(cal, 1 / 0.8, 1 / 1.8); T.calaminaN = rep(calN, 1 / 0.8, 1 / 1.8);
  const [tej, tejN] = genTeja(rng(19));
  T.teja = tej; T.tejaN = tejN;
  [T.ventanas, T.ventanasR] = genVentanas(rng(20));
  T.puertas = genPuertas(rng(21));
  T.letreros = genLetreros();
  T.hojas = genHojas(rng(22));
  T.losaTecho = rep(genLosaTecho(rng(23)), 1 / 4, 1 / 4);
  return T;
}

// ================================================================ materiales (compartidos)
const uTiempo = { value: 0 };
function conViento(mat, amp, clave) {
  mat.onBeforeCompile = (sh) => {
    sh.uniforms.uTiempo = uTiempo;
    sh.vertexShader = 'uniform float uTiempo;\n' + sh.vertexShader.replace('#include <begin_vertex>', `#include <begin_vertex>
      #ifdef USE_INSTANCING
        float faseV = instanceMatrix[3][0] * 0.37 + instanceMatrix[3][2] * 0.23;
      #else
        float faseV = 0.0;
      #endif
      float kV = max(position.y - 1.2, 0.0) * ${amp.toFixed(4)};
      transformed.x += sin(uTiempo * 1.15 + faseV + position.y * 0.4) * kV;
      transformed.z += cos(uTiempo * 0.93 + faseV * 1.3) * kV * 0.7;`);
  };
  mat.customProgramCacheKey = () => 'viento-' + clave;
  return mat;
}
/** Líneas que se desvanecen con la distancia a la cámara (cables invisibles desde lejos) */
function desvanecer(mat, d0, d1) {
  mat.onBeforeCompile = (sh) => {
    sh.vertexShader = 'varying float vDistC;\n' + sh.vertexShader.replace('#include <project_vertex>', '#include <project_vertex>\n  vDistC = -mvPosition.z;');
    sh.fragmentShader = 'varying float vDistC;\n' + sh.fragmentShader.replace('#include <fog_fragment>', `#include <fog_fragment>
  gl_FragColor.a *= 1.0 - smoothstep(${d0.toFixed(1)}, ${d1.toFixed(1)}, vDistC);`);
  };
  mat.customProgramCacheKey = () => 'desvanecer';
  return mat;
}
function materiales(renderer) {
  const T = texturas();
  const aniso = renderer && renderer.capabilities ? Math.min(8, renderer.capabilities.getMaxAnisotropy()) : 8;
  Object.values(T).forEach((t) => { t.anisotropy = aniso; });
  const std = (o) => new THREE.MeshStandardMaterial(o);
  return {
    T,
    suelo: std({ map: T.pasto, vertexColors: true, roughness: 0.97, metalness: 0 }),
    afirmado: std({ map: T.afirmado, vertexColors: true, roughness: 0.95, metalness: 0 }),
    asfalto: std({ map: T.asfalto, vertexColors: true, roughness: 0.86, metalness: 0 }),
    losas: std({ map: T.losas, vertexColors: true, roughness: 0.84, metalness: 0 }),
    vereda: std({ map: T.vereda, vertexColors: true, roughness: 0.86, metalness: 0 }),
    muro: std({ map: T.muro, vertexColors: true, roughness: 0.9, metalness: 0 }),
    ladrillo: std({ map: T.ladrillo, vertexColors: true, roughness: 0.92, metalness: 0 }),
    calamina: std({ map: T.calamina, normalMap: T.calaminaN, normalScale: new THREE.Vector2(0.9, 0.9), vertexColors: true, roughness: 0.52, metalness: 0.35 }),
    teja: std({ map: T.teja, normalMap: T.tejaN, normalScale: new THREE.Vector2(1, 1), vertexColors: true, roughness: 0.82, metalness: 0 }),
    ventana: std({ map: T.ventanas, roughnessMap: T.ventanasR, vertexColors: true, roughness: 1, metalness: 0.1, polygonOffset: true, polygonOffsetFactor: -1, polygonOffsetUnits: -2 }),
    puerta: std({ map: T.puertas, vertexColors: true, roughness: 0.62, metalness: 0.15, polygonOffset: true, polygonOffsetFactor: -1, polygonOffsetUnits: -2 }),
    oscuro: std({ vertexColors: true, roughness: 0.55, metalness: 0.3 }),
    losa: std({ map: T.losaTecho, vertexColors: true, roughness: 0.93, metalness: 0 }),
    copaLejana: std({ color: 0xffffff, roughness: 1, metalness: 0, envMapIntensity: 0.25 }),
    letrero: std({ map: T.letreros, roughness: 0.55, metalness: 0, emissive: 0xffffff, emissiveMap: T.letreros, emissiveIntensity: 0.05, polygonOffset: true, polygonOffsetFactor: -1, polygonOffsetUnits: -2 }),
    hojas: conViento(std({ map: T.hojas, roughness: 0.9, metalness: 0, envMapIntensity: 0.5 }), 0.006, 'hojas'),
    hojasLejos: std({ map: T.hojas, roughness: 0.92, metalness: 0, envMapIntensity: 0.5 }),
    tronco: std({ color: 0xffffff, roughness: 0.95, metalness: 0 }),
    fronda: conViento(std({ vertexColors: true, roughness: 0.78, metalness: 0, side: THREE.DoubleSide }), 0.012, 'fronda'),
    cable: desvanecer(new THREE.LineBasicMaterial({ color: 0x1e1e1e, transparent: true, opacity: 0.7, depthWrite: false }), 70, 240),
  };
}

// ================================================================ contexto: marcos, calles y límites
function prepararContexto(datos) {
  const cx = datos.contexto || {};
  const V = cx.ancho_vereda ?? 1.2, CAB = cx.ancho_calzada_ab ?? 7.0, CDA = cx.ancho_calzada_da ?? 6.0;
  const { A, B, C, D } = datos.vertices;
  const lote = datos.lote.map((p) => [p[0], p[1]]);
  const centro = centroide(lote);
  const tAB = nrm(sub(B, A)); let nAB = perp(tAB); if (dot(nAB, sub(centro, A)) > 0) nAB = mul(nAB, -1);
  const tAD = nrm(sub(D, A)); let nDA = perp(tAD); if (dot(nDA, sub(centro, A)) > 0) nDA = mul(nDA, -1);
  const FJ = new Marco(A, tAB, nAB), FL = new Marco(A, tAD, nDA);
  const patio = cx.patio_verde_fondo && cx.patio_verde_fondo[0] ? cx.patio_verde_fondo[0].ext.map((p) => [p[0], p[1]]) : null;
  const sJ = (e, oL) => FJ.s(cruce(FJ, e, FL, oL));
  const sL = (e, oJ) => FL.s(cruce(FL, e, FJ, oJ));
  const orden = (a, b) => [Math.min(a, b), Math.max(a, b)];
  const calles = [];
  const nueva = (o) => {
    const k = { V, ...o };
    k.half = k.w / 2 + V;
    k.sIni = k.ini ? Math.min(k.ini(k.c - k.half), k.ini(k.c + k.half)) : k.s0;
    calles.push(k); return k;
  };
  const cJ = V + CAB / 2, cL = V + CDA / 2;
  nueva({ id: 'jr', nombre: 'Jr. Rodríguez de Mendoza', m: FJ, c: cJ, w: CAB, prio: 4, s0: -720, s1: 720, tipo: 'asfalto',
    pav: orden(sJ(cJ, LIM_L[1] + 45), sJ(cJ, LIM_L[0] - 45)), ver: orden(sJ(cJ, LIM_L[1] + 20), sJ(cJ, LIM_L[0] - 20)) });
  nueva({ id: 'lat', nombre: 'Calle lateral', m: FL, c: cL, w: CDA, prio: 3, s0: 0, s1: sL(cL, LIM_J[0] - 120), tipo: 'losas',
    ini: (e) => sL(e, V), pav: [-50, sL(cL, LIM_J[0] - 15)], ver: [-50, sL(cL, LIM_J[0] - 10)] });
  const secJ = (id, c, tipo) => { const r = orden(sJ(c, LIM_L[1] + 25), sJ(c, LIM_L[0] - 25)); return nueva({ id, m: FJ, c, w: 6, prio: 2, s0: r[0] - 50, s1: r[1] + 50, tipo, pav: r, ver: r }); };
  const secL = (id, c, tipo) => { const r = orden(sL(c, LIM_J[1] + 25), sL(c, LIM_J[0] - 25)); return nueva({ id, m: FL, c, w: 6, prio: 1, s0: r[0] - 50, s1: r[1] + 50, tipo, pav: r, ver: r }); };
  secJ('se', -88, 'losas');
  secJ('sw', 98, 'afirmado');
  secL('ss', -82, 'losas');
  secL('sn', 92, 'afirmado');
  return { datos, V, CAB, CDA, A, B, C, D, lote, centro, FJ, FL, patio, calles };
}
/** Calle (corredor calzada + veredas) que contiene al punto P */
function enCalle(ctx, P, margen = 0) {
  for (const k of ctx.calles) {
    const e = k.m.e(P) - k.c;
    if (Math.abs(e) < k.half + margen) {
      const s = k.m.s(P);
      if (s > k.sIni - margen && s < k.s1 + margen) return k;
    }
  }
  return null;
}

// ================================================================ relieve del valle
function crearRelieve(ctx) {
  const { centro, FJ, calles } = ctx;
  const t = FJ.t, n = FJ.n, jr = calles[0], lat = calles[1];
  return function altura(x, z) {
    const dx = x - centro[0], dz = z - centro[1];
    const a = dx * t[0] + dz * t[1], b = dx * n[0] + dz * n[1];
    const ab = Math.abs(b), lado = b >= 0 ? 1 : 0;
    const Wv = Math.max(300, 375 + 75 * fbm(a / 450, lado * 3.1 + 0.5, 3));
    let h = 0;
    if (ab > Wv) {
      const q = ab - Wv;
      const Hs = (lado ? 260 : 320) * (0.8 + 0.4 * fbm(a / 700, lado * 7.3 + 1.7, 3));
      h = Hs * Math.pow(suave(q / 850), 1.25) + q * 0.03;
    }
    const aa = Math.abs(a);
    if (aa > 900) h = Math.max(h, 360 * suave((aa - 900) / 700) * (0.75 + 0.45 * fbm(b / 260, a > 0 ? 9.1 : 4.4, 3)));
    if (h > 0) {
      const cresta = 1 - Math.abs(fbm(x / 320, z / 320, 4, 2.3));
      h += (cresta - 0.5) * 95 * suave(h / 90) + fbm(x / 85, z / 85, 3, 5.5) * 16 * suave(h / 30);
    }
    const ell = Math.hypot(a / 460, b / 270);
    if (ell > 1) {
      let mk = suave((ell - 1) / 0.45);
      mk *= suave((Math.abs(jr.m.e([x, z]) - jr.c) - 12) / 30);
      const sl = lat.m.s([x, z]);
      if (sl > -15 && sl < lat.s1 + 40) mk *= suave((Math.abs(lat.m.e([x, z]) - lat.c) - 12) / 30);
      h += 3.5 * mk * (fbm(x / 170, z / 170, 3, 8.8) + 0.3);
    }
    return h;
  };
}
const C_T = {
  pasto: col('#7f9160'), pasto2: col('#6c8254'), tierra: col('#968266'), bosque: col('#34503a'), bosque2: col('#466b43'),
  claro: col('#7b9659'), lejos: col('#aebfcc'), campo: col('#7d9460'),
  cultivos: ['#8fa964', '#7a9655', '#a5ae68', '#a08f68', '#68894a', '#86a05a', '#98ab63', '#738f55'].map((h) => col(h)),
};
const neblina = (r) => suave((r - 450) / 1100) * 0.24;
function colorTerreno(ctx, x, z, h) {
  const P = [x, z];
  const r = len(sub(P, ctx.centro));
  const oJ = ctx.FJ.e(P), oL = ctx.FL.e(P);
  let c;
  const dPueblo = Math.max(LIM_J[0] - 20 - oJ, oJ - LIM_J[1] - 20, LIM_L[0] - 20 - oL, oL - LIM_L[1] - 20);
  const cPueblo = () => {
    const nn = fbm(x / 16, z / 16, 3, 1.3);
    let k = mezclar(C_T.pasto, C_T.tierra, suave((nn + 0.25) * 1.6));
    return mezclar(k, C_T.pasto2, suave(fbm(x / 45, z / 45, 2, 4.4) + 0.5));
  };
  const cCampo = () => escalar(C_T.campo, 0.95 + 0.1 * fbm(x / 60, z / 60, 2, 6.6));
  if (dPueblo < 0) c = cPueblo();
  else c = mezclar(cPueblo(), cCampo(), suave(dPueblo / 30));
  if (h > 1.5) {
    const f = fbm(x / 130, z / 130, 4, 7.7);
    let cb = mezclar(C_T.bosque, C_T.bosque2, suave(fbm(x / 30, z / 30, 3, 9.9) * 1.1 + 0.5));
    if (f > 0.15 && h < 240) cb = mezclar(cb, C_T.claro, suave((f - 0.15) * 3.0) * 0.8);
    c = mezclar(c, cb, suave((h - 1.5) / 22));
  }
  return mezclar(c, C_T.lejos, neblina(r));
}
function construirTerreno(ctx, altura) {
  const { centro } = ctx;
  const NA = 220, RMAX = 1750;
  const radios = [0];
  for (let r = 0; r < RMAX;) { r += r < 60 ? 2.5 : r < 320 ? Math.max(2.5, r * 0.045) : r * 0.055; radios.push(Math.min(r, RMAX)); }
  const pos = [], colr = [], uv = [], idx = [], alt = [];
  const push = (x, z) => {
    const h = altura(x, z);
    pos.push(x, h - 0.03, z); uv.push(x, z); alt.push(h);
    const c = colorTerreno(ctx, x, z, h); colr.push(c[0], c[1], c[2]);
  };
  push(centro[0], centro[1]);
  for (let k = 1; k < radios.length; k++) {
    const r = radios[k];
    for (let j = 0; j < NA; j++) { const a = (j / NA) * Math.PI * 2; push(centro[0] + r * Math.cos(a), centro[1] + r * Math.sin(a)); }
  }
  for (let j = 0; j < NA; j++) idx.push(0, 1 + ((j + 1) % NA), 1 + j);
  for (let k = 1; k < radios.length - 1; k++) {
    const b0 = 1 + (k - 1) * NA, b1 = 1 + k * NA;
    for (let j = 0; j < NA; j++) {
      const a = b0 + j, b = b0 + (j + 1) % NA, c = b1 + j, d = b1 + (j + 1) % NA;
      idx.push(a, b, c, b, d, c);
    }
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  g.setAttribute('color', new THREE.Float32BufferAttribute(colr, 3));
  g.setIndex(idx);
  g.computeVertexNormals();
  const nn = g.attributes.normal;
  if (nn.getY(0) < 0) {
    for (let k = 0; k < idx.length; k += 3) { const t = idx[k + 1]; idx[k + 1] = idx[k + 2]; idx[k + 2] = t; }
    g.setIndex(idx); g.computeVertexNormals();
  }
  // altura exacta de la malla (interpolación en los triángulos de la grilla polar) para apoyar objetos
  const H = (k, j) => (k === 0 ? alt[0] : alt[1 + (k - 1) * NA + (((j % NA) + NA) % NA)]);
  const alturaMalla = (x, z) => {
    const dx = x - centro[0], dz = z - centro[1];
    const r = Math.hypot(dx, dz);
    if (r >= RMAX - 1e-3) return altura(x, z);
    let lo = 0, hi = radios.length - 1;
    while (hi - lo > 1) { const mid = (lo + hi) >> 1; if (radios[mid] <= r) lo = mid; else hi = mid; }
    let th = Math.atan2(dz, dx); if (th < 0) th += Math.PI * 2;
    const jf = (th / (Math.PI * 2)) * NA, j = Math.floor(jf), tj = jf - j;
    const tr = (r - radios[lo]) / (radios[lo + 1] - radios[lo]);
    if (lo === 0) return lerp(alt[0], lerp(H(1, j), H(1, j + 1), tj), tr);
    const a = H(lo, j), b = H(lo, j + 1), c = H(lo + 1, j), d = H(lo + 1, j + 1);
    if (tr + tj <= 1) return a + (c - a) * tr + (b - a) * tj;
    return d + (b - d) * (1 - tr) + (c - d) * (1 - tj);
  };
  return { geo: g, alturaMalla };
}

// ================================================================ textura de parcelas (multiplicador del suelo, 1 px ~ 0.83 m)
const S_PARC = 1700, N_PARC = 2048;
function genParcelas(ctx, altura, casas) {
  const N = N_PARC, S = S_PARC;
  const [c, x] = lienzo(N, N);
  const r = rng(909);
  const [cx, cz] = ctx.centro;
  const px = (P) => [((P[0] - cx) / S + 0.5) * N, ((P[1] - cz) / S + 0.5) * N];
  const rgb = (m) => `rgb(${clamp(m[0] * 128, 0, 255) | 0},${clamp(m[1] * 128, 0, 255) | 0},${clamp(m[2] * 128, 0, 255) | 0})`;
  const poli = (pts, estilo) => { x.fillStyle = estilo; x.beginPath(); pts.forEach((p, i) => { const q = px(p); if (i) x.lineTo(q[0], q[1]); else x.moveTo(q[0], q[1]); }); x.closePath(); x.fill(); };
  x.fillStyle = 'rgb(128,128,128)'; x.fillRect(0, 0, N, N);
  const { FJ, FL } = ctx;
  const P = (oJ, oL) => cruce(FJ, oJ, FL, oL);
  const enPueblo = (oJ, oL, m = 10) => oJ > LIM_J[0] - m && oJ < LIM_J[1] + m && oL > LIM_L[0] - m && oL < LIM_L[1] + m;
  const TIPOS = [
    [[1.0, 1.0, 1.0], 0.3, 0], [[1.18, 1.12, 0.88], 0.14, 0], [[1.12, 1.16, 0.78], 0.14, 1], [[1.55, 1.02, 0.82], 0.1, 1],
    [[0.8, 0.88, 0.82], 0.12, 2], [[0.92, 1.06, 0.8], 0.12, 1], [[1.3, 1.22, 0.92], 0.08, 0],
  ];
  const tipo = () => { let q = r(); for (const t of TIPOS) { q -= t[1]; if (q <= 0) return t; } return TIPOS[0]; };
  const CW = 52, CL = 40;
  for (let i = -19; i <= 19; i++) for (let j = -24; j <= 24; j++) {
    const oJ0 = i * CW, oL0 = j * CL;
    const pc = P(oJ0 + CW / 2, oL0 + CL / 2);
    if (Math.abs(pc[0] - cx) > S / 2 + 60 || Math.abs(pc[1] - cz) > S / 2 + 60) continue;
    if (enPueblo(oJ0 + CW / 2, oL0 + CL / 2, 12)) continue;
    if (altura(pc[0], pc[1]) > 5) continue;
    const partes = r() < 0.45 ? 2 + (r() < 0.3 ? 1 : 0) : 1;
    const porJ = r() < 0.5;
    for (let k = 0; k < partes; k++) {
      const a0 = k / partes, a1 = (k + 1) / partes;
      const q = porJ ? [oJ0 + CW * a0, oL0, oJ0 + CW * a1, oL0 + CL] : [oJ0, oL0 + CL * a0, oJ0 + CW, oL0 + CL * a1];
      const esq = [P(q[0], q[1]), P(q[2], q[1]), P(q[2], q[3]), P(q[0], q[3])];
      const [m, , surcos] = tipo();
      const v = 0.92 + r() * 0.16;
      poli(esq, rgb([m[0] * v, m[1] * v, m[2] * v]));
      if (surcos === 1) {
        x.save(); x.beginPath(); esq.forEach((p, n) => { const z = px(p); if (n) x.lineTo(z[0], z[1]); else x.moveTo(z[0], z[1]); }); x.closePath(); x.clip();
        x.strokeStyle = rgb([m[0] * v * 0.82, m[1] * v * 0.85, m[2] * v * 0.85]); x.lineWidth = 1;
        const lado = r() < 0.5;
        for (let t = 0; t < 1; t += 0.035) {
          const A = lado ? P(q[0] + (q[2] - q[0]) * t, q[1]) : P(q[0], q[1] + (q[3] - q[1]) * t);
          const B = lado ? P(q[0] + (q[2] - q[0]) * t, q[3]) : P(q[2], q[1] + (q[3] - q[1]) * t);
          const a = px(A), b = px(B); x.beginPath(); x.moveTo(a[0], a[1]); x.lineTo(b[0], b[1]); x.stroke();
        }
        x.restore();
      } else if (surcos === 2) {
        for (let n = 0; n < 26; n++) {
          const z = px(P(lerp(q[0], q[2], 0.1 + r() * 0.8), lerp(q[1], q[3], 0.1 + r() * 0.8)));
          x.fillStyle = rgb([0.55, 0.65, 0.55]); x.beginPath(); x.arc(z[0], z[1], 2 + r() * 2.5, 0, 7); x.fill();
        }
      }
    }
    // cercos vivos (hileras de arbustos) en algunos linderos
    const linde = (A, B) => {
      const a = px(A), b = px(B); const L = Math.hypot(b[0] - a[0], b[1] - a[1]);
      for (let t = 0; t < L; t += 2.2) { const f = t / L; x.fillStyle = rgb([0.55 + r() * 0.15, 0.66 + r() * 0.15, 0.55]); x.beginPath(); x.arc(lerp(a[0], b[0], f), lerp(a[1], b[1], f), 1.6 + r() * 1.4, 0, 7); x.fill(); }
    };
    if (r() < 0.35) linde(P(oJ0, oL0), P(oJ0 + CW, oL0));
    if (r() < 0.35) linde(P(oJ0, oL0), P(oJ0, oL0 + CL));
  }
  // copas del bosque en las laderas (dentro del lienzo)
  for (let gx = 0; gx < N; gx += 6) for (let gz = 0; gz < N; gz += 6) {
    const X = cx + ((gx + r() * 6) / N - 0.5) * S, Z = cz + ((gz + r() * 6) / N - 0.5) * S;
    const h = altura(X, Z);
    if (h < 2) continue;
    const k = suave((h - 2) / 15);
    const osc = r() < 0.55;
    const m = osc ? 1 - 0.35 * k : 1 + 0.22 * k;
    x.fillStyle = rgb([m, m * (osc ? 1 : 1.03), m]);
    const q = px([X, Z]);
    x.beginPath(); x.arc(q[0], q[1], 3 + r() * 4, 0, 7); x.fill();
  }
  // patios traseros: tierra apisonada, huertas y pasto seco
  for (const h of casas) {
    if (h.anexo || h.distC > 330 || r() < 0.35) continue;
    const b0 = h.d + 0.4 + r() * 1.5, b1 = b0 + 3 + r() * 7;
    const a0 = h.a0 + 0.4, a1 = h.a0 + h.w - 0.4;
    const W2 = (a, b) => [h.P0[0] + h.u[0] * a + h.v[0] * b, h.P0[1] + h.u[1] * a + h.v[1] * b];
    const t = r();
    const m = t < 0.45 ? [1.45, 1.08, 0.82] : t < 0.7 ? [0.78, 0.86, 0.78] : [1.22, 1.16, 0.92];
    const v = 0.9 + r() * 0.2;
    poli([W2(a0, b0), W2(a1, b0), W2(a1, b1), W2(a0, b1)], rgb([m[0] * v, m[1] * v, m[2] * v]));
  }
  // manchas suaves en el pueblo
  for (let i = 0; i < 260; i++) {
    const oJ = lerp(LIM_J[0], LIM_J[1], r()), oL = lerp(LIM_L[0], LIM_L[1], r());
    const q = px(P(oJ, oL));
    const g = x.createRadialGradient(q[0], q[1], 0, q[0], q[1], 6 + r() * 14);
    g.addColorStop(0, r() < 0.5 ? 'rgba(180,140,105,0.45)' : 'rgba(100,112,100,0.4)'); g.addColorStop(1, 'rgba(128,128,128,0)');
    x.fillStyle = g; x.fillRect(q[0] - 20, q[1] - 20, 40, 40);
  }
  x.strokeStyle = 'rgb(128,128,128)'; x.lineWidth = 6; x.strokeRect(0, 0, N, N);
  const t = new THREE.CanvasTexture(c);
  t.flipY = false;
  t.wrapS = t.wrapT = THREE.ClampToEdgeWrapping;
  t.anisotropy = 4;
  return t;
}
function aplicarParcelas(mat, tex, centro) {
  mat.onBeforeCompile = (sh) => {
    sh.uniforms.tParcelas = { value: tex };
    sh.uniforms.uParc = { value: new THREE.Vector3(centro[0], centro[1], 1 / S_PARC) };
    sh.vertexShader = 'varying vec2 vXZp;\n' + sh.vertexShader.replace('#include <begin_vertex>', '#include <begin_vertex>\n  vXZp = (modelMatrix * vec4(position, 1.0)).xz;');
    sh.fragmentShader = 'uniform sampler2D tParcelas;\nuniform vec3 uParc;\nvarying vec2 vXZp;\n' + sh.fragmentShader.replace('#include <map_fragment>',
      '#include <map_fragment>\n  diffuseColor.rgb *= texture2D(tParcelas, (vXZp - uParc.xy) * uParc.z + 0.5).rgb * 2.0;');
  };
  mat.customProgramCacheKey = () => 'parcelas';
}

// ================================================================ calles y veredas
function tira(k, e0, e1, r0, r1) {
  const a0 = k.ini ? k.ini(e0) : k.s0, b0 = k.ini ? k.ini(e1) : k.s0;
  const t = { m: k.m, e0, e1, segs: [{ a0: Math.max(a0, r0 ?? -1e9), a1: Math.min(k.s1, r1 ?? 1e9), b0: Math.max(b0, r0 ?? -1e9), b1: Math.min(k.s1, r1 ?? 1e9), y0: Y_VEREDA, y1: Y_VEREDA, finA: true, finB: true }] };
  return t;
}
function cortarTira(t, mY, f0, f1) {
  const sb = (e, f) => t.m.s(cruce(t.m, e, mY, f));
  const ca = [sb(t.e0, f0), sb(t.e0, f1)].sort((p, q) => p - q);
  const cb = [sb(t.e1, f0), sb(t.e1, f1)].sort((p, q) => p - q);
  const out = [];
  for (const g of t.segs) {
    if ((ca[1] <= g.a0 && cb[1] <= g.b0) || (ca[0] >= g.a1 && cb[0] >= g.b1)) { out.push(g); continue; }
    if (ca[0] > g.a0 + 0.05 && cb[0] > g.b0 + 0.05) out.push({ ...g, a1: ca[0], b1: cb[0], finB: true });
    if (ca[1] < g.a1 - 0.05 && cb[1] < g.b1 - 0.05) out.push({ ...g, a0: ca[1], b0: cb[1], finA: true });
  }
  t.segs = out;
}
function partirTira(t, s) {
  const out = [];
  for (const g of t.segs) {
    if (g.a0 < s - 0.01 && g.a1 > s + 0.01 && g.b0 < s - 0.01 && g.b1 > s + 0.01) {
      out.push({ ...g, a1: s, b1: s, finB: false }, { ...g, a0: s, b0: s, finA: false });
    } else out.push(g);
  }
  t.segs = out;
}
/** Rebaje vehicular de vereda frente a un portón: tramo bajo [r0,r1] con rampas */
function rebajar(t, r0, r1, rampa = 0.9, yb = 0.012) {
  const cs = [r0 - rampa, r0, r1, r1 + rampa];
  cs.forEach((s) => partirTira(t, s));
  for (const g of t.segs) {
    const sm = (g.a0 + g.a1) / 2;
    if (sm > cs[0] && sm < cs[1]) { g.y0 = Y_VEREDA; g.y1 = yb; }
    else if (sm > cs[1] && sm < cs[2]) { g.y0 = yb; g.y1 = yb; }
    else if (sm > cs[2] && sm < cs[3]) { g.y0 = yb; g.y1 = Y_VEREDA; }
  }
}
function geoVereda(gb, t, rnd) {
  const sgn = Math.sign(t.e1 - t.e0), V = Math.abs(t.e1 - t.e0);
  const cV = col('#cfcbc2'), cS = col('#e2e0da');
  const haciaC = [-t.m.n[0] * sgn, 0, -t.m.n[1] * sgn], haciaP = [t.m.n[0] * sgn, 0, t.m.n[1] * sgn];
  const T3 = [t.m.t[0], 0, t.m.t[1]];
  for (const g of t.segs) {
    const L = Math.max(Math.abs(g.a1 - g.a0), Math.abs(g.b1 - g.b0));
    if (L < 0.05) continue;
    const N = Math.max(1, Math.ceil(L / 3));
    const F = [];
    for (let i = 0; i <= N; i++) {
      const k = i / N;
      const sa = lerp(g.a0, g.a1, k), sb = lerp(g.b0, g.b1, k), y = lerp(g.y0, g.y1, k);
      const Cp = t.m.p(sa, t.e0), Pp = t.m.p(sb, t.e1);
      const f = 0.16 / V;
      const Cb = lerp2(Cp, Pp, f);
      F.push({ Cp, Cb, Pp, y, sa, sb, sc: lerp(sa, sb, f), tono: 0.95 + 0.08 * rnd() });
    }
    const P3 = (p, y) => [p[0], y, p[1]];
    for (let i = 0; i < N; i++) {
      const p = F[i], q = F[i + 1];
      gb.poly([P3(p.Cp, p.y), P3(q.Cp, q.y), P3(q.Cb, q.y), P3(p.Cb, p.y)], [[0, p.sa], [0, q.sa], [0.16, q.sc], [0.16, p.sc]],
        [escalar(cS, p.tono), escalar(cS, q.tono), escalar(cS, q.tono), escalar(cS, p.tono)], ARRIBA);
      gb.poly([P3(p.Cb, p.y), P3(q.Cb, q.y), P3(q.Pp, q.y), P3(p.Pp, p.y)], [[0.16, p.sc], [0.16, q.sc], [V, q.sb], [V, p.sb]],
        [escalar(cV, p.tono), escalar(cV, q.tono), escalar(cV, q.tono), escalar(cV, p.tono)], ARRIBA);
      gb.poly([P3(p.Cp, -0.03), P3(q.Cp, -0.03), P3(q.Cp, q.y), P3(p.Cp, p.y)], [[p.sa, 0], [q.sa, 0], [q.sa, q.y], [p.sa, p.y]], escalar(cS, 0.9), haciaC);
      gb.poly([P3(p.Pp, -0.05), P3(q.Pp, -0.05), P3(q.Pp, q.y), P3(p.Pp, p.y)], [[p.sb, 0], [q.sb, 0], [q.sb, q.y], [p.sb, p.y]], escalar(cV, 0.85), haciaP);
    }
    if (g.finA) { const p = F[0]; gb.poly([P3(p.Cp, -0.03), P3(p.Pp, -0.03), P3(p.Pp, p.y), P3(p.Cp, p.y)], [[0, 0], [V, 0], [V, p.y], [0, p.y]], escalar(cS, 0.9), [-T3[0], 0, -T3[2]]); }
    if (g.finB) { const p = F[N]; gb.poly([P3(p.Cp, -0.03), P3(p.Pp, -0.03), P3(p.Pp, p.y), P3(p.Cp, p.y)], [[0, 0], [V, 0], [V, p.y], [0, p.y]], escalar(cS, 0.9), T3); }
  }
}
function geoCalzada(gb, t, eRef, semilla) {
  for (const g of t.segs) {
    const L = Math.max(Math.abs(g.a1 - g.a0), Math.abs(g.b1 - g.b0));
    if (L < 0.05) continue;
    const N = Math.max(1, Math.ceil(L / 4));
    const tono = (s) => 1 + 0.07 * fbm(s / 38, semilla, 2, 3.3) + 0.03 * fbm(s / 9, semilla + 4.1, 2, 1.1);
    for (let i = 0; i < N; i++) {
      const k0 = i / N, k1 = (i + 1) / N;
      const s00 = lerp(g.a0, g.a1, k0), s01 = lerp(g.a0, g.a1, k1), s10 = lerp(g.b0, g.b1, k0), s11 = lerp(g.b0, g.b1, k1);
      const p0 = t.m.p(s00, t.e0), p1 = t.m.p(s01, t.e0), p2 = t.m.p(s11, t.e1), p3 = t.m.p(s10, t.e1);
      const u0 = t.e0 - eRef, u1 = t.e1 - eRef;
      const c = [s00, s01, s11, s10].map((s) => { const v = tono(s); return [v, v, v]; });
      gb.poly([[p0[0], 0, p0[1]], [p1[0], 0, p1[1]], [p2[0], 0, p2[1]], [p3[0], 0, p3[1]]],
        [[u0, s00], [u0, s01], [u1, s11], [u1, s10]], c, ARRIBA);
    }
  }
}
function construirCalles(ctx, M, grupo) {
  const { calles, FJ, FL, V } = ctx;
  const rnd = rng(3031);
  const gV = new GB();
  const gCal = { asfalto: new GB(), losas: new GB(), afirmado: new GB() };
  const tiras = new Map();
  for (const k of calles) {
    const cal = tira(k, k.c - k.w / 2, k.c + k.w / 2);
    const vn = tira(k, k.c - k.w / 2, k.c - k.half, k.ver[0], k.ver[1]);
    const vp = tira(k, k.c + k.w / 2, k.c + k.half, k.ver[0], k.ver[1]);
    tiras.set(k.id, { cal, vn, vp });
  }
  // cruces: la calle de menor prioridad (X) se corta en los sardineles de Y; las veredas de Y se cortan en las líneas de propiedad de X
  for (const X of calles) for (const Y of calles) {
    if (X.m === Y.m || X.prio >= Y.prio) continue;
    const P = cruce(X.m, X.c, Y.m, Y.c);
    const sx = X.m.s(P), sy = Y.m.s(P);
    if (sx < X.sIni || sx > X.s1 || sy < Y.sIni || sy > Y.s1) continue;
    const tx = tiras.get(X.id), ty = tiras.get(Y.id);
    for (const t of [tx.cal, tx.vn, tx.vp]) cortarTira(t, Y.m, Y.c - Y.w / 2, Y.c + Y.w / 2);
    for (const t of [ty.vn, ty.vp]) cortarTira(t, X.m, X.c - X.half, X.c + X.half);
  }
  // T del jirón con la calle lateral (la lateral nace en el sardinel del lado del lote)
  const jr = calles[0], lat = calles[1];
  cortarTira(tiras.get('jr').vn, FL, lat.c - lat.half, lat.c + lat.half);
  // rebajes frente a los portones vehiculares del lote
  for (const a of ctx.datos.accesos || []) {
    if (a.tipo !== 'porton') continue;
    const cc = a.centro;
    for (const [k, m] of [[jr, FJ], [lat, FL]]) {
      if (Math.abs(m.e(cc)) > 0.6) continue;
      const s = [m.s(a.a), m.s(a.b)].sort((p, q) => p - q);
      rebajar(tiras.get(k.id).vn, s[0] - 0.25, s[1] + 0.25);
    }
  }
  for (const k of calles) {
    const { cal, vn, vp } = tiras.get(k.id);
    geoVereda(gV, vn, rnd);
    geoVereda(gV, vp, rnd);
    // pavimento dentro del pueblo, afirmado fuera
    partirTira(cal, k.pav[0]); partirTira(cal, k.pav[1]);
    const pav = { ...cal, segs: cal.segs.filter((g) => (g.a0 + g.a1) / 2 > k.pav[0] && (g.a0 + g.a1) / 2 < k.pav[1]) };
    const afi = { ...cal, segs: cal.segs.filter((g) => !((g.a0 + g.a1) / 2 > k.pav[0] && (g.a0 + g.a1) / 2 < k.pav[1])) };
    const eRef = k.c - k.w / 2;
    geoCalzada(gCal[k.tipo], pav, eRef, k.prio * 1.7);
    geoCalzada(gCal.afirmado, afi, eRef, k.prio * 2.3);
  }
  const agregar = (gb, mat, nombre) => {
    if (gb.vacio()) return;
    const me = new THREE.Mesh(gb.build(), mat);
    me.receiveShadow = true; me.name = nombre;
    grupo.add(me);
  };
  agregar(gV, M.vereda, 'entorno-veredas');
  agregar(gCal.asfalto, M.asfalto, 'entorno-asfalto');
  agregar(gCal.losas, M.losas, 'entorno-losas');
  agregar(gCal.afirmado, M.afirmado, 'entorno-afirmado');
}

// ================================================================ registro de ocupación (colisiones)
class Registro {
  constructor(celda = 16) { this.c = celda; this.m = new Map(); this.items = []; }
  bb(poly) {
    let x0 = Infinity, z0 = Infinity, x1 = -Infinity, z1 = -Infinity;
    for (const p of poly) { x0 = Math.min(x0, p[0]); z0 = Math.min(z0, p[1]); x1 = Math.max(x1, p[0]); z1 = Math.max(z1, p[1]); }
    return [x0, z0, x1, z1];
  }
  celdas(bb, fn) {
    for (let i = Math.floor(bb[0] / this.c); i <= Math.floor(bb[2] / this.c); i++)
      for (let j = Math.floor(bb[1] / this.c); j <= Math.floor(bb[3] / this.c); j++) fn(i + ',' + j);
  }
  agregar(poly, tag = 'casa', datos = null) {
    const it = { poly, bb: this.bb(poly), tag, datos };
    this.items.push(it);
    this.celdas(it.bb, (k) => { if (!this.m.has(k)) this.m.set(k, []); this.m.get(k).push(it); });
    return it;
  }
  cerca(bb) {
    const s = new Set();
    this.celdas(bb, (k) => { const l = this.m.get(k); if (l) l.forEach((it) => s.add(it)); });
    return s;
  }
  choca(poly) {
    const bb = this.bb(poly);
    for (const it of this.cerca(bb)) {
      if (it.bb[0] > bb[2] || it.bb[2] < bb[0] || it.bb[1] > bb[3] || it.bb[3] < bb[1]) continue;
      if (chocan(poly, it.poly)) return it;
    }
    return null;
  }
  distancia(p, r) {
    let m = Infinity;
    for (const it of this.cerca([p[0] - r, p[1] - r, p[0] + r, p[1] + r])) m = Math.min(m, distPoly(p, it.poly));
    return m;
  }
}

// ================================================================ casas
const PAL_MURO = ['#e9dfc6', '#efe8d8', '#ddd2b4', '#c3d4ae', '#a9c9b4', '#b5ccd9', '#cad9e0', '#d39a7e', '#cfa286', '#e3c483',
  '#ecdda6', '#f0eee6', '#ddb5a8', '#cbbfd6', '#e7b582', '#d6d0bf', '#cdd8c2', '#b8cfc9', '#e8d9b5', '#f2e9d0'];
const PAL_ZOC = ['#56694f', '#7b4034', '#6a6963', '#6b5241', '#46607a', '#3d3e3b', '#8a7a62', '#94493a', '#5b4b6b', '#2f4f4a'];
const PAL_TECHO = [['#a9adaf', 4], ['#8e9395', 3.5], ['#8a6148', 2.6], ['#9c4334', 2.6], ['#7a3129', 1.2], ['#5f7963', 0.5], ['#c3c7c9', 0.6], ['#6f5c4c', 1.6], ['#7b7f80', 1.5]];
const PAL_PUERTA = ['#8a5c3b', '#6a452c', '#4a7553', '#46698a', '#9a9c9e', '#7a3530', '#e2e0d8', '#38444b', '#5d3a2a'];
const C_GRIS = col('#a7a59d'), C_MADERA = col('#6e4c32'), C_OSCURO = col('#2a2724'), C_FIERRO = col('#5a3d2c'), C_TANQUE = col('#1f2221');
const C_LADR = col('#f4efe8');

function celdaVentana(k) { const i = k % 4, j = Math.floor(k / 4); return [i / 4 + 0.002, 1 - (j + 1) / 2 + 0.004, (i + 1) / 4 - 0.002, 1 - j / 2 - 0.004]; }
function celdaPuerta(k) { return [k / 4 + 0.003, 0.004, (k + 1) / 4 - 0.003, 0.996]; }
function celdaLetrero(k) { const i = k % 2, j = Math.floor(k / 2); return [i / 2 + 0.003, 1 - (j + 1) / 4 + 0.006, (i + 1) / 2 - 0.003, 1 - j / 4 - 0.006]; }

/** Muro plano P->Q (2D) con vanos rehundidos; 'out' = normal exterior 2D. u de los vanos medido desde P */
function fachada(gbM, J, P, Q, out, y0, y1, vanos, colM, zoc = null) {
  const L = len(sub(Q, P));
  if (L < 0.02 || y1 - y0 < 0.01) return;
  vanos = vanos.filter((o) => o.u0 > 0.12 && o.u1 < L - 0.12 && o.v0 >= y0 - 1e-6 && o.v1 <= y1 - 0.05);
  const dir = nrm(sub(Q, P));
  const X = (u, y, off = 0) => [P[0] + dir[0] * u + out[0] * off, y, P[1] + dir[1] * u + out[1] * off];
  const hacia = [out[0], 0, out[1]];
  const uB = dot(P, dir);
  const ys = new Set([y0, y1]);
  if (zoc && zoc.h > y0 && zoc.h < y1) ys.add(zoc.h);
  for (const o of vanos) { if (o.v0 > y0 && o.v0 < y1) ys.add(o.v0); if (o.v1 > y0 && o.v1 < y1) ys.add(o.v1); }
  const yl = [...ys].sort((a, b) => a - b);
  for (let k = 0; k < yl.length - 1; k++) {
    const ya = yl[k], yb = yl[k + 1];
    if (yb - ya < 1e-4) continue;
    const ym = (ya + yb) / 2;
    const huecos = vanos.filter((o) => o.v0 < ym && o.v1 > ym).map((o) => [o.u0, o.u1]).sort((p, q) => p[0] - q[0]);
    const c = zoc && ym < zoc.h ? zoc.col : colM;
    let uc = 0;
    const tramo = (ua, ub) => {
      if (ub - ua < 1e-4) return;
      gbM.poly([X(ua, ya), X(ub, ya), X(ub, yb), X(ua, yb)], [[uB + ua, ya], [uB + ub, ya], [uB + ub, yb], [uB + ua, yb]], c, hacia);
    };
    for (const [h0, h1] of huecos) { tramo(uc, h0); uc = Math.max(uc, h1); }
    tramo(uc, L);
  }
  const right = [out[1], -out[0]];
  const espejo = dot(dir, right) < 0;
  for (const o of vanos) {
    const p = o.prof ?? 0.12;
    const cr = escalar(o.v0 < (zoc ? zoc.h : -9) ? zoc.col : colM, 0.86);
    gbM.poly([X(o.u0, o.v0, 0), X(o.u0, o.v0, -p), X(o.u0, o.v1, -p), X(o.u0, o.v1, 0)], [[0, o.v0], [p, o.v0], [p, o.v1], [0, o.v1]], cr, [dir[0], 0, dir[1]]);
    gbM.poly([X(o.u1, o.v0, 0), X(o.u1, o.v0, -p), X(o.u1, o.v1, -p), X(o.u1, o.v1, 0)], [[0, o.v0], [p, o.v0], [p, o.v1], [0, o.v1]], cr, [-dir[0], 0, -dir[1]]);
    gbM.poly([X(o.u0, o.v1, 0), X(o.u1, o.v1, 0), X(o.u1, o.v1, -p), X(o.u0, o.v1, -p)], [[o.u0, 0], [o.u1, 0], [o.u1, p], [o.u0, p]], escalar(cr, 0.8), ABAJO);
    gbM.poly([X(o.u0, o.v0, 0), X(o.u1, o.v0, 0), X(o.u1, o.v0, -p), X(o.u0, o.v0, -p)], [[o.u0, 0], [o.u1, 0], [o.u1, p], [o.u0, p]], cr, ARRIBA);
    const pts = [X(o.u0, o.v0, -p), X(o.u1, o.v0, -p), X(o.u1, o.v1, -p), X(o.u0, o.v1, -p)];
    if (o.tipo === 'hueco') { J.oscuro.poly(pts, null, C_OSCURO, hacia); continue; }
    const cel = o.tipo === 'ventana' ? celdaVentana(o.celda) : celdaPuerta(o.celda);
    const [cu0, cv0, cu1, cv1] = cel;
    const ua = espejo ? cu1 : cu0, ub = espejo ? cu0 : cu1;
    (o.tipo === 'ventana' ? J.ventana : J.puerta).poly(pts, [[ua, cv0], [ub, cv0], [ub, cv1], [ua, cv1]], o.tinte || [1, 1, 1], hacia);
    if (o.alfeizar) J.muro.cajaSeg(X(o.u0 - 0.06, o.v0 - 0.035, 0.035), X(o.u1 + 0.06, o.v0 - 0.035, 0.035), 0.13, 0.07, escalar(colM, 0.92));
    if (o.letrero !== undefined && o.letrero >= 0) {
      const [lu0, lv0, lu1, lv1] = celdaLetrero(o.letrero);
      const la = espejo ? lu1 : lu0, lb = espejo ? lu0 : lu1;
      const ys0 = o.v1 + 0.12, ys1 = Math.min(o.v1 + 0.7, o.techoLetrero ?? 99);
      if (ys1 - ys0 > 0.35) J.letrero.poly([X(o.u0 - 0.15, ys0, 0.04), X(o.u1 + 0.15, ys0, 0.04), X(o.u1 + 0.15, ys1, 0.04), X(o.u0 - 0.15, ys1, 0.04)],
        [[la, lv0], [lb, lv0], [lb, lv1], [la, lv1]], [1, 1, 1], hacia);
    }
  }
}
/** Panel plano (ventana/puerta) apenas delante del muro (detalle medio) */
function panelPlano(J, P, Q, out, u0, u1, v0, v1, tipo, celda, tinte) {
  const dir = nrm(sub(Q, P));
  const X = (u, y) => [P[0] + dir[0] * u + out[0] * 0.015, y, P[1] + dir[1] * u + out[1] * 0.015];
  const right = [out[1], -out[0]];
  const espejo = dot(dir, right) < 0;
  const [cu0, cv0, cu1, cv1] = tipo === 'ventana' ? celdaVentana(celda) : celdaPuerta(celda);
  const ua = espejo ? cu1 : cu0, ub = espejo ? cu0 : cu1;
  (tipo === 'ventana' ? J.ventana : J.puerta).poly([X(u0, v0), X(u1, v0), X(u1, v1), X(u0, v1)], [[ua, cv0], [ub, cv0], [ub, cv1], [ua, cv1]], tinte || [1, 1, 1], [out[0], 0, out[1]]);
}
/** Muro con coronación variable (gablete): rectángulo hasta el mínimo + trapecios encima */
function muroPerfil(gbM, J, E0, E1, out, y0, alturas, colM, vanos = [], zoc = null) {
  // alturas: [[t (0..1 a lo largo de E0->E1), y], ...] ordenado por t
  const L = len(sub(E1, E0));
  const ymin = Math.min(...alturas.map((a) => a[1]));
  fachada(gbM, J, E0, E1, out, y0, ymin, vanos, colM, zoc);
  const dir = nrm(sub(E1, E0)); const uB = dot(E0, dir);
  for (let k = 0; k < alturas.length - 1; k++) {
    const [ta, ya] = alturas[k], [tb, yb] = alturas[k + 1];
    if (ya - ymin < 1e-3 && yb - ymin < 1e-3) continue;
    const A = lerp2(E0, E1, ta), B = lerp2(E0, E1, tb);
    const pts = [[A[0], ymin, A[1]], [B[0], ymin, B[1]], [B[0], yb, B[1]], [A[0], ya, A[1]]];
    const uv = [[uB + ta * L, ymin], [uB + tb * L, ymin], [uB + tb * L, yb], [uB + ta * L, ya]];
    if (yb - ymin < 1e-3) { pts.splice(2, 1); uv.splice(2, 1); } else if (ya - ymin < 1e-3) { pts.splice(3, 1); uv.splice(3, 1); }
    gbM.poly(pts, uv, colM, [out[0], 0, out[1]]);
  }
}
/** Plancha de techo (4 esquinas 3D de la cara inferior) con espesor */
function techoPlano(gb, c4, esp, colr, bordes = true, colInf = null) {
  const top = c4.map((p) => [p[0], p[1] + esp, p[2]]);
  const e = nrm3([c4[1][0] - c4[0][0], c4[1][1] - c4[0][1], c4[1][2] - c4[0][2]]);
  const s0 = [c4[3][0] - c4[0][0], c4[3][1] - c4[0][1], c4[3][2] - c4[0][2]];
  const k0 = s0[0] * e[0] + s0[1] * e[1] + s0[2] * e[2];
  const sl = nrm3([s0[0] - e[0] * k0, s0[1] - e[1] * k0, s0[2] - e[2] * k0]);
  const uv = c4.map((p) => { const d = [p[0] - c4[0][0], p[1] - c4[0][1], p[2] - c4[0][2]]; return [d[0] * e[0] + d[1] * e[1] + d[2] * e[2], d[0] * sl[0] + d[1] * sl[1] + d[2] * sl[2]]; });
  gb.poly(top, uv, colr, ARRIBA);
  if (colInf) gb.poly(c4, uv, colInf, ABAJO);
  if (bordes) {
    const cx = (c4[0][0] + c4[2][0]) / 2, cz = (c4[0][2] + c4[2][2]) / 2;
    for (let i = 0; i < 4; i++) {
      const a = c4[i], b = c4[(i + 1) % 4], ta = top[i], tb = top[(i + 1) % 4];
      const mx = (a[0] + b[0]) / 2 - cx, mz = (a[2] + b[2]) / 2 - cz;
      gb.poly([a, b, tb, ta], [[0, 0], [1, 0], [1, esp], [0, esp]], escalar(colr, 0.7), [mx, 0, mz]);
    }
  }
}
function tanque(J, P, y, rnd) {
  const g = tanque.geo || (tanque.geo = new THREE.CylinderGeometry(0.55, 0.55, 1.2, 12, 1, false));
  const m = new THREE.Matrix4().makeTranslation(P[0], y + 0.25 + 0.6, P[1]);
  J.oscuro.geo(g, m, rnd() < 0.85 ? C_TANQUE : col('#3d6c9e'));
  J.muro.prisma([[P[0] - 0.6, P[1] - 0.6], [P[0] + 0.6, P[1] - 0.6], [P[0] + 0.6, P[1] + 0.6], [P[0] - 0.6, P[1] + 0.6]], y, y + 0.25, C_GRIS);
}
function fierros(J, P, y, alto, rnd, columna = true) {
  if (columna) J.muro.prisma([[P[0] - 0.13, P[1] - 0.13], [P[0] + 0.13, P[1] - 0.13], [P[0] + 0.13, P[1] + 0.13], [P[0] - 0.13, P[1] + 0.13]], y, y + 0.12, C_GRIS);
  for (const [dx, dz] of [[-0.07, -0.07], [0.07, -0.07], [0.07, 0.07], [-0.07, 0.07]]) {
    const h = alto * (0.85 + rnd() * 0.3), inc = (rnd() - 0.5) * 0.12;
    J.oscuro.cajaSeg([P[0] + dx, y, P[1] + dz], [P[0] + dx + inc, y + h, P[1] + dz + inc * 0.5], 0.014, 0.014, C_FIERRO, [1, 0, 0], true);
  }
}

/** Especificación aleatoria de una casa */
function especCasa(rnd, o) {
  const h = { base: o.base ?? Y_VEREDA, kL: o.kL || 0, kR: o.kR || 0, fachIzq: !!o.fachIzq, fachDer: !!o.fachDer, frente: o.frente !== false, lod: o.lod };
  const cerca = o.distLote < 25;
  const tope = o.bajo ? 5.2 : cerca ? 6.6 : 7.0;
  let pisos = rnd() < (o.comercial ? 0.55 : 0.4) ? 2 : 1;
  if (o.posterior) pisos = rnd() < 0.35 ? 2 : 1;
  if (o.bajo) pisos = 1;
  h.hp1 = h.base + 2.65 + rnd() * 0.45;
  let alto2 = h.hp1 + 2.5 + rnd() * 0.3;
  const rr = rnd();
  let tipo;
  if (pisos === 1) tipo = rr < 0.32 ? 'dos_aguas' : rr < 0.58 ? 'agua_frente' : rr < 0.82 ? 'agua_atras' : 'losa';
  else if (pisos === 2) tipo = rr < 0.28 ? 'losa' : rr < 0.56 ? 'agua_atras' : rr < 0.74 ? 'dos_aguas' : rr < 0.88 ? 'agua_frente' : 'obra';
  else tipo = 'losa';
  if (o.posterior) tipo = rr < 0.5 ? 'agua_atras' : rr < 0.82 ? 'losa' : 'obra';
  if (tipo === 'obra') pisos = 1;
  h.pisos = pisos;
  h.tipo = tipo;
  h.pend = tipo === 'agua_atras' ? 0.06 + rnd() * 0.03 : 0.17 + rnd() * 0.12;
  h.eF = 0.5 + rnd() * 0.35; h.eB = 0.35;
  h.vol = pisos >= 2 && !h.kL && !h.kR && h.base > 0.1 && h.frente && rnd() < 0.3 ? 0.5 + rnd() * 0.2 : 0;
  h.parapeto = tipo === 'agua_atras' ? 0.3 + rnd() * 0.25 : tipo === 'losa' ? 0.3 + rnd() * 0.6 : 0;
  if (pisos === 2) alto2 = Math.min(alto2, tope - h.parapeto);
  h.alto = pisos === 1 ? h.hp1 : pisos === 2 ? alto2 : Math.min(alto2 + 2.6, tope - h.parapeto);
  h.d = o.d;
  // cumbreras bajo el tope
  const subida = tipo === 'dos_aguas' ? h.pend * (o.d + h.vol) / 2 : tipo === 'agua_frente' ? h.pend * (o.d + h.vol) : 0;
  if (h.alto + subida > tope) {
    const p = (tope - h.alto) / Math.max(1, tipo === 'dos_aguas' ? (o.d + h.vol) / 2 : o.d + h.vol);
    if (p >= 0.1) h.pend = p; else { h.tipo = 'agua_atras'; h.pend = 0.06; h.parapeto = 0.3; }
  }
  h.colMuro = col(elegir(rnd, PAL_MURO), 0.93 + rnd() * 0.07);
  h.colMuro2 = rnd() < 0.72 ? h.colMuro : col(elegir(rnd, PAL_MURO), 0.93 + rnd() * 0.07);
  h.ladrillo2 = pisos >= 2 && rnd() < 0.12;
  h.zocalo = rnd() < 0.8 ? { h: h.base + 0.7 + rnd() * 0.35, col: col(elegir(rnd, PAL_ZOC)) } : null;
  h.colTecho = col(elegirPeso(rnd, PAL_TECHO), 0.88 + rnd() * 0.14);
  h.colLosa = escalar(col(elegir(rnd, ['#a9a69e', '#9c998f', '#b0aca2', '#938f86'])), 0.92 + rnd() * 0.12);
  h.teja = (h.tipo === 'dos_aguas' || h.tipo === 'agua_frente') && pisos === 1 && rnd() < 0.2;
  if (h.teja) { h.colTecho = col('#ffffff', 0.85 + rnd() * 0.15); h.pend = Math.max(h.pend, 0.3); }
  h.celdaV = elegir(rnd, [0, 0, 1, 4, 4, 6, 3, 1]);
  h.celdaV2 = rnd() < 0.5 ? h.celdaV : elegir(rnd, [2, 5, 3, 0, 6]);
  h.celdaP = elegir(rnd, [0, 0, 1, 1, 3]);
  h.tintePuerta = col(elegir(rnd, PAL_PUERTA));
  h.tienda = o.comercial ? rnd() < 0.4 : rnd() < 0.1;
  h.letrero = h.tienda && rnd() < 0.65 ? Math.floor(rnd() * 8) : -1;
  h.tanque = tipo === 'losa' && rnd() < 0.65;
  h.fierros = (tipo === 'losa' && rnd() < 0.5) || tipo === 'obra';
  h.cornisa = pisos >= 2 && !h.vol && rnd() < 0.6;
  h.obra = tipo === 'obra' ? { hb: 0.9 + rnd() * 1.4, colH: 2.45 } : null;
  h.colCiego = rnd() < 0.35 ? null : col(elegir(rnd, ['#bdb8ad', '#c9c3b6', '#d8d0bf', '#b8b3a8']));
  return h;
}
function disponerVanos(h, L, rnd) {
  const base = h.base;
  const puerta = () => ({ tipo: 'puerta', ancho: 0.95 + rnd() * 0.25, alto: 2.15 + rnd() * 0.12 });
  const ventana = () => ({ tipo: 'ventana', ancho: 1.0 + rnd() * 0.6, alto: 1.1 + rnd() * 0.15, sill: 0.95 + rnd() * 0.1 });
  const enroll = () => ({ tipo: 'enrollable', ancho: 2.3 + rnd() * 0.7, alto: 2.4 });
  let els;
  if (L < 5.2) els = rnd() < 0.5 ? [puerta(), ventana()] : [ventana(), puerta()];
  else if (L < 8) {
    if (h.tienda) els = [enroll(), puerta()];
    else { const r = rnd(); els = r < 0.4 ? [ventana(), puerta(), ventana()] : r < 0.7 ? [puerta(), ventana(), ventana()] : [ventana(), ventana(), puerta()]; }
  } else if (h.tienda) els = [ventana(), enroll(), puerta()];
  else if (rnd() < 0.2) els = [{ tipo: 'enrollable', ancho: 2.6, alto: 2.3 }, puerta(), ventana()];
  else els = [ventana(), puerta(), ventana(), ventana()];
  const margen = 0.45;
  while (els.length > 1 && els.reduce((s, e) => s + e.ancho, 0) + margen * (els.length + 1) > L) {
    let i = -1; els.forEach((e, k) => { if (e.tipo === 'ventana') i = k; });
    if (i < 0) i = els.length - 1;
    els.splice(i, 1);
  }
  while (els.reduce((s, e) => s + e.ancho, 0) + margen * 2 > L && els[0].ancho > 0.7) els[0].ancho *= 0.85;
  const gap = (L - els.reduce((s, e) => s + e.ancho, 0)) / (els.length + 1);
  let a = gap; const p1 = [];
  for (const e of els) {
    const v0 = e.tipo === 'ventana' ? base + e.sill : base;
    const o = { u0: a, u1: a + e.ancho, v0, v1: v0 + e.alto, prof: e.tipo === 'ventana' ? 0.12 : 0.1 };
    if (e.tipo === 'ventana') Object.assign(o, { tipo: 'ventana', celda: h.celdaV, alfeizar: true });
    else if (e.tipo === 'enrollable') Object.assign(o, { tipo: 'puerta', celda: 2, tinte: escalar(h.tintePuerta, 0.4).map((c, i) => c + [0.55, 0.57, 0.6][i] * 0.6), letrero: h.letrero, techoLetrero: h.hp1 - 0.08 });
    else Object.assign(o, { tipo: 'puerta', celda: h.celdaP, tinte: h.tintePuerta });
    p1.push(o); a += e.ancho + gap;
  }
  const pisosSup = [];
  for (let piso = 2; piso <= h.pisos; piso++) {
    const yb = h.hp1 + (piso - 2) * 2.6;
    const fila = [];
    for (const o of p1) {
      const c = (o.u0 + o.u1) / 2, an = clamp(o.u1 - o.u0, 1.0, 1.7);
      const v0 = yb + 0.95, v1 = Math.min(yb + 2.15, h.alto - 0.25);
      if (v1 - v0 > 0.6) fila.push({ u0: c - an / 2, u1: c + an / 2, v0, v1, tipo: 'ventana', celda: h.celdaV2, prof: 0.12, alfeizar: true });
    }
    pisosSup.push(fila);
  }
  return { p1, pisosSup };
}
function ventanasLaterales(h, Lside, desde, rnd, pisos) {
  // ventanas en una fachada lateral (casa de esquina): las primeras dentro de los primeros ~8 m
  const out = [];
  const n = Lside > 7 ? 2 : Lside > 3.5 ? 1 : 0;
  for (let i = 0; i < n; i++) {
    const c = desde + (i + 0.5) * Math.min(Lside, 8) / n;
    const an = 1.1 + rnd() * 0.3;
    for (let p = 1; p <= pisos; p++) {
      const yb = p === 1 ? h.base : h.hp1 + (p - 2) * 2.6;
      const v0 = yb + 0.95, v1 = Math.min(yb + 2.1, (p === pisos ? h.alto : h.hp1 + (p - 1) * 2.6) - 0.25);
      if (v1 - v0 > 0.6) out.push({ piso: p, u0: c - an / 2, u1: c + an / 2, v0, v1, tipo: 'ventana', celda: p === 1 ? h.celdaV : h.celdaV2, prof: 0.12, alfeizar: true });
    }
  }
  return out;
}

/** Geometría de una casa en una fila. lod 0: detalle completo; 1: medio; 2: volumen simple */
function construirCasa(J, h, rnd) {
  if (h.ladrilloTodo) J = { ...J, muro: J.ladrillo };
  const { P0, u, v, a0, w, d } = h;
  const kL = h.kL || 0, kR = h.kR || 0;
  const W2 = (a, b) => [P0[0] + u[0] * a + v[0] * b, P0[1] + u[1] * a + v[1] * b];
  const W3 = (a, b, y) => { const p = W2(a, b); return [p[0], y, p[1]]; };
  const aL = (b) => a0 + kL * b, aR = (b) => a0 + w + kR * b;
  const lod = h.lod;
  const vol = lod === 0 ? h.vol || 0 : 0;
  const Y0 = (h.base ?? Y_VEREDA) - 0.6;
  const out = mul(v, -1);
  const tipo = h.tipo, pend = h.pend, alto = h.alto;
  const bF = -vol;
  const gbM2 = h.ladrillo2 ? J.ladrillo : J.muro;
  const cM = h.colMuro, cM2 = h.ladrillo2 ? C_LADR : h.colMuro2;
  const cCiego = h.colCiego;
  const gbCiego = cCiego ? J.muro : J.ladrillo;
  const colCiego = cCiego || C_LADR;
  // coronación de muros (cara inferior del techo) en función de b
  let yT;
  if (tipo === 'dos_aguas') yT = (b) => alto + pend * Math.min(b - bF, d - b);
  else if (tipo === 'agua_frente') yT = (b) => alto + pend * (b - bF);
  else if (tipo === 'agua_atras') yT = (b) => alto - pend * (b - bF);
  else yT = () => alto;
  const bm = (d + bF) / 2;
  const bs = (b0) => (tipo === 'dos_aguas' && bm > b0 + 0.05 ? [b0, bm, d] : [b0, d]);
  const piso1Top = h.pisos >= 2 ? h.hp1 : alto;

  // ------------------------------------------------ nivel 2: volumen simple
  if (lod === 2) {
    const c = h.colMuro;
    const prof = (izq) => {
      const aS = izq ? aL : aR;
      const E0 = W2(aS(0), 0), E1 = W2(aS(d), d);
      let o = nrm(perp(sub(E1, E0))); if (dot(o, u) * (izq ? -1 : 1) < 0) o = mul(o, -1);
      muroPerfil(J.muro, J, E0, E1, o, Y0, bs(0).map((b) => [b / d, yT(b)]), c);
    };
    fachada(J.muro, J, W2(aL(0), 0), W2(aR(0), 0), out, Y0, yT(0), [], c);
    fachada(J.muro, J, W2(aR(d), d), W2(aL(d), d), v, Y0, yT(d), [], escalar(c, 0.92));
    prof(true); prof(false);
    if (tipo === 'losa' || tipo === 'obra') J.losa.poly([W3(aL(0), 0, alto), W3(aR(0), 0, alto), W3(aR(d), d, alto), W3(aL(d), d, alto)], [W2(aL(0), 0), W2(aR(0), 0), W2(aR(d), d), W2(aL(d), d)], h.colLosa || C_GRIS, ARRIBA);
    else {
      const pl = tipo === 'dos_aguas' ? [[-0.3, bm], [bm, d + 0.3]] : [[-0.3, d + 0.3]];
      const yE = (b) => (tipo === 'dos_aguas' ? alto + pend * Math.min(b - bF, d - b) : yT(b));
      const ct = h.teja ? col('#c0806a') : h.colTecho;
      for (const [b0, b1] of pl) J.calamina.poly([W3(aL(b0), b0, yE(b0)), W3(aR(b0), b0, yE(b0)), W3(aR(b1), b1, yE(b1)), W3(aL(b1), b1, yE(b1))],
        [[0, 0], [w, 0], [w, b1 - b0], [0, b1 - b0]], ct, ARRIBA);
    }
    return;
  }

  // ------------------------------------------------ fachada principal
  const vanos = h.frente ? disponerVanos(h, w, rnd) : { p1: [], pisosSup: [] };
  const Pf = W2(aL(0), 0), Qf = W2(aR(0), 0);
  if (lod === 0) {
    if (h.frente) fachada(J.muro, J, Pf, Qf, out, Y0, piso1Top, vanos.p1, cM, h.zocalo);
    else fachada(gbCiego, J, Pf, Qf, out, Y0, piso1Top, [], colCiego);
  } else {
    // nivel 1: bandas de color + paneles planos
    const zh = h.zocalo && h.frente ? h.zocalo.h : Y0;
    if (h.zocalo && h.frente) fachada(J.muro, J, Pf, Qf, out, Y0, zh, [], h.zocalo.col);
    fachada(h.frente ? J.muro : gbCiego, J, Pf, Qf, out, zh, piso1Top, [], h.frente ? cM : colCiego);
    for (const o of vanos.p1) panelPlano(J, Pf, Qf, out, o.u0, o.u1, o.v0, o.v1, o.tipo, o.tipo === 'ventana' ? 7 : o.celda, o.tinte);
  }
  if (h.pisos >= 2) {
    const Pu = W2(aL(bF), bF), Qu = W2(aR(bF), bF);
    const gbU = h.frente ? gbM2 : gbCiego, cU = h.frente ? cM2 : colCiego;
    if (lod === 0) {
      const todos = vanos.pisosSup.flat();
      fachada(gbU, J, Pu, Qu, out, h.hp1, alto, todos, cU);
      if (vol > 0) {
        J.muro.prisma([W2(a0, bF), W2(a0 + w, bF), W2(a0 + w, 0), W2(a0, 0)], h.hp1 - 0.18, h.hp1 + 0.02, escalar(cM2, 0.95), { fondo: true });
        for (const [aa, s] of [[a0, -1], [a0 + w, 1]]) {
          const E0 = W2(aa, bF), E1 = W2(aa, 0);
          J.muro.poly([[E0[0], h.hp1, E0[1]], [E1[0], h.hp1, E1[1]], [E1[0], yT(0), E1[1]], [E0[0], yT(bF), E0[1]]], null, escalar(cM2, 0.9), [u[0] * s, 0, u[1] * s]);
        }
      } else if (h.cornisa) J.muro.cajaSeg(W3(aL(0), -0.05, h.hp1), W3(aR(0), -0.05, h.hp1), 0.1, 0.14, escalar(cM, 0.85));
    } else {
      fachada(gbU, J, Pf, Qf, out, h.hp1, alto, [], cU);
      for (const o of vanos.pisosSup.flat()) panelPlano(J, Pf, Qf, out, o.u0, o.u1, o.v0, o.v1, 'ventana', 7, null);
    }
  }
  // ------------------------------------------------ costados
  for (const izq of [true, false]) {
    const aS = izq ? aL : aR;
    const E0 = W2(aS(0), 0), E1 = W2(aS(d), d);
    let o = nrm(perp(sub(E1, E0))); if (dot(o, u) * (izq ? -1 : 1) < 0) o = mul(o, -1);
    const fach = izq ? h.fachIzq : h.fachDer;
    const Ls = len(sub(E1, E0));
    const gbS = fach ? J.muro : (h.pegado && izq ? gbCiego : J.muro);
    const cS = fach ? cM : (h.pegado && izq ? colCiego : escalar(cM, 0.93));
    // tramo inferior
    if (h.pisos >= 2) {
      const vl = fach && lod === 0 ? ventanasLaterales(h, Ls, 0.8, rnd, 1) : [];
      fachada(gbS, J, E0, E1, o, Y0, h.hp1, vl, cS, fach ? h.zocalo : null);
      const E0u = W2(aS(bF), bF);
      const vl2 = fach && lod === 0 ? ventanasLaterales(h, Ls, 0.8, rnd, h.pisos).filter((x) => x.piso >= 2) : [];
      const top = bs(bF).map((b) => [(b - bF) / (d - bF), yT(b)]);
      if (tipo === 'agua_atras' && fach) top.forEach((t) => { t[1] = alto; });
      muroPerfil(fach ? gbM2 : gbS, J, E0u, E1, o, h.hp1, top, fach ? cM2 : cS, vl2.map((x) => ({ ...x, u0: x.u0 + vol, u1: x.u1 + vol })));
    } else {
      const vl = fach && lod === 0 ? ventanasLaterales(h, Ls, 0.8, rnd, 1) : [];
      const top = bs(0).map((b) => [b / d, yT(b)]);
      if ((tipo === 'agua_atras' || tipo === 'losa') && fach) top.forEach((t) => { t[1] = alto; });
      muroPerfil(gbS, J, E0, E1, o, Y0, top, cS, vl, fach ? h.zocalo : null);
    }
    if (fach && lod === 1) for (const x of ventanasLaterales(h, Ls, 0.8, rnd, h.pisos)) panelPlano(J, E0, E1, o, x.u0, x.u1, x.v0, x.v1, 'ventana', 7, null);
  }
  // ------------------------------------------------ fondo
  {
    const E0 = W2(aR(d), d), E1 = W2(aL(d), d);
    const Lb = len(sub(E1, E0));
    fachada(J.muro, J, E0, E1, v, Y0, yT(d), [], escalar(cM, 0.9));
    if (Lb > 3) {
      const c = Lb * (0.3 + rnd() * 0.4);
      panelPlano(J, E0, E1, v, c - 0.5, c + 0.5, h.base + 1.0, h.base + 2.0, 'ventana', 7, null);
      if (h.pisos >= 2) panelPlano(J, E0, E1, v, c - 0.5, c + 0.5, h.hp1 + 0.95, h.hp1 + 1.95, 'ventana', 7, null);
      if (Lb > 5) panelPlano(J, E0, E1, v, Lb * 0.75, Lb * 0.75 + 0.9, h.base, h.base + 2.05, 'puerta', 1, escalar(h.tintePuerta, 0.9));
    }
  }
  // ------------------------------------------------ techo
  const ovL = h.fachIzq ? 0.3 : 0, ovR = h.fachDer ? 0.3 : 0;
  if (tipo === 'dos_aguas' || tipo === 'agua_frente' || tipo === 'agua_atras') {
    const gbT = h.teja ? J.teja : J.calamina, esp = h.teja ? 0.07 : 0.045;
    const bFe = tipo === 'agua_atras' ? bF + 0.16 : bF - h.eF;
    const bBe = d + h.eB;
    const yE = (b) => (tipo === 'dos_aguas' ? alto + pend * Math.min(b - bF, d - b) : yT(b));
    const planos = tipo === 'dos_aguas' ? [[bFe, bm], [bm, bBe]] : [[bFe, bBe]];
    const cInf = lod === 0 ? escalar(h.teja ? col('#8a6a52') : col('#8c8f90'), 0.75) : null;
    for (const [b0, b1] of planos) {
      techoPlano(gbT, [W3(aL(b0) - ovL, b0, yE(b0)), W3(aR(b0) + ovR, b0, yE(b0)), W3(aR(b1) + ovR, b1, yE(b1)), W3(aL(b1) - ovL, b1, yE(b1))], esp, h.colTecho, lod === 0, cInf);
    }
    if (tipo === 'dos_aguas') gbT.cajaSeg(W3(aL(bm) - ovL, bm, yE(bm) + esp + 0.02), W3(aR(bm) + ovR, bm, yE(bm) + esp + 0.02), 0.34, 0.05, escalar(h.colTecho, 0.85));
    if (lod === 0 && tipo !== 'agua_atras' && h.frente) {
      J.muro.cajaSeg(W3(aL(bFe) - ovL, bFe - 0.012, yE(bFe) + esp - 0.08), W3(aR(bFe) + ovR, bFe - 0.012, yE(bFe) + esp - 0.08), 0.03, 0.17, C_MADERA);
      for (let a = aL(0) + 0.35; a < aR(0) - 0.15; a += 0.95) {
        J.muro.cajaSeg(W3(a, bF, yE(bF) - 0.065), W3(a, bFe + 0.05, yE(bFe + 0.05) - 0.065), 0.07, 0.11, C_MADERA);
      }
    }
  }
  if (tipo === 'agua_atras' || tipo === 'losa' || tipo === 'obra') {
    if (tipo !== 'agua_atras') J.losa.poly([W3(aL(bF), bF, alto), W3(aR(bF), bF, alto), W3(aR(d), d, alto), W3(aL(d), d, alto)], [W2(aL(bF), bF), W2(aR(bF), bF), W2(aR(d), d), W2(aL(d), d)], h.colLosa || C_GRIS, ARRIBA);
    const pp = h.parapeto || (tipo === 'obra' ? 0.12 : 0);
    const gbP = h.frente ? (h.pisos >= 2 ? gbM2 : J.muro) : gbCiego;
    const cP = h.frente ? (h.pisos >= 2 ? cM2 : cM) : colCiego;
    const parapeto = (Pa, Pb, hacia, y0, y1, gb, c) => {
      const inw = mul(hacia, -0.15);
      gb.prisma([Pa, Pb, add(Pb, inw), add(Pa, inw)], y0, y1, c, { colTapa: escalar(c, 0.9) });
    };
    if (pp > 0) parapeto(W2(aL(bF), bF), W2(aR(bF), bF), out, alto, alto + pp, gbP, cP);
    if (lod === 0 && tipo === 'losa') {
      for (const izq of [true, false]) {
        const aS = izq ? aL : aR;
        const E0 = W2(aS(bF + 0.15), bF + 0.15), E1 = W2(aS(d), d);
        let o = nrm(perp(sub(E1, E0))); if (dot(o, u) * (izq ? -1 : 1) < 0) o = mul(o, -1);
        const fach = izq ? h.fachIzq : h.fachDer;
        parapeto(E0, E1, o, alto, alto + (fach ? pp : 0.22), J.muro, fach ? cP : escalar(cM, 0.9));
      }
    } else if (tipo === 'agua_atras') {
      for (const izq of [true, false]) if (izq ? h.fachIzq : h.fachDer) {
        const aS = izq ? aL : aR;
        const E0 = W2(aS(bF + 0.15), bF + 0.15), E1 = W2(aS(d), d);
        let o = nrm(perp(sub(E1, E0))); if (dot(o, u) * (izq ? -1 : 1) < 0) o = mul(o, -1);
        parapeto(E0, E1, o, alto, alto + pp, J.muro, cM);
      }
    }
    if (h.tanque && w > 3.2) tanque(J, W2(aL(d) + 1.0 + rnd() * Math.max(0.1, w - 2.6), d - 1.2), alto, rnd);
    if (h.fierros && lod === 0 && tipo === 'losa') {
      for (const [a, b] of [[aL(bF) + 0.15, bF + 0.15], [aR(bF) - 0.15, bF + 0.15], [aL(d) + 0.15, d - 0.15], [aR(d) - 0.15, d - 0.15]]) fierros(J, W2(a, b), alto, 0.75, rnd);
    }
  }
  // ------------------------------------------------ segundo piso en construcción
  if (tipo === 'obra') {
    const y0 = alto, hc = h.obra.colH;
    const nCol = Math.max(2, Math.ceil(w / 3.6) + 1);
    const cols = [];
    for (let i = 0; i < nCol; i++) { const t = i / (nCol - 1); cols.push([lerp(aL(0) + 0.13, aR(0) - 0.13, t), 0.13]); }
    cols.push([aL(d) + 0.13, d - 0.13], [aR(d) - 0.13, d - 0.13]);
    if (d > 7) cols.push([aL(d / 2) + 0.13, d / 2], [aR(d / 2) - 0.13, d / 2]);
    for (const [a, b] of cols) {
      const P = W2(a, b);
      J.muro.prisma([[P[0] - 0.125, P[1] - 0.125], [P[0] + 0.125, P[1] - 0.125], [P[0] + 0.125, P[1] + 0.125], [P[0] - 0.125, P[1] + 0.125]], y0, y0 + hc, escalar(C_GRIS, 0.92));
      if (lod === 0) fierros(J, P, y0 + hc, 0.7, rnd, false);
    }
    // muros de ladrillo a medio levantar entre columnas del frente
    for (let i = 0; i < nCol - 1; i++) {
      const a1 = cols[i][0] + 0.125, a2 = cols[i + 1][0] - 0.125;
      if (a2 - a1 < 0.3) continue;
      const hb = rnd() < 0.3 ? hc - 0.15 : h.obra.hb * (0.6 + rnd() * 0.5);
      J.ladrillo.prisma([W2(a1, 0), W2(a2, 0), W2(a2, 0.13), W2(a1, 0.13)], y0, y0 + Math.min(hb, hc), C_LADR);
    }
    for (const izq of [true, false]) {
      const aS = izq ? aL : aR, sgn = izq ? 1 : -1;
      const L2 = d * (0.35 + rnd() * 0.5);
      J.ladrillo.prisma([W2(aS(0.26) + 0.0, 0.26), W2(aS(L2), L2), W2(aS(L2) + 0.13 * sgn, L2), W2(aS(0.26) + 0.13 * sgn, 0.26)], y0, y0 + h.obra.hb * (0.5 + rnd() * 0.5), C_LADR);
    }
    if (lod === 0 && rnd() < 0.6) { const P = W2(lerp(aL(d * 0.6), aR(d * 0.6), 0.5), d * 0.6); J.ladrillo.prisma([[P[0] - 0.4, P[1] - 0.3], [P[0] + 0.4, P[1] - 0.3], [P[0] + 0.4, P[1] + 0.3], [P[0] - 0.4, P[1] + 0.3]], y0, y0 + 0.45, C_LADR); }
  }
}

// ================================================================ planificación de filas de casas
function lineaPerpendicular(m, s) { return { p: m.p(s, 0), d: m.n }; }
function planificarFilas(ctx) {
  const { calles, FJ, FL, B, C } = ctx;
  const filas = [];
  const famJ = calles.filter((k) => k.m === FJ), famL = calles.filter((k) => k.m === FL);
  const lat = calles[1];
  // filas paralelas al jirón: son dueñas de las esquinas (fachada lateral sobre la calle transversal)
  for (const k of famJ) for (const lado of [-1, 1]) {
    const eP = k.c + lado * k.half;
    const sDe = (oL) => FJ.s(cruce(FJ, eP, FL, oL));
    const lim = [sDe(LIM_L[0]), sDe(LIM_L[1])].sort((p, q) => p - q);
    const cortes = [];
    for (const y of famL) {
      const sy = FL.s(cruce(FL, y.c, FJ, eP));
      if (sy < y.sIni - 0.5 || sy > y.s1) continue;
      const s1 = sDe(y.c - y.half), s2 = sDe(y.c + y.half);
      cortes.push(s1 < s2 ? { a: s1, b: s2, la: FL.linea(y.c - y.half), lb: FL.linea(y.c + y.half) } : { a: s2, b: s1, la: FL.linea(y.c + y.half), lb: FL.linea(y.c - y.half) });
    }
    cortes.sort((p, q) => p.a - q.a);
    let sI = lim[0], lI = lineaPerpendicular(FJ, lim[0]), eI = false;
    const segs = [];
    for (const c of cortes) {
      if (c.b < lim[0] || c.a > lim[1]) continue;
      if (c.a > sI + 3) segs.push({ sI, sF: c.a, lI, lF: c.la, eI, eF: true });
      sI = c.b; lI = c.lb; eI = true;
    }
    if (lim[1] > sI + 3) segs.push({ sI, sF: lim[1], lI, lF: lineaPerpendicular(FJ, lim[1]), eI, eF: false });
    for (const sg of segs) {
      const f = { calle: k, m: FJ, eP, sigma: lado, ...sg, comercial: k.id === 'jr' };
      if (k.id === 'jr' && lado === -1 && sg.eF && Math.abs(sg.sF - FJ.s(cruce(FJ, eP, FL, lat.c + lat.half))) < 0.5) {
        // esquina frente al portón de ingreso: jardín cercado (deja libre la toma de cámara hacia P-1)
        f.jardinFin = 16;
      }
      if (k.id === 'jr' && lado === -1 && sg.sI < 15 && sg.sF > 15) {
        // frente del lote sobre el jirón: la fila empieza en B, pegada al muro B-C del lote
        f.sI = FJ.s(B); f.lI = { p: B, d: nrm(sub(C, B)) }; f.eI = false; f.pegado = true; f.fondoMax = FONDO_ESQ;
      }
      filas.push(f);
    }
  }
  // filas paralelas a la calle lateral: empiezan detrás de las casas de esquina
  for (const k of famL) for (const lado of [-1, 1]) {
    const eP = k.c + lado * k.half;
    const sDe = (oJ) => FL.s(cruce(FL, eP, FJ, oJ));
    const lim = [sDe(LIM_J[0]), sDe(LIM_J[1])].sort((p, q) => p - q);
    if (k.id === 'lat') lim[0] = Math.max(lim[0], sDe(-FONDO_ESQ));
    const cortes = [];
    for (const y of famJ) {
      const sy = FJ.s(cruce(FJ, y.c, FL, eP));
      if (sy < y.sIni || sy > y.s1) continue;
      const sk = sDe(y.c);
      if (sk < k.sIni - 0.5 || sk > k.s1) continue;
      const s1 = sDe(y.c - y.half - FONDO_ESQ), s2 = sDe(y.c + y.half + FONDO_ESQ);
      const l1 = FJ.linea(y.c - y.half - FONDO_ESQ), l2 = FJ.linea(y.c + y.half + FONDO_ESQ);
      cortes.push(s1 < s2 ? { a: s1, b: s2, la: l1, lb: l2 } : { a: s2, b: s1, la: l2, lb: l1 });
    }
    cortes.sort((p, q) => p.a - q.a);
    let sI = lim[0], lI = k.id === 'lat' ? FJ.linea(-FONDO_ESQ) : lineaPerpendicular(FL, lim[0]);
    const segs = [];
    for (const c of cortes) {
      if (c.b < lim[0] || c.a > lim[1]) continue;
      if (c.a > sI + 3) segs.push({ sI, sF: c.a, lI, lF: c.la });
      sI = c.b; lI = c.lb;
    }
    if (lim[1] > sI + 3) segs.push({ sI, sF: lim[1], lI, lF: lineaPerpendicular(FL, lim[1]) });
    for (const sg of segs) {
      const f = { calle: k, m: FL, eP, sigma: lado, ...sg, eI: false, eF: false, comercial: false };
      if (k.id === 'lat' && lado === 1 && Math.abs(sg.sI - lim[0]) < 0.01) f.fachIni = true;   // da al jardín de la esquina
      if (k.id === 'lat' && lado === -1 && sg.sI < 25) {
        // frente del lote sobre la lateral: lote (0-20 m) y patio verde; la fila empieza al este del patio
        if (ctx.patio) {
          const pe = ctx.patio.slice().sort((p, q) => FL.s(q) - FL.s(p));
          const a = pe[0], b = pe[1];
          f.sI = Math.max(FL.s(a), FL.s(b)); f.lI = { p: a, d: nrm(sub(b, a)) };
        } else { f.sI = FL.s(ctx.D) + 14; f.lI = lineaPerpendicular(FL, f.sI); }
        f.fondoMax = 13;
      }
      filas.push(f);
    }
  }
  return filas;
}

function generarFila(f, ctx, reg, rnd, casas, baldios, jardines = []) {
  const { m, eP, sigma } = f;
  const prop = m.linea(eP);
  const P0 = interLineas(prop, f.lI), PF = interLineas(prop, f.lF);
  if (!P0 || !PF) return;
  const u = nrm(sub(PF, P0)), v = mul(m.n, sigma);
  const L = len(sub(PF, P0));
  if (L < 3) return;
  const pend = (lin) => { let dd = lin.d; if (dot(dd, v) < 0) dd = mul(dd, -1); return dot(dd, u) / dot(dd, v); };
  const kIni = pend(f.lI), kFin = pend(f.lF);
  const Lc = f.jardinFin ? L - f.jardinFin : L;
  if (f.jardinFin) jardines.push({ P0, u, v, a0: Lc, w: f.jardinFin, d: FONDO_ESQ, kR: kFin });
  let a = 0;
  let primera = true;
  while (a < Lc - 2.5) {
    let w = rnd() < 0.12 ? 4.5 + rnd() * 1.2 : rnd() < 0.15 ? 10.5 + rnd() * 3 : 6 + rnd() * 4;
    if (primera && f.eI && kIni > 0.3) w = Math.max(w, 9 + kIni * 4);
    if (Lc - a - w < 4.5) w = Lc - a;
    const ultima = a + w >= Lc - 0.01;
    const kL = primera ? kIni : 0, kR = ultima && !f.jardinFin ? kFin : 0;
    const centro2 = add(add(P0, mul(u, a + w / 2)), mul(v, 6));
    const distC = len(sub(centro2, ctx.centro));
    const distLote = Math.max(0, distPoly(centro2, ctx.lote));
    const lod = distC < R_CERCA ? 0 : distC < R_MEDIO ? 1 : 2;
    const esquina = (primera && f.eI) || (ultima && f.eF && !f.jardinFin);
    let d = esquina ? FONDO_ESQ : 10 + rnd() * 8;
    if (f.fondoMax) d = Math.min(d, f.fondoMax);
    if (distLote < 25) d = Math.min(d, FONDO_ESQ);
    // ancho trasero mínimo (esquinas agudas)
    while (w + (kR - kL) * d < 3 && d > 5) d -= 1;
    const pBaldio = distLote < 30 ? 0.03 : 0.07 + 0.25 * suave((distC - 120) / 160);
    const huella = (dd) => [add(P0, mul(u, a)), add(P0, mul(u, a + w)), add(add(P0, mul(u, a + w + kR * dd)), mul(v, dd)), add(add(P0, mul(u, a + kL * dd)), mul(v, dd))];
    let ok = false;
    const baldio = !(primera && f.pegado) && !esquina && rnd() < pBaldio;
    if (w > 2.5 && !baldio) {
      for (let intento = 0; intento < 4 && !ok; intento++) {
        const H = huella(d);
        const chk = encoger(H, 0.08);
        const choque = reg.choca(chk) || chk.some((p) => enCalle(ctx, p, -0.05)) || enCalle(ctx, centroide(chk), -0.05);
        if (!choque) ok = true; else d *= 0.72;
        if (d < 4.5) break;
      }
    }
    if (ok) {
      const H = huella(d);
      const spec = especCasa(rnd, { distLote, comercial: f.comercial, lod, kL, kR, d, fachIzq: primera && (f.eI || f.fachIni), fachDer: ultima && (f.eF || f.jardinFin), bajo: distLote < 7 });
      Object.assign(spec, { P0, u, v, a0: a, w, d, kL, kR, pegado: primera && f.pegado, calle: f.calle.id, distC });
      if (primera && f.pegado) spec.fachIzq = false;
      reg.agregar(H, 'casa', spec);
      casas.push(spec);
      // construcción posterior (cocina, depósito, cuartos) en el patio
      if (lod <= 1 && !esquina && rnd() < 0.45 && w > 3.6) {
        const gap = 0.8 + rnd() * 3, dd = 3 + rnd() * 4, ww = Math.min(w - 1.0, 3 + rnd() * 4);
        const a1 = a + 0.5 + rnd() * Math.max(0, w - 1 - ww), b1 = d + gap;
        const Q0 = add(P0, mul(v, b1));
        const Hb = [add(Q0, mul(u, a1)), add(Q0, mul(u, a1 + ww)), add(add(Q0, mul(u, a1 + ww)), mul(v, dd)), add(add(Q0, mul(u, a1)), mul(v, dd))];
        const chk = encoger(Hb, 0.1);
        if (!reg.choca(chk) && !chk.some((p) => enCalle(ctx, p, 0.5)) && distPoly(centroide(Hb), ctx.lote) > 4) {
          const sp = especCasa(rnd, { distLote: 99, lod: 1, d: dd, base: 0 });
          Object.assign(sp, { P0: Q0, u, v, a0: a1, w: ww, d: dd, kL: 0, kR: 0, pisos: 1, tipo: rnd() < 0.72 ? 'agua_frente' : 'losa',
            vol: 0, tienda: false, letrero: -1, tanque: false, fierros: false, cornisa: false, obra: null, fachIzq: false, fachDer: false,
            lod: 1, distC: len(sub(centroide(Hb), ctx.centro)), anexo: true });
          sp.hp1 = sp.alto = 2.3 + rnd() * 0.5; sp.pend = 0.1; sp.eF = 0.35; sp.parapeto = sp.tipo === 'losa' ? 0.15 : 0; sp.teja = false;
          if (rnd() < 0.35) { sp.colMuro = C_LADR; sp.ladrilloTodo = true; }
          sp.enCerca = sp.distC < R_CERCA;
          reg.agregar(Hb, 'anexo', sp); casas.push(sp);
        }
      }
    } else if (w > 2.5) baldios.push({ P0, u, v, a0: a, w, lod, base: Y_VEREDA, kL, kR, distC });
    a += w;
    primera = false;
  }
}
/** Fila de construcciones posteriores pegadas a un lindero del lote (muro ciego hacia el lote) */
function filaPosterior(ctx, reg, rnd, casas, origen, dirT, ini, fin, fondo) {
  const c = ctx.centro;
  let n = perp(dirT); if (dot(n, sub(c, origen)) > 0) n = mul(n, -1);
  const prop = { p: add(origen, mul(n, 0.02)), d: dirT };
  const P0 = interLineas(prop, ini), PF = interLineas(prop, fin);
  if (!P0 || !PF) return;
  const u = nrm(sub(PF, P0)), v = n;
  const L = len(sub(PF, P0));
  const pend = (lin) => { let dd = lin.d; if (dot(dd, v) < 0) dd = mul(dd, -1); return dot(dd, u) / dot(dd, v); };
  const kIni = pend(ini), kFin = pend(fin);
  let a = 0, primera = true;
  while (a < L - 2) {
    let w = 5 + rnd() * 5;
    if (L - a - w < 4) w = L - a;
    const ultima = a + w >= L - 0.01;
    const kL = primera ? kIni : 0, kR = ultima ? kFin : 0;
    let d = fondo[0] + rnd() * (fondo[1] - fondo[0]);
    while (w + (kR - kL) * d < 3 && d > 4) d -= 0.5;
    const H = [add(P0, mul(u, a)), add(P0, mul(u, a + w)), add(add(P0, mul(u, a + w + kR * d)), mul(v, d)), add(add(P0, mul(u, a + kL * d)), mul(v, d))];
    if (!reg.choca(encoger(H, 0.08))) {
      const centro2 = centroide(H);
      const spec = especCasa(rnd, { distLote: 0, posterior: true, lod: 0, kL, kR, d, base: 0, frente: false });
      Object.assign(spec, { P0, u, v, a0: a, w, d, kL, kR, frente: false, base: 0, distC: len(sub(centro2, c)) });
      reg.agregar(H, 'casa', spec);
      casas.push(spec);
    }
    a += w; primera = false;
  }
}
/** Cerco de un terreno sin construir: muro con portón metálico */
function construirBaldio(J, b, rnd) {
  const { P0, u, v, a0, w } = b;
  const P = add(P0, mul(u, a0)), Q = add(P0, mul(u, a0 + w));
  const out = mul(v, -1);
  const h = 1.9 + rnd() * 0.5;
  const ladr = rnd() < 0.45;
  const gb = ladr ? J.ladrillo : J.muro;
  const c = ladr ? C_LADR : col(elegir(rnd, PAL_MURO), 0.92);
  const gw = Math.min(3.0, w * 0.45), g0 = (w - gw) * (0.2 + rnd() * 0.6);
  const inw = mul(v, 0.15);
  const tramo = (x0, x1) => { if (x1 - x0 < 0.1) return; const A = add(P, mul(u, x0)), B2 = add(P, mul(u, x1)); gb.prisma([A, B2, add(B2, inw), add(A, inw)], -0.4, h, c); };
  tramo(0, g0); tramo(g0 + gw, w);
  if (b.lod <= 1) panelPlano(J, add(P, mul(u, g0)), add(P, mul(u, g0 + gw)), out, 0, gw, b.base, b.base + Math.min(h, 2.3), 'puerta', 1, col(elegir(rnd, PAL_PUERTA)));
  if (b.lod <= 1) J.oscuro.cajaSeg([P[0] + u[0] * g0 + v[0] * 0.07, b.base + Math.min(h, 2.3) + 0.03, P[1] + u[1] * g0 + v[1] * 0.07], [P[0] + u[0] * (g0 + gw) + v[0] * 0.07, b.base + Math.min(h, 2.3) + 0.03, P[1] + u[1] * (g0 + gw) + v[1] * 0.07], 0.05, 0.05, col('#2b2b2b'));
  return [P, Q];
}

// ================================================================ cerco bajo con reja metálica
function cercoReja(J, A, Bp, v, hMuro = 0.7, hReja = 1.72, colM = col('#e6dcc5'), cR = col('#2d3a33')) {
  const inw = mul(v, 0.15);
  J.muro.prisma([A, Bp, add(Bp, inw), add(A, inw)], -0.3, hMuro, colM);
  const o = mul(v, 0.075);
  J.oscuro.cajaSeg([A[0] + o[0], hReja, A[1] + o[1]], [Bp[0] + o[0], hReja, Bp[1] + o[1]], 0.04, 0.04, cR);
  J.oscuro.cajaSeg([A[0] + o[0], hMuro + 0.2, A[1] + o[1]], [Bp[0] + o[0], hMuro + 0.2, Bp[1] + o[1]], 0.03, 0.03, cR);
  const L = len(sub(Bp, A)), dir = nrm(sub(Bp, A));
  for (let s = 0.1; s < L - 0.05; s += 0.13) {
    const P = add(A, mul(dir, s));
    J.oscuro.cajaSeg([P[0] + o[0], hMuro, P[1] + o[1]], [P[0] + o[0], hReja, P[1] + o[1]], 0.018, 0.018, cR, [1, 0, 0], true);
  }
  for (let s = 0; s <= L + 0.01; s += Math.max(2.5, L / Math.ceil(L / 3))) {
    const P = add(A, mul(dir, Math.min(s, L)));
    J.muro.prisma([[P[0] - 0.14, P[1] - 0.14], [P[0] + 0.14, P[1] - 0.14], [P[0] + 0.14, P[1] + 0.14], [P[0] - 0.14, P[1] + 0.14]].map((q) => add(q, mul(v, 0.07))), -0.3, hReja + 0.1, colM);
  }
}
/** Jardín cercado en la esquina frente al portón de ingreso (pasto, arbustos, bancas) */
function construirJardin(ctx, J, jd, reg, gbSuelo, extraVeg) {
  const { P0, u, v, a0, w, d, kR } = jd;
  const W2 = (a, b) => add(add(P0, mul(u, a)), mul(v, b));
  const H = [W2(a0, 0), W2(a0 + w, 0), W2(a0 + w + kR * d, d), W2(a0, d)];
  reg.agregar(H, 'jardin');
  const cP = [col('#7fa457'), col('#6e9a4a'), col('#86aa5c'), col('#77a051')];
  gbSuelo.poly(H.map((p) => [p[0], 0.004, p[1]]), H.map((p) => [p[0], p[1]]), H.map((_, i) => cP[i % 4]), ARRIBA);
  // frente al jirón (con puerta) y frente a la calle lateral
  const g0 = w * 0.3, g1 = g0 + 1.2;
  cercoReja(J, W2(a0, 0), W2(a0 + g0, 0), v, 0.45, 1.25);
  cercoReja(J, W2(a0 + g1, 0), W2(a0 + w, 0), v, 0.45, 1.25);
  panelPlano(J, W2(a0 + g0, 0), W2(a0 + g1, 0), mul(v, -1), 0, 1.2, Y_VEREDA, Y_VEREDA + 1.3, 'puerta', 3, col('#3a4a40'));
  const nL = nrm(perp(sub(H[2], H[1]))); const vin = dot(nL, sub(centroide(H), H[1])) > 0 ? nL : mul(nL, -1);
  cercoReja(J, H[1], H[2], vin, 0.45, 1.25);
  // muro de fondo y lateral (colindancias)
  const cM = col('#d8d0bf');
  J.muro.prisma([H[3], H[2], add(H[2], mul(v, 0.15)), add(H[3], mul(v, 0.15))], -0.3, 2.2, cM);
  J.muro.prisma([H[0], H[3], add(H[3], mul(u, 0.15)), add(H[0], mul(u, 0.15))], -0.3, 2.2, cM);
  // bancas de madera
  for (const [fa, fb] of [[0.35, 0.55], [0.7, 0.45]]) {
    const A = W2(a0 + w * fa - 0.8, d * fb), B = W2(a0 + w * fa + 0.8, d * fb);
    J.muro.cajaSeg([A[0], 0.45, A[1]], [B[0], 0.45, B[1]], 0.4, 0.06, C_MADERA);
    for (const P of [A, B]) J.oscuro.cajaSeg([P[0], 0, P[1]], [P[0], 0.42, P[1]], 0.05, 0.3, col('#3b3b3b'), [1, 0, 0]);
  }
  // arbustos junto al cerco y un árbol pequeño al fondo (lejos de la toma de cámara)
  for (let t = 0.12; t < 0.95; t += 0.16) extraVeg.push({ tipo: 'arbusto', P: W2(a0 + w * t, 0.9), s: 0.8 });
  extraVeg.push({ tipo: 'frondoso2', P: W2(a0 + 1.6, d - 1.8), s: 0.62 });
  extraVeg.push({ tipo: 'arbusto', P: W2(a0 + w - 1.5, d - 1.2), s: 1.1 });
}

// ================================================================ casa de techo rojizo y patio verde junto al vértice D
function construirPatio(ctx, Jc, reg, rnd, casas, gbSuelo) {
  const { FL, patio } = ctx;
  if (!patio) return null;
  const sD = FL.s(ctx.D);
  // casa antigua de adobe con techo de teja, pegada al muro del lote en D
  const P0 = FL.p(0, 0), u = FL.t, v = mul(FL.n, -1);
  const w = 8.0, d = 7.6, a0 = sD + 0.05;
  const spec = {
    P0, u, v, a0, w, d, kL: 0, kR: 0, lod: 0, base: Y_VEREDA, pisos: 1, tipo: 'dos_aguas', pend: 0.42, eF: 0.85, eB: 0.6, vol: 0,
    hp1: Y_VEREDA + 3.0, alto: Y_VEREDA + 3.0, parapeto: 0, colMuro: col('#efe7d3'), colMuro2: col('#efe7d3'), ladrillo2: false,
    zocalo: { h: Y_VEREDA + 0.9, col: col('#8f4434') }, colTecho: col('#ffffff', 0.95), teja: true, celdaV: 3, celdaV2: 3, celdaP: 0,
    tintePuerta: col('#6a452c'), tienda: false, letrero: -1, tanque: false, fierros: false, cornisa: false, obra: null,
    colCiego: col('#e6dcc5'), fachIzq: false, fachDer: true, frente: true, pegado: false, distC: 20,
  };
  const H = [FL.p(a0, 0), FL.p(a0 + w, 0), add(FL.p(a0 + w, 0), mul(v, d)), add(FL.p(a0, 0), mul(v, d))];
  reg.agregar(H, 'casa', spec);
  casas.push(spec);
  // cerco del patio sobre la calle: murete tarrajeado + reja
  const s0 = a0 + w, s1 = Math.max(...patio.map((p) => FL.s(p)));
  cercoReja(Jc, FL.p(s0, 0), FL.p(s1, 0), v);
  // pasto del patio (más verde)
  const cP = [col('#7fa457'), col('#6e9a4a'), col('#86aa5c'), col('#77a051')];
  gbSuelo.poly(patio.map((p) => [p[0], 0.004, p[1]]), patio.map((p) => [p[0], p[1]]), patio.map((_, i) => cP[i % 4]), ARRIBA);
  return spec;
}

// ================================================================ vegetación
function lobulo(r, det, amp, semilla) {
  const g = new THREE.IcosahedronGeometry(r, det);
  const p = g.attributes.position;
  for (let i = 0; i < p.count; i++) {
    const x = p.getX(i), y = p.getY(i), z = p.getZ(i);
    const k = 1 + amp * PERLIN.noise(x * 1.9 / r + semilla, y * 1.9 / r, z * 1.9 / r - semilla);
    p.setXYZ(i, x * k, y * k, z * k);
  }
  return g;
}
function copa(lobs, det, rnd, centro, semilla, uvEsc = 2.4) {
  const geos = [];
  for (const [lx, ly, lz, r] of lobs) {
    const g = lobulo(r, det, 0.22, semilla + geos.length * 3.7);
    g.translate(lx, ly, lz);
    geos.push(g);
  }
  const g = mergeGeometries(geos, false);
  const p = g.attributes.position, n = g.attributes.normal;
  const uv = new Float32Array(p.count * 2);
  for (let i = 0; i < p.count; i++) {
    const dx = p.getX(i) - centro[0], dy = p.getY(i) - centro[1], dz = p.getZ(i) - centro[2];
    const l = Math.hypot(dx, dy, dz) || 1;
    const nx = n.getX(i) * 0.4 + (dx / l) * 0.6, ny = n.getY(i) * 0.4 + (dy / l) * 0.6 + 0.1, nz = n.getZ(i) * 0.4 + (dz / l) * 0.6;
    const ln = Math.hypot(nx, ny, nz);
    n.setXYZ(i, nx / ln, ny / ln, nz / ln);
    uv[2 * i] = (Math.atan2(dz, dx) / (Math.PI * 2)) * 3 * (l / uvEsc) + 0.5; uv[2 * i + 1] = p.getY(i) / uvEsc;
  }
  g.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
  return g;
}
function geoFrondoso(semilla, det) {
  const r = rng(semilla);
  const lobs = [];
  const n = det ? 6 : 4;
  for (let i = 0; i < n; i++) {
    const a = (i / n) * Math.PI * 2 + r() * 0.8, rr = i === 0 ? 0 : 0.9 + r() * 0.6;
    lobs.push([Math.cos(a) * rr, 4.4 + (r() - 0.4) * 1.0 + (i === 0 ? 0.5 : 0), Math.sin(a) * rr, 1.25 + r() * 0.5]);
  }
  const c = copa(lobs, det, r, [0, 4.4, 0], semilla * 0.37);
  const tr = [];
  const t0 = new THREE.CylinderGeometry(0.13, 0.22, 3.6, det ? 7 : 5, 1, true); t0.translate(0, 1.8, 0); tr.push(t0);
  if (det) for (let i = 0; i < 3; i++) {
    const b = new THREE.CylinderGeometry(0.05, 0.09, 1.8, 5, 1, true); b.translate(0, 0.9, 0);
    b.rotateZ(0.6 + r() * 0.3); b.rotateY((i / 3) * Math.PI * 2 + r()); b.translate(0, 2.6, 0); tr.push(b);
  }
  return { copa: c, tronco: mergeGeometries(tr, false) };
}
function geoEucalipto(semilla, det) {
  const r = rng(semilla);
  const lobs = [];
  const n = det ? 6 : 4;
  for (let i = 0; i < n; i++) {
    const ang = (i / n) * Math.PI * 2 + r(), rr = i === 0 ? 0.2 : 1.0 + r() * 0.9;
    lobs.push([Math.cos(ang) * rr, 8.4 + r() * 4.2, Math.sin(ang) * rr, 1.1 + r() * 0.6]);
  }
  const c = copa(lobs, det, r, [0, 10.5, 0], semilla * 0.21);
  c.scale(1.1, 0.85, 1.1); c.translate(0, 1.4, 0);
  const t = new THREE.CylinderGeometry(0.11, 0.24, 11, det ? 7 : 5, 1, true); t.translate(0, 5.5, 0);
  return { copa: c, tronco: t };
}
function geoPalmera(semilla) {
  const r = rng(semilla);
  const H = 7.5, curva = (t) => [Math.sin(t * 1.2) * 0.5, t * H, 0];
  const tr = [];
  const N = 5;
  for (let i = 0; i < N; i++) {
    const a = curva(i / N), b = curva((i + 1) / N);
    const L = Math.hypot(b[0] - a[0], b[1] - a[1]);
    const g = new THREE.CylinderGeometry(0.15 - 0.012 * (i + 1), 0.16 - 0.012 * i, L * 1.02, 7, 1, true);
    g.translate(0, L / 2, 0); g.rotateZ(-Math.atan2(b[0] - a[0], b[1] - a[1])); g.translate(a[0], a[1], 0);
    tr.push(g);
  }
  const top = curva(1);
  const pos = [], colr = [];
  const verde = col('#4f7d33'), amarillo = col('#9a9a4a'), oscuro = col('#355a26');
  const nF = 11;
  for (let f = 0; f < nF; f++) {
    const az = (f / nF) * Math.PI * 2 + r() * 0.4, el = 0.25 + r() * 0.6, Lf = 2.8 + r() * 0.9;
    const dir = [Math.cos(az), 0, Math.sin(az)];
    const lado = [-dir[2], 0, dir[0]];
    const S = 8;
    const R = [];
    for (let k = 0; k <= S; k++) {
      const t = k / S, s = t * Lf;
      R.push([top[0] + dir[0] * s * Math.cos(el), top[1] + Math.sin(el) * s - 0.55 * s * s / Lf, top[2] + dir[2] * s * Math.cos(el)]);
    }
    for (let k = 0; k < S; k++) {
      const t = (k + 0.5) / S, lk = 0.62 * Math.sin(Math.PI * Math.min(1, t * 1.15)) + 0.08;
      const a = R[k], b = R[k + 1];
      const cc = mezclar(f % 3 ? verde : oscuro, amarillo, t * 0.6);
      for (const sg of [1, -1]) {
        const tip = [a[0] + lado[0] * lk * sg + (b[0] - a[0]) * 0.8, a[1] - 0.22 * lk, a[2] + lado[2] * lk * sg + (b[2] - a[2]) * 0.8];
        pos.push(...a, ...b, ...tip); colr.push(...cc, ...cc, ...escalar(cc, 0.85));
      }
    }
  }
  const fr = new THREE.BufferGeometry();
  fr.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  fr.setAttribute('color', new THREE.Float32BufferAttribute(colr, 3));
  fr.computeVertexNormals();
  const nn = fr.attributes.normal;
  for (let i = 0; i < nn.count; i++) if (nn.getY(i) < 0) nn.setXYZ(i, -nn.getX(i), -nn.getY(i), -nn.getZ(i));
  return { tronco: mergeGeometries(tr, false), fronda: fr };
}
function geoPlatano(semilla) {
  const r = rng(semilla);
  const tr = [], pos = [], colr = [];
  const verde = col('#5f9a3c'), claro = col('#82b04e'), seco = col('#8a7a45');
  const tallos = 2;
  for (let ti = 0; ti < tallos; ti++) {
    const ox = (r() - 0.5) * 0.9, oz = (r() - 0.5) * 0.9, H = 2.0 + r() * 1.0;
    const g = new THREE.CylinderGeometry(0.08, 0.13, H, 6, 1, true); g.translate(ox, H / 2, oz); tr.push(g);
    const nH = 5;
    for (let hj = 0; hj < nH; hj++) {
      const az = (hj / nH) * Math.PI * 2 + r() * 0.7, Lh = 1.5 + r() * 0.7, el = 0.5 + r() * 0.6;
      const dir = [Math.cos(az), 0, Math.sin(az)], lado = [-dir[2], 0, dir[0]];
      const S = 4, M = [];
      for (let k = 0; k <= S; k++) { const s = (k / S) * Lh; M.push([ox + dir[0] * s * Math.cos(el) * 1.1, H + Math.sin(el) * s - 0.8 * s * s / Lh, oz + dir[2] * s * Math.cos(el) * 1.1]); }
      const cc = hj === 0 && r() < 0.6 ? seco : mezclar(verde, claro, r() * 0.6);
      for (let k = 0; k < S; k++) {
        const t0 = k / S, t1 = (k + 1) / S;
        const w0 = 0.32 * Math.sin(Math.PI * Math.min(1, 0.15 + t0)) + 0.02, w1 = 0.32 * Math.sin(Math.PI * Math.min(1, 0.15 + t1)) + 0.02;
        const a = M[k], b = M[k + 1];
        for (const sg of [1, -1]) {
          const a2 = [a[0] + lado[0] * w0 * sg, a[1] - 0.06, a[2] + lado[2] * w0 * sg], b2 = [b[0] + lado[0] * w1 * sg, b[1] - 0.06, b[2] + lado[2] * w1 * sg];
          pos.push(...a, ...b, ...b2, ...a, ...b2, ...a2);
          for (let q = 0; q < 6; q++) colr.push(...cc);
        }
      }
    }
  }
  const h = new THREE.BufferGeometry();
  h.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  h.setAttribute('color', new THREE.Float32BufferAttribute(colr, 3));
  h.computeVertexNormals();
  const nn = h.attributes.normal;
  for (let i = 0; i < nn.count; i++) if (nn.getY(i) < 0) nn.setXYZ(i, -nn.getX(i), -nn.getY(i), -nn.getZ(i));
  return { tronco: mergeGeometries(tr, false), fronda: h };
}
function geoArbusto(semilla, det = 1) {
  const r = rng(semilla);
  const lobs = [];
  for (let i = 0; i < 3; i++) lobs.push([(r() - 0.5) * 0.8, 0.45 + r() * 0.25, (r() - 0.5) * 0.8, 0.45 + r() * 0.25]);
  return copa(lobs, det, r, [0, 0.5, 0], semilla * 0.11, 1.2);
}
function geoLejano() {
  const g = new THREE.IcosahedronGeometry(1, 0);
  const p = g.attributes.position, n = g.attributes.normal;
  for (let i = 0; i < p.count; i++) { const x = p.getX(i), y = p.getY(i), z = p.getZ(i); const l = Math.hypot(x, y, z); n.setXYZ(i, x / l, y / l + 0.25, z / l); }
  g.scale(1, 1.15, 1); g.translate(0, 0.9, 0);
  return g;
}
function instanciar(geo, mat, lista, sombra, nombre) {
  if (!lista.length) return null;
  const im = new THREE.InstancedMesh(geo, mat, lista.length);
  const m = new THREE.Matrix4(), q = new THREE.Quaternion(), s = new THREE.Vector3(), p = new THREE.Vector3(), e = new THREE.Euler(), c = new THREE.Color();
  lista.forEach((it, i) => {
    q.setFromEuler(e.set(it.inc || 0, it.rot || 0, 0));
    p.set(it.x, it.y, it.z); s.set(it.s, it.s * (it.sy || 1), it.s);
    m.compose(p, q, s); im.setMatrixAt(i, m);
    if (it.c) im.setColorAt(i, c.setRGB(it.c[0], it.c[1], it.c[2]));
  });
  if (im.instanceColor) im.instanceColor.needsUpdate = true;
  im.castShadow = sombra; im.receiveShadow = true;
  im.computeBoundingSphere();
  im.name = nombre;
  return im;
}

function construirVegetacion(ctx, M, grupo, reg, casas, altura, baldiosPts, extraVeg = []) {
  const rnd = rng(7071);
  const L = { frondoso: [[], []], frondoso2: [[], []], eucalipto: [[], []], palmera: [[], []], platano: [[], []], arbusto: [[], []], lejano: [] };
  const { lote, patio, centro } = ctx;
  const TINTES = [[1, 1, 1], [1.12, 1.06, 0.78], [0.82, 0.92, 0.9], [1.06, 0.96, 0.82], [0.9, 0.97, 0.85]];
  const tono = (base, var_ = 0.12) => { const k = 1 - var_ / 2 + rnd() * var_; const t = elegir(rnd, TINTES); return [base[0] * k * t[0], base[1] * k * t[1], base[2] * k * t[2]]; };
  const libre = (P, rc, enPatio = false) => {
    if (enCalle(ctx, P, 0.6)) return false;
    if (distPoly(P, lote) < rc + 0.4) return false;
    if (!enPatio && patio && distPoly(P, patio) < 0.5) return false;
    if (reg.distancia(P, rc + 2) < Math.max(0.8, rc * 0.35)) return false;
    return true;
  };
  const poner = (tipo, P, s, extra = {}) => {
    const dc = len(sub(P, centro));
    const it = { x: P[0], y: altura(P[0], P[1]) - 0.08, z: P[1], s, rot: rnd() * Math.PI * 2, ...extra };
    if (tipo === 'lejano') { L.lejano.push(it); return; }
    L[tipo][dc < R_CERCA - 10 ? 0 : 1].push(it);
  };
  const BASES = { frondoso: col('#ffffff'), eucalipto: col('#c9dccb'), palmera: col('#ffffff'), platano: col('#ffffff'), arbusto: col('#e8f0d8') };
  const elegirTipo = (dLote) => {
    const r = rnd();
    if (r < 0.46) return rnd() < 0.5 ? 'frondoso' : 'frondoso2';
    if (r < 0.66) return 'platano';
    if (r < 0.75) return 'palmera';
    if (r < 0.84 && dLote > 45) return 'eucalipto';
    return 'arbusto';
  };
  const escalaDe = (tipo, dLote) => {
    if (tipo === 'eucalipto') return 0.8 + rnd() * 0.45;
    if (tipo === 'palmera') return 0.85 + rnd() * 0.35;
    if (tipo === 'platano') return 0.9 + rnd() * 0.35;
    if (tipo === 'arbusto') return 0.8 + rnd() * 0.7;
    return (dLote < 20 ? 0.7 : 0.8) + rnd() * (dLote < 20 ? 0.3 : 0.5);
  };
  // patios traseros de las casas
  for (const h of casas) {
    if (h.distC > 330) continue;
    const n = rnd() < 0.62 ? 1 + (rnd() < 0.35 ? 1 : 0) : 0;
    for (let i = 0; i < n; i++) {
      const b = h.d + 2.2 + rnd() * 7;
      const a = h.a0 + 1 + rnd() * Math.max(0.5, h.w - 2);
      const P = [h.P0[0] + h.u[0] * a + h.v[0] * b, h.P0[1] + h.u[1] * a + h.v[1] * b];
      const dLote = distPoly(P, lote);
      const tipo = elegirTipo(dLote);
      const s = escalaDe(tipo, dLote);
      const rc = tipo === 'arbusto' ? 0.8 : tipo === 'platano' ? 1.3 : tipo === 'eucalipto' ? 1.8 : 2.2 * s;
      if (!libre(P, rc)) continue;
      const base = BASES[tipo.replace('2', '')];
      poner(tipo, P, s, { c: tono(base), sy: tipo === 'arbusto' ? 0.7 + rnd() * 0.4 : 1 });
    }
  }
  // terrenos sin construir: árbol o plátanos
  for (const P of baldiosPts) {
    if (rnd() < 0.7) { const tipo = rnd() < 0.5 ? 'platano' : 'frondoso'; const s = escalaDe(tipo, 99); if (libre(P, 2)) poner(tipo, P, s, { c: tono(BASES[tipo]) }); }
  }
  // relleno del interior de las manzanas
  for (let i = 0; i < 1300; i++) {
    const oJ = lerp(LIM_J[0] + 5, LIM_J[1] - 5, rnd()), oL = lerp(LIM_L[0] + 5, LIM_L[1] - 5, rnd());
    const P = cruce(ctx.FJ, oJ, ctx.FL, oL);
    if (fbm(P[0] / 60, P[1] / 60, 2, 3.3) < -0.05) continue;
    const dLote = distPoly(P, lote);
    const tipo = elegirTipo(dLote);
    const s = escalaDe(tipo, dLote);
    if (!libre(P, tipo === 'arbusto' ? 0.8 : 2.2 * s)) continue;
    poner(tipo, P, s, { c: tono(BASES[tipo.replace('2', '')]) });
  }
  // vegetación de jardines (posiciones fijas)
  for (const e of extraVeg) if (!enCalle(ctx, e.P, 0.8)) poner(e.tipo, e.P, e.s, { c: tono(BASES[e.tipo.replace('2', '')], 0.06), sy: e.tipo === 'arbusto' ? 0.8 : 1 });
  // patio verde detrás del fondo del lote
  if (patio) {
    const FL = ctx.FL;
    const sitios = [
      ['frondoso', 0.55, 0.62, 1.12], ['frondoso2', 0.8, 0.35, 0.95], ['palmera', 0.25, 0.8, 1.0], ['platano', 0.85, 0.75, 1.1],
      ['platano', 0.15, 0.55, 1.0], ['arbusto', 0.92, 0.12, 1.2], ['arbusto', 0.7, 0.1, 1.0], ['arbusto', 0.4, 0.92, 1.1], ['frondoso', 0.3, 0.3, 0.8],
    ];
    const ss = patio.map((p) => FL.s(p)), ee = patio.map((p) => FL.e(p));
    const s0 = Math.min(...ss), s1 = Math.max(...ss), e0 = Math.min(...ee), e1 = Math.max(...ee);
    for (const [tipo, fs, fe, s] of sitios) {
      const P = FL.p(lerp(s0, s1, fs), lerp(e1, e0, fe));
      if (!enPoly(P, patio) || reg.distancia(P, 4) < 0.8 || distPoly(P, lote) < 2.0) continue;
      poner(tipo, P, s, { c: tono(BASES[tipo.replace('2', '')], 0.06) });
    }
  }
  // campo: hileras de árboles en linderos de parcelas y bosquetes
  for (let i = 0; i < 520; i++) {
    const ang = rnd() * Math.PI * 2, r = 200 + rnd() * 520;
    const P = [centro[0] + Math.cos(ang) * r, centro[1] + Math.sin(ang) * r];
    const oJ = ctx.FJ.e(P), oL = ctx.FL.e(P);
    if (oJ > LIM_J[0] - 8 && oJ < LIM_J[1] + 8 && oL > LIM_L[0] - 8 && oL < LIM_L[1] + 8) continue;
    if (enCalle(ctx, P, 3) || reg.distancia(P, 6) < 2) continue;
    const h = altura(P[0], P[1]);
    if (h > 25) continue;
    const linde = Math.abs(((oJ / 52) % 1 + 1) % 1 - 0.5) > 0.44 || Math.abs(((oL / 38) % 1 + 1) % 1 - 0.5) > 0.45;
    if (!linde && fbm(P[0] / 90, P[1] / 90, 2, 6.1) < 0.25) continue;
    const n = 1 + Math.floor(rnd() * 4);
    for (let k = 0; k < n; k++) {
      const Q = [P[0] + (rnd() - 0.5) * 14, P[1] + (rnd() - 0.5) * 14];
      if (enCalle(ctx, Q, 2)) continue;
      const tipo = r < 300 ? (rnd() < 0.25 ? 'eucalipto' : 'frondoso') : 'lejano';
      if (tipo === 'lejano') poner('lejano', Q, 1, { s: 2.8 + rnd() * 2.2, sy: 0.85 + rnd() * 0.45, c: mezclar(escalar(col(elegir(rnd, ['#56743f', '#4b6a3a', '#62804a', '#5a6f3c'])), 0.9 + rnd() * 0.2), escalar(C_T.lejos, 0.7), neblina(r)) });
      else poner(tipo, Q, escalaDe(tipo, 99), { c: tono(BASES[tipo]) });
    }
  }
  // bosque en las laderas: manchas de copas agrupadas (mismo tono que el suelo del bosque)
  let n = 0;
  for (let i = 0; i < 40000 && n < 1500; i++) {
    const ang = rnd() * Math.PI * 2, r = 380 + rnd() * 470;
    const P = [centro[0] + Math.cos(ang) * r, centro[1] + Math.sin(ang) * r];
    const h = altura(P[0], P[1]);
    if (h < 2 || h > 300) continue;
    if (fbm(P[0] / 130, P[1] / 130, 4, 7.7) > 0.0 - rnd() * 0.2) continue;
    if (fbm(P[0] / 40, P[1] / 40, 2, 2.9) < 0.05) continue;
    const s = 3.5 + rnd() * 2.5;
    const base = escalar(col(elegir(rnd, ['#3f5c36', '#4a683d', '#3a5434', '#52703f'])), 0.85 + rnd() * 0.2);
    const c = mezclar(base, escalar(C_T.lejos, 0.7), neblina(r));
    L.lejano.push({ x: P[0], y: h - 1.2, z: P[1], s, sy: 0.9 + rnd() * 0.5, rot: rnd() * 6.3, c });
    n++;
  }
  // geometrías e instancias
  const gF = [geoFrondoso(101, 1), geoFrondoso(101, 0)], gF2 = [geoFrondoso(202, 1), geoFrondoso(202, 0)];
  const gE = [geoEucalipto(303, 1), geoEucalipto(303, 0)];
  const gP = geoPalmera(404), gPl = geoPlatano(505), gA = [geoArbusto(606, 1), geoArbusto(606, 0)], gL = geoLejano();
  const agregar = (o) => { if (o) grupo.add(o); };
  for (const i of [0, 1]) {
    const sombra = i === 0, sufijo = i === 0 ? '-cerca' : '-medio';
    const troncoCol = (lst, c) => lst.map((it) => ({ ...it, c: escalar(c, 0.9 + ((it.x * 7.3 + it.z * 3.1) % 1 + 1) % 1 * 0.2) }));
    const cT = col('#5a4838');
    agregar(instanciar(gF[i].copa, i ? M.hojasLejos : M.hojas, L.frondoso[i], sombra, 'arboles' + sufijo));
    agregar(instanciar(gF[i].tronco, M.tronco, troncoCol(L.frondoso[i], cT), sombra, 'troncos' + sufijo));
    agregar(instanciar(gF2[i].copa, i ? M.hojasLejos : M.hojas, L.frondoso2[i], sombra, 'arboles2' + sufijo));
    agregar(instanciar(gF2[i].tronco, M.tronco, troncoCol(L.frondoso2[i], cT), sombra, 'troncos2' + sufijo));
    agregar(instanciar(gE[i].copa, i ? M.hojasLejos : M.hojas, L.eucalipto[i], sombra, 'eucaliptos' + sufijo));
    agregar(instanciar(gE[i].tronco, M.tronco, troncoCol(L.eucalipto[i], col('#b8ad9b')), sombra, 'troncos-euc' + sufijo));
    agregar(instanciar(gP.fronda, M.fronda, L.palmera[i], sombra, 'palmeras' + sufijo));
    agregar(instanciar(gP.tronco, M.tronco, troncoCol(L.palmera[i], col('#a89c88')), sombra, 'troncos-palm' + sufijo));
    agregar(instanciar(gPl.fronda, M.fronda, L.platano[i], sombra, 'platanos' + sufijo));
    agregar(instanciar(gPl.tronco, M.tronco, troncoCol(L.platano[i], col('#6f8a45')), sombra, 'tallos-plat' + sufijo));
    agregar(instanciar(gA[i], i ? M.hojasLejos : M.hojas, L.arbusto[i], sombra, 'arbustos' + sufijo));
  }
  agregar(instanciar(gL, M.copaLejana, L.lejano, false, 'arboles-lejanos'));
}

// ================================================================ postes de alumbrado y cables
function construirPostes(ctx, Jc, Jm, M, grupo) {
  const { calles, FJ, FL } = ctx;
  const jr = calles[0], lat = calles[1];
  const rnd = rng(8081);
  const lineas = [];       // [[p0,p1], ...] puntos 3D
  const gPoste = new THREE.CylinderGeometry(0.085, 0.15, 9.0, 8, 1, false);
  const gAisl = new THREE.CylinderGeometry(0.05, 0.07, 0.16, 6, 1, false);
  const cPoste = col('#a9a69d'), cMetal = col('#5d6266'), cAisl = col('#d9d6cc'), cLamp = col('#6f757a');
  const sobreVereda = (P, propia) => {
    for (const k of calles) { if (k === propia) continue; const e = Math.abs(k.m.e(P) - k.c); const s = k.m.s(P); if (e < k.half + 0.5 && s > k.sIni - 1 && s < k.s1 + 1) return false; }
    return true;
  };
  const postes = (k, lado, s0, s1, paso, evitar = []) => {
    const e = k.c + lado * (k.w / 2 + 0.3);
    const lst = [];
    for (let s = s0; s <= s1; s += paso * (0.9 + rnd() * 0.2)) {
      if (evitar.some(([a, b]) => s > a && s < b)) continue;
      const P = k.m.p(s, e);
      if (!sobreVereda(P, k)) continue;
      const haciaCalle = mul(k.m.n, -lado);
      lst.push({ P, haciaCalle, along: k.m.t, lamp: true });
    }
    return lst;
  };
  const sBoca = FJ.s(cruce(FJ, jr.c + jr.w / 2 + 0.3, FL, lat.c));
  const lJr = postes(jr, 1, -150, 185, 31, [[sBoca - 7, sBoca + 5]]);
  const lLat = postes(lat, 1, FL.s(cruce(FL, lat.c + lat.w / 2 + 0.3, FJ, -2.2)), 240, 31);
  const otras = [];
  for (const k of calles.slice(2)) otras.push(postes(k, 1, k.pav[0] + 6, k.pav[1] - 4, 34));
  const todos = [lJr, lLat, ...otras];
  const anclas = (p) => {
    const { P, haciaCalle, along } = p;
    const across = haciaCalle;
    const at = (off, y) => [P[0] + across[0] * off, y, P[1] + across[1] * off];
    return { mt: [at(-0.3, 8.78), at(0.4, 8.78), at(1.05, 8.78)], bt: [at(0.18, 7.3), at(0.32, 7.05)], tel: [at(-0.18, 5.9), at(-0.18, 5.6)], along };
  };
  for (const lst of todos) for (const p of lst) {
    const { P, haciaCalle } = p;
    const yb = Y_VEREDA;
    const J = len(sub(P, ctx.centro)) < R_CERCA + 15 ? Jc : Jm;
    J.muro.geo(gPoste, new THREE.Matrix4().makeTranslation(P[0], yb + 4.5, P[1]), cPoste);
    const at = (off, y) => [P[0] + haciaCalle[0] * off, y, P[1] + haciaCalle[1] * off];
    J.muro.cajaSeg(at(-0.45, 8.6), at(1.2, 8.6), 0.1, 0.1, cPoste);
    for (const off of [-0.3, 0.4, 1.05]) J.muro.geo(gAisl, new THREE.Matrix4().makeTranslation(...at(off, 8.73)), cAisl);
    J.oscuro.cajaSeg(at(0.08, 7.35), at(0.4, 7.35), 0.05, 0.05, cMetal);
    J.oscuro.cajaSeg(at(0.08, 7.0), at(0.4, 7.0), 0.05, 0.05, cMetal);
    if (p.lamp) {
      const a0 = at(0.12, 7.75), a1 = at(1.55, 8.15);
      J.oscuro.cajaSeg(a0, a1, 0.05, 0.05, cLamp);
      const c1 = at(1.75, 8.12), c2 = at(1.25, 8.18);
      J.oscuro.cajaSeg(c2, c1, 0.26, 0.11, cLamp);
      J.muro.cajaSeg([c2[0], c2[1] - 0.065, c2[2]], [c1[0], c1[1] - 0.065, c1[2]], 0.2, 0.02, col('#e8ecef'));
    }
  }
  // transformador en un poste lejano del lote
  if (lJr.length > 6) { const p = lJr[lJr.length - 3]; const m = new THREE.Matrix4().makeTranslation(p.P[0] - p.haciaCalle[0] * 0.45, 6.4, p.P[1] - p.haciaCalle[1] * 0.45); Jm.muro.geo(new THREE.CylinderGeometry(0.32, 0.32, 0.95, 10), m, col('#8f9a95')); }
  // cables entre postes consecutivos (catenaria simple)
  const catenaria = (a, b, flecha, n = 10) => {
    for (let i = 0; i < n; i++) {
      const t0 = i / n, t1 = (i + 1) / n;
      const p0 = [lerp(a[0], b[0], t0), lerp(a[1], b[1], t0) - flecha * 4 * t0 * (1 - t0), lerp(a[2], b[2], t0)];
      const p1 = [lerp(a[0], b[0], t1), lerp(a[1], b[1], t1) - flecha * 4 * t1 * (1 - t1), lerp(a[2], b[2], t1)];
      lineas.push(...p0, ...p1);
    }
  };
  const tender = (p, q) => {
    const A = anclas(p), B2 = anclas(q);
    const L = len(sub(p.P, q.P));
    for (let i = 0; i < 3; i++) catenaria(A.mt[i], B2.mt[i], 0.25 + L * 0.009);
    for (let i = 0; i < 2; i++) catenaria(A.bt[i], B2.bt[i], 0.35 + L * 0.012);
    catenaria(A.tel[0], B2.tel[0], 0.45 + L * 0.014);
  };
  for (const lst of [lJr, lLat]) for (let i = 0; i < lst.length - 1; i++) if (len(sub(lst[i].P, lst[i + 1].P)) < 45) tender(lst[i], lst[i + 1]);
  // cruce aéreo del jirón hacia la línea de la lateral
  if (lJr.length && lLat.length) {
    let best = lJr[0];
    for (const p of lJr) if (len(sub(p.P, lLat[0].P)) < len(sub(best.P, lLat[0].P))) best = p;
    if (len(sub(best.P, lLat[0].P)) < 24) tender(best, lLat[0]);
  }
  // acometidas domiciliarias desde los postes a las fachadas del mismo lado
  for (const lst of [lJr, lLat]) for (const p of lst) {
    if (rnd() < 0.35 || len(sub(p.P, ctx.centro)) > 160) continue;
    const A = anclas(p).bt[1];
    for (const sg of [1, -1]) {
      if (rnd() < 0.5) continue;
      const off = (2.5 + rnd() * 5) * sg;
      const B2 = [p.P[0] + p.along[0] * off - p.haciaCalle[0] * 1.0, 3.1 + rnd() * 0.8, p.P[1] + p.along[1] * off - p.haciaCalle[1] * 1.0];
      catenaria(A, B2, 0.15, 6);
    }
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(lineas, 3));
  const ls = new THREE.LineSegments(g, M.cable);
  ls.name = 'entorno-cables';
  grupo.add(ls);
}

// ================================================================ caseríos lejanos
function construirCaserios(ctx, Jl, reg, altura, rnd, casasLejanas) {
  const { centro, FJ, FL, calles } = ctx;
  const jr = calles[0], lat = calles[1];
  // casas dispersas a lo largo del jirón y de la lateral fuera del pueblo
  const filaDispersa = (k, lado, s0, s1) => {
    const eP = k.c + lado * k.half;
    for (let s = s0; s < s1;) {
      const w = 6 + rnd() * 4;
      if (rnd() < 0.5) {
        const d = 7 + rnd() * 4;
        const u = k.m.t, v = mul(k.m.n, lado);
        const P0 = k.m.p(s, eP);
        const H = [P0, add(P0, mul(u, w)), add(add(P0, mul(u, w)), mul(v, d)), add(P0, mul(v, d))];
        if (!reg.choca(encoger(H, 0.1))) {
          const spec = especCasa(rnd, { distLote: 300, lod: 2, d, base: altura(P0[0], P0[1]) });
          Object.assign(spec, { P0, u, v, a0: 0, w, d, kL: 0, kR: 0, distC: len(sub(P0, centro)) });
          reg.agregar(H, 'casa', spec); casasLejanas.push(spec);
        }
      }
      s += w + rnd() * 18;
    }
  };
  const lim = [FJ.s(cruce(FJ, jr.c, FL, LIM_L[1])), FJ.s(cruce(FJ, jr.c, FL, LIM_L[0]))].sort((a, b) => a - b);
  for (const lado of [-1, 1]) { filaDispersa(jr, lado, lim[1] + 8, lim[1] + 380); filaDispersa(jr, lado, lim[0] - 380, lim[0] - 8); }
  const sl = FL.s(cruce(FL, lat.c, FJ, LIM_J[0]));
  for (const lado of [-1, 1]) filaDispersa(lat, lado, sl + 8, lat.s1 - 10);
  // caseríos en el fondo del valle
  for (let i = 0; i < 14; i++) {
    const ang = rnd() * Math.PI * 2, r = 280 + rnd() * 420;
    const C0 = [centro[0] + Math.cos(ang) * r, centro[1] + Math.sin(ang) * r];
    if (altura(C0[0], C0[1]) > 18) continue;
    const n = 2 + Math.floor(rnd() * 6);
    for (let k = 0; k < n; k++) {
      const P0 = [C0[0] + (rnd() - 0.5) * 50, C0[1] + (rnd() - 0.5) * 50];
      if (enCalle(ctx, P0, 4)) continue;
      const giro = (rnd() - 0.5) * 0.4;
      const u = [FJ.t[0] * Math.cos(giro) - FJ.t[1] * Math.sin(giro), FJ.t[0] * Math.sin(giro) + FJ.t[1] * Math.cos(giro)];
      const v = perp(u);
      const w = 6 + rnd() * 5, d = 6 + rnd() * 5;
      const H = [P0, add(P0, mul(u, w)), add(add(P0, mul(u, w)), mul(v, d)), add(P0, mul(v, d))];
      if (H.some((p) => enCalle(ctx, p, 1)) || reg.choca(encoger(H, 0.1))) continue;
      const hb = Math.min(...H.map((p) => altura(p[0], p[1])));
      const spec = especCasa(rnd, { distLote: 400, lod: 2, d, base: hb });
      Object.assign(spec, { P0, u, v, a0: 0, w, d, kL: 0, kR: 0, distC: r });
      reg.agregar(H, 'casa', spec); casasLejanas.push(spec);
    }
  }
}

// ================================================================ ensamblaje
function mallas(J, M, grupo, sombra, sufijo) {
  for (const [k, gb] of Object.entries(J)) {
    if (gb.vacio()) continue;
    const me = new THREE.Mesh(gb.build(), M[k]);
    me.castShadow = sombra;
    me.receiveShadow = sombra;
    me.name = `entorno-${k}-${sufijo}`;
    grupo.add(me);
  }
}

export function crearEntorno(scene, datos, opciones = {}) {
  const grupo = new THREE.Group();
  grupo.name = 'entorno';
  const ctx = prepararContexto(datos);
  const M = materiales(opciones.renderer);
  const altura = crearRelieve(ctx);
  const reg = new Registro(16);
  reg.agregar(ctx.lote, 'lote');
  if (ctx.patio) reg.agregar(ctx.patio, 'patio');

  // suelo + calles
  const gSuelo = new GB();
  const Jc = juego(), Jm = juego();
  const rC = rng(5051);
  const casas = [], baldios = [], jardines = [], extraVeg = [];
  construirPatio(ctx, Jc, reg, rC, casas, gSuelo);
  construirCalles(ctx, M, grupo);

  // casas: primero los linderos del lote (pegadas al muro), luego las filas por cercanía al lote
  const { B, C, D } = ctx;
  const fondoFila = planificarFilas(ctx);
  const fJrLote = fondoFila.find((f) => f.pegado);
  if (fJrLote) generarFila(fJrLote, ctx, reg, rC, casas, baldios, jardines);
  const dirBC = nrm(sub(C, B));
  const lineaJr = ctx.FJ.linea(-FONDO_ESQ);
  filaPosterior(ctx, reg, rC, casas, B, dirBC, lineaJr, { p: add(C, mul(dirBC, 7)), d: perp(dirBC) }, [6.5, 9]);
  if (ctx.patio) {
    const dirCD = nrm(sub(D, C));
    const sur = ctx.patio.slice().sort((p, q) => len(sub(p, C)) - len(sub(q, C)));
    filaPosterior(ctx, reg, rC, casas, C, dirCD, { p: C, d: dirBC }, { p: sur[0], d: nrm(sub(sur[1], sur[0])) }, [6.5, 8.5]);
  }
  const resto = fondoFila.filter((f) => f !== fJrLote);
  const distFila = (f) => {
    const P = interLineas(f.m.linea(f.eP), f.lI), Q = interLineas(f.m.linea(f.eP), f.lF);
    return P && Q ? distSeg(ctx.centro, P, Q) : 1e9;
  };
  resto.sort((a, b) => (a.m === b.m ? distFila(a) - distFila(b) : a.m === ctx.FJ ? -1 : 1));
  for (const f of resto) generarFila(f, ctx, reg, rC, casas, baldios, jardines);
  for (const jd of jardines) construirJardin(ctx, Jc, jd, reg, gSuelo, extraVeg);
  const terreno = construirTerreno(ctx, altura);
  const alturaMalla = terreno.alturaMalla;
  const lejanas = [];
  construirCaserios(ctx, Jm, reg, alturaMalla, rC, lejanas);

  for (const h of casas) construirCasa(h.lod === 0 || h.enCerca ? Jc : Jm, h, rC);
  for (const h of lejanas) construirCasa(Jm, h, rC);
  const baldiosPts = [];
  for (const b of baldios) {
    const [P, Q] = construirBaldio(b.lod === 0 ? Jc : Jm, b, rC);
    baldiosPts.push(add(lerp2(P, Q, 0.5), mul(b.v, 5 + rC() * 6)));
  }

  // terreno (malla polar) + pasto del patio; textura de parcelas/patios como multiplicador
  aplicarParcelas(M.suelo, genParcelas(ctx, altura, casas), ctx.centro);
  const gT = terreno.geo;
  const gP = gSuelo.vacio() ? null : gSuelo.build();
  const suelo = new THREE.Mesh(gP ? mergeGeometries([gT, gP], false) : gT, M.suelo);
  suelo.receiveShadow = true; suelo.name = 'entorno-suelo';
  grupo.add(suelo);

  construirPostes(ctx, Jc, Jm, M, grupo);
  construirVegetacion(ctx, M, grupo, reg, casas.concat(lejanas), alturaMalla, baldiosPts, extraVeg);
  mallas(Jc, M, grupo, true, 'cerca');
  mallas(Jm, M, grupo, false, 'lejos');

  grupo.userData = { casas: casas.length + lejanas.length, ctx };
  scene.add(grupo);
  return {
    grupo,
    actualizar(t) { uTiempo.value = t || 0; },
  };
}
