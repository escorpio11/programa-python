// Modelo 3D de la pollería campestre a partir de escena_polleria.json (convención: (u, v) -> x = u, z = -v).
// El entorno urbano (calles, casas vecinas, cerros) se reutiliza del recorrido del estacionamiento.
// Parámetros: ?w=&h= (tamaño), &etapa=1|2, &modo=evento (sombrillas retiradas y mesas redondas).
import * as THREE from 'three';
import { Sky } from 'three/addons/objects/Sky.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { crearEntorno } from '/estacionamiento_rodriguez_mendoza/animacion_3d/web/entorno.js';
import { crearVehiculo, COLORES_AUTOS } from '/estacionamiento_rodriguez_mendoza/animacion_3d/web/vehiculos.js';
import { texPasto, texAdoquin, texConcreto, texTarrajeo } from '/estacionamiento_rodriguez_mendoza/animacion_3d/web/texturas.js';

const qs = new URLSearchParams(location.search);
const ANCHO = +qs.get('w') || window.innerWidth;
const ALTO = +qs.get('h') || window.innerHeight;
const ETAPA = +(qs.get('etapa') || 1);
const EVENTO = qs.get('modo') === 'evento';
const VISOR = qs.get('visor') === '1';

const D = await (await fetch('./escena_polleria.json')).json();
const ctxParking = await (await fetch('/estacionamiento_rodriguez_mendoza/animacion_3d/web/escena.json')).json();

// ------------------------------------------------------------------ utilidades geométricas
const X = (p) => p[0];
const Z = (p) => -p[1];
const V3 = (p, y = 0) => new THREE.Vector3(X(p), y, Z(p));
const { D: Dsd, t: Tsd, n: Nsd } = D.marco_sd;
const SD = (s, d) => [Dsd[0] + s * Tsd[0] + d * Nsd[0], Dsd[1] + s * Tsd[1] + d * Nsd[1]];
const E = D.edificio;
const N2 = E.npt2;

function forma(poly) {
  const sh = new THREE.Shape();
  poly.forEach((p, i) => (i ? sh.lineTo(p[0], p[1]) : sh.moveTo(p[0], p[1])));
  return sh;
}
function prisma(poly, y0, y1, mat, sombra = true) {
  if (!poly || poly.length < 3) return new THREE.Group();
  const g = new THREE.ExtrudeGeometry(forma(poly), { depth: y1 - y0, bevelEnabled: false });
  const m = new THREE.Mesh(g, mat);
  m.rotation.x = -Math.PI / 2;
  m.position.y = y0;
  m.castShadow = sombra; m.receiveShadow = true;
  return m;
}
function plano(poly, y, mat) {
  if (!poly || poly.length < 3) return new THREE.Group();
  const g = new THREE.ShapeGeometry(forma(poly));
  const m = new THREE.Mesh(g, mat);
  m.rotation.x = -Math.PI / 2;
  m.position.y = y;
  m.receiveShadow = true;
  return m;
}
function caja(a, b, h0, h1, esp, mat, sombra = true) {
  const dx = b[0] - a[0], dv = b[1] - a[1];
  const L = Math.hypot(dx, dv);
  const m = new THREE.Mesh(new THREE.BoxGeometry(L, h1 - h0, esp), mat);
  m.position.set((a[0] + b[0]) / 2, (h0 + h1) / 2, -(a[1] + b[1]) / 2);
  m.rotation.y = Math.atan2(dv, dx);
  m.castShadow = sombra; m.receiveShadow = true;
  return m;
}
function poste(p, h0, h1, lado, mat) {
  const m = new THREE.Mesh(new THREE.BoxGeometry(lado, h1 - h0, lado), mat);
  m.position.set(X(p), (h0 + h1) / 2, Z(p));
  m.castShadow = true; m.receiveShadow = true;
  return m;
}
function interp(a, b, k) { return [a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k]; }
function rotar(p, c, ang) {
  const s = Math.sin(ang), co = Math.cos(ang);
  return [c[0] + (p[0] - c[0]) * co - (p[1] - c[1]) * s, c[1] + (p[0] - c[0]) * s + (p[1] - c[1]) * co];
}

// ------------------------------------------------------------------ renderer, cielo y luz
const canvas = document.getElementById('lienzo');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(1);
renderer.setSize(ANCHO, ALTO, false);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 0.95;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(40, ANCHO / ALTO, 0.3, 2500);

const sky = new Sky();
sky.scale.setScalar(4000);
const su = sky.material.uniforms;
su.turbidity.value = 2.8; su.rayleigh.value = 2.2; su.mieCoefficient.value = 0.004; su.mieDirectionalG.value = 0.82;
scene.add(sky);
const norte = new THREE.Vector3(D.meta.norte[0], 0, -D.meta.norte[1]).normalize();
const oeste = new THREE.Vector3(norte.z, 0, -norte.x);
const lote = D.lote;
const centro = new THREE.Vector3(lote.reduce((s, p) => s + p[0], 0) / lote.length, 0,
  -lote.reduce((s, p) => s + p[1], 0) / lote.length);
const elev = THREE.MathUtils.degToRad(40);
const dirSol = oeste.clone().multiplyScalar(Math.cos(elev) * 0.8).add(norte.clone().multiplyScalar(Math.cos(elev) * 0.45));
dirSol.y = Math.sin(elev); dirSol.normalize();
su.sunPosition.value.copy(dirSol);
const sol = new THREE.DirectionalLight(0xffeccc, 2.6);
sol.position.copy(centro).addScaledVector(dirSol, 120);
sol.target.position.copy(centro);
sol.castShadow = true;
sol.shadow.mapSize.set(4096, 4096);
const sc = sol.shadow.camera;
sc.left = -45; sc.right = 45; sc.top = 45; sc.bottom = -45; sc.near = 20; sc.far = 260;
sol.shadow.bias = -0.0004; sol.shadow.normalBias = 0.03;
scene.add(sol, sol.target);
scene.add(new THREE.HemisphereLight(0xe0e7ee, 0x5d5444, 0.45));
{
  const pmrem = new THREE.PMREMGenerator(renderer);
  const s2 = new THREE.Scene();
  const sk = new Sky(); sk.scale.setScalar(4000);
  Object.keys(su).forEach((k) => { if (sk.material.uniforms[k]) sk.material.uniforms[k].value = su[k].value; });
  s2.add(sk);
  const pis = new THREE.Mesh(new THREE.CircleGeometry(3000, 32), new THREE.MeshBasicMaterial({ color: 0xb7b19f }));
  pis.rotation.x = -Math.PI / 2; pis.position.y = -2; s2.add(pis);
  scene.environment = pmrem.fromScene(s2, 0.02).texture;
}
scene.fog = new THREE.FogExp2(0xbac8d2, 0.0005);

// ------------------------------------------------------------------ materiales
const rep = (t, r) => { t.repeat.set(r, r); return t; };
const M = {
  pasto: new THREE.MeshStandardMaterial({ map: rep(texPasto(31), 0.25), roughness: 0.95, color: 0xdfeacb }),
  seto: new THREE.MeshStandardMaterial({ color: 0x3f6b2b, roughness: 0.95 }),
  adoquin: new THREE.MeshStandardMaterial({ map: rep(texAdoquin(7), 0.35), roughness: 0.85, color: 0xd9d4cc }),
  laja: new THREE.MeshStandardMaterial({ map: rep(texConcreto([196, 176, 140], 9), 0.3), roughness: 0.9 }),
  concreto: new THREE.MeshStandardMaterial({ map: rep(texConcreto([186, 184, 178], 5), 0.25), roughness: 0.9 }),
  tarrajeo: new THREE.MeshStandardMaterial({ map: rep(texTarrajeo([236, 226, 204], 3), 0.5), roughness: 0.92 }),
  tarrajeoBlanco: new THREE.MeshStandardMaterial({ map: rep(texTarrajeo([240, 238, 232], 4), 0.5), roughness: 0.92 }),
  muroVecino: new THREE.MeshStandardMaterial({ map: rep(texTarrajeo([214, 205, 186], 8), 0.4), roughness: 0.95 }),
  piedra: new THREE.MeshStandardMaterial({ color: 0x8c8274, roughness: 0.95 }),
  madera: new THREE.MeshStandardMaterial({ color: 0x8a5a33, roughness: 0.7 }),
  maderaClara: new THREE.MeshStandardMaterial({ color: 0xb8875a, roughness: 0.65 }),
  acero: new THREE.MeshStandardMaterial({ color: 0x3b3f44, roughness: 0.45, metalness: 0.6 }),
  aceroClaro: new THREE.MeshStandardMaterial({ color: 0x9aa1a8, roughness: 0.35, metalness: 0.7 }),
  vidrio: new THREE.MeshPhysicalMaterial({ color: 0x9fc4d6, roughness: 0.05, metalness: 0.0, transparent: true,
    opacity: 0.32, side: THREE.DoubleSide, depthWrite: false }),
  vidrioOscuro: new THREE.MeshStandardMaterial({ color: 0x415a68, roughness: 0.15, metalness: 0.3 }),
  techo: new THREE.MeshStandardMaterial({ color: 0x9e4630, roughness: 0.75, side: THREE.DoubleSide }),
  techoInf: new THREE.MeshStandardMaterial({ color: 0xd8d2c4, roughness: 0.9, side: THREE.DoubleSide }),
  lona: new THREE.MeshStandardMaterial({ color: 0xf0e4c8, roughness: 0.85, side: THREE.DoubleSide }),
  mesa: new THREE.MeshStandardMaterial({ color: 0x9b6b40, roughness: 0.6 }),
  silla: new THREE.MeshStandardMaterial({ color: 0x2d2d2d, roughness: 0.6 }),
  mantel: new THREE.MeshStandardMaterial({ color: 0xf4f1ea, roughness: 0.85 }),
  agua: new THREE.MeshPhysicalMaterial({ color: 0x3fa7c9, roughness: 0.05, transmission: 0.2, transparent: true,
    opacity: 0.88 }),
  anden: new THREE.MeshStandardMaterial({ map: rep(texConcreto([214, 206, 188], 12), 0.3), roughness: 0.9 }),
  escenario: new THREE.MeshStandardMaterial({ color: 0x6b4a2e, roughness: 0.55 }),
  calamina: new THREE.MeshStandardMaterial({ color: 0x8e9396, roughness: 0.5, metalness: 0.5, side: THREE.DoubleSide }),
  hojas: new THREE.MeshStandardMaterial({ color: 0x4f7a32, roughness: 0.9, flatShading: true }),
  hojasPalma: new THREE.MeshStandardMaterial({ color: 0x5b8a34, roughness: 0.85, side: THREE.DoubleSide }),
  tronco: new THREE.MeshStandardMaterial({ color: 0x6b5238, roughness: 0.95 }),
  fuego: new THREE.MeshStandardMaterial({ color: 0x2b2b2b, roughness: 0.7, metalness: 0.4 }),
};

const G = new THREE.Group();
G.name = 'polleria';
scene.add(G);

// ------------------------------------------------------------------ pisos
G.add(plano(D.interior, 0.005, M.pasto));
for (const p of (ETAPA >= 2 ? D.pisos.setos2 : D.pisos.setos) || []) G.add(prisma(p, 0.0, 0.85, M.seto));
G.add(plano(D.pisos.calzada, 0.02, M.adoquin));
for (const pz of D.pisos.plazas) G.add(plano(pz.poly, 0.025, M.adoquin));
G.add(plano(D.pisos.motos, 0.025, M.adoquin));
G.add(plano(D.pisos.vereda, 0.03, M.laja));
for (const c of D.pisos.caminos) if (c.etapa <= ETAPA) G.add(plano(c.poly, 0.03, M.laja));
for (const p of D.pisos.porche) G.add(plano(p, 0.04, M.laja));
G.add(plano(E.envolvente1, 0.045, M.laja));
// líneas de las plazas
for (const pz of D.pisos.plazas) {
  const q = pz.poly;
  for (let i = 0; i < q.length; i++) {
    const a = q[i], b = q[(i + 1) % q.length];
    const m = caja(a, b, 0.03, 0.035, 0.1, new THREE.MeshStandardMaterial({ color: 0xf2f2f0, roughness: 0.8 }), false);
    G.add(m);
  }
}

// ------------------------------------------------------------------ cercos y vanos
const vanos = D.vanos.map((v) => ({ ...v, a: v.a, b: v.b }));
function tramosLibres(a, b) {
  // devuelve los tramos [k0, k1] del segmento a-b que no caen en un vano
  const L = Math.hypot(b[0] - a[0], b[1] - a[1]);
  const t = [(b[0] - a[0]) / L, (b[1] - a[1]) / L];
  const cortes = [];
  for (const v of vanos) {
    const ka = ((v.a[0] - a[0]) * t[0] + (v.a[1] - a[1]) * t[1]) / L;
    const kb = ((v.b[0] - a[0]) * t[0] + (v.b[1] - a[1]) * t[1]) / L;
    const dist = Math.abs((v.a[0] - a[0]) * t[1] - (v.a[1] - a[1]) * t[0]);
    if (dist < 0.5 && Math.max(ka, kb) > 0 && Math.min(ka, kb) < 1) cortes.push([Math.min(ka, kb), Math.max(ka, kb)]);
  }
  cortes.sort((p, q) => p[0] - q[0]);
  const out = []; let k = 0;
  for (const [k0, k1] of cortes) { if (k0 > k) out.push([k, k0]); k = Math.max(k, k1); }
  if (k < 1) out.push([k, 1]);
  return out;
}
{
  const [P0, P1, P2, P3] = lote;          // B, C, D, A
  const frentes = [[P3, P0], [P2, P3]];   // A-B (jirón) y D-A (calle lateral)
  for (const [a, b] of frentes) {
    for (const [k0, k1] of tramosLibres(a, b)) {
      const p = interp(a, b, k0), q = interp(a, b, k1);
      G.add(caja(p, q, 0, 0.6, 0.3, M.piedra));
      const L = Math.hypot(q[0] - p[0], q[1] - p[1]);
      const n = Math.max(1, Math.round(L / 2.0));
      for (let i = 0; i <= n; i++) {
        const r = interp(p, q, i / n);
        G.add(poste(r, 0.6, 1.85, 0.1, M.madera));
      }
      for (const y of [1.05, 1.5, 1.8]) G.add(caja(p, q, y - 0.04, y + 0.04, 0.05, M.madera));
    }
  }
  for (const [a, b] of [[P0, P1], [P1, P2]]) G.add(caja(a, b, 0, 2.4, 0.15, M.muroVecino));
  // portada principal P-1: postes y techito de teja
  const p1 = D.vanos.find((v) => v.codigo === 'P-1');
  for (const p of [p1.a, p1.b]) G.add(poste(p, 0, 2.7, 0.3, M.maderaClara));
  const cent = interp(p1.a, p1.b, 0.5);
  const L = Math.hypot(p1.b[0] - p1.a[0], p1.b[1] - p1.a[1]);
  const techito = new THREE.Mesh(new THREE.BoxGeometry(L + 0.8, 0.12, 1.3), M.techo);
  techito.position.set(X(cent), 2.82, Z(cent));
  techito.rotation.y = Math.atan2(p1.b[1] - p1.a[1], p1.b[0] - p1.a[0]);
  techito.castShadow = true;
  G.add(techito);
  const viga = caja(p1.a, p1.b, 2.55, 2.75, 0.2, M.maderaClara);
  G.add(viga);
}

// ------------------------------------------------------------------ preexistencias y caseta de GLP
{
  const ex = D.existentes;
  G.add(prisma(ex.lena.poly, 0, ex.lena.altura, M.madera));
  G.add(prisma(ex.lena.poly, ex.lena.altura, ex.lena.altura + 0.06, M.calamina));
  G.add(prisma(ex.garaje.poly, 0, ex.garaje.altura, M.tarrajeoBlanco));
  G.add(prisma(ex.garaje.poly, ex.garaje.altura, ex.garaje.altura + 0.12, M.concreto));
  G.add(prisma(D.pisos.glp, 0, 2.2, M.tarrajeoBlanco));
}

// ------------------------------------------------------------------ edificio
const EDIF = new THREE.Group();
G.add(EDIF);
{
  // columnas
  const conTecho = new Set(E.columnas_hasta_techo.map((p) => p.join(',')));
  for (const c of E.columnas) {
    const alto = conTecho.has(c.join(',')) ? E.alero : N2 + 1.1;
    EDIF.add(poste(c, 0, alto, E.columna_lado, M.acero));
  }
  // losa del 2.º piso con canto y vigas
  EDIF.add(prisma(E.losa2, N2 - 0.15, N2, M.concreto));
  const losa = E.losa2;
  for (let i = 0; i < losa.length; i++) {
    const a = losa[i], b = losa[(i + 1) % losa.length];
    EDIF.add(caja(a, b, N2 - 0.45, N2 - 0.15, 0.14, M.acero));
  }
  for (const s of E.ejes_s) EDIF.add(caja(SD(s, E.ejes_d[0]), SD(s, 24.8), N2 - 0.6, N2 - 0.15, 0.18, M.acero));
  for (const d of [14.23, 16.07, 17.9, 19.57, 21.23, 22.9, 23.9]) EDIF.add(caja(SD(5.6, d), SD(18.5, d), N2 - 0.42, N2 - 0.15, 0.13, M.acero));
  // muros del 1.er y 2.º piso
  const muro = (sg) => {
    const { a, b, tipo, h0, h1 } = sg;
    if (tipo === 'tabique' || tipo === 'pase' || tipo === 'puerta') return;
    if (tipo === 'vidrio' || tipo === 'vidrio_plegable' || tipo === 'puerta_vidrio') {
      EDIF.add(caja(a, b, h0, h1, 0.03, M.vidrio, false));
      EDIF.add(caja(a, b, h0, h0 + 0.06, 0.08, M.acero));
      EDIF.add(caja(a, b, h1 - 0.06, h1, 0.08, M.acero));
      const L = Math.hypot(b[0] - a[0], b[1] - a[1]);
      const n = Math.max(1, Math.round(L / (tipo === 'vidrio_plegable' ? 0.9 : 1.2)));
      for (let i = 0; i <= n; i++) {
        const p = interp(a, b, i / n);
        EDIF.add(poste(p, h0, h1, 0.05, M.acero));
      }
      return;
    }
    const esp = tipo === 'muro_acustico' ? 0.25 : 0.15;
    const mat = h0 > 1 ? M.tarrajeoBlanco : M.tarrajeo;
    if (tipo === 'muro_ventana_alta' || tipo === 'muro_ventana') {
      const L = Math.hypot(b[0] - a[0], b[1] - a[1]);
      const yv0 = tipo === 'muro_ventana_alta' ? h0 + 2.05 : h0 + 1.0;
      const yv1 = Math.min(h1 - 0.25, yv0 + (tipo === 'muro_ventana_alta' ? 0.7 : 1.3));
      EDIF.add(caja(a, b, h0, yv0, esp, mat));
      EDIF.add(caja(a, b, yv1, h1, esp, mat));
      let k = 0.6;
      let prev = 0;
      while (k + 2.0 <= L - 0.4) {
        EDIF.add(caja(interp(a, b, prev / L), interp(a, b, k / L), yv0, yv1, esp, mat));
        EDIF.add(caja(interp(a, b, k / L), interp(a, b, (k + 2.0) / L), yv0, yv1, 0.04, M.vidrioOscuro));
        prev = k + 2.0; k += 2.75;
      }
      EDIF.add(caja(interp(a, b, prev / L), b, yv0, yv1, esp, mat));
      return;
    }
    EDIF.add(caja(a, b, h0, h1, esp, tipo === 'muro_acustico' ? M.maderaClara : mat));
  };
  E.muros1.forEach(muro);
  E.muros2.forEach(muro);
  // barandas de vidrio de la terraza
  for (const bd of E.barandas) {
    EDIF.add(caja(bd.a, bd.b, N2, N2 + bd.h, 0.025, M.vidrio, false));
    EDIF.add(caja(bd.a, bd.b, N2 + bd.h - 0.04, N2 + bd.h + 0.02, 0.07, M.aceroClaro));
  }
  // escenario
  EDIF.add(prisma(E.escenario.poly, N2, N2 + E.escenario.altura, M.escenario));
  // techos a dos aguas
  for (const t of E.techos) {
    const esq = t.esquinas, cum = t.cumbrera;
    const tg = [cum[1][0] - cum[0][0], cum[1][1] - cum[0][1]];
    const Lr = Math.hypot(...tg);
    const par = (a, b) => Math.abs(((b[0] - a[0]) * tg[1] - (b[1] - a[1]) * tg[0]) / (Lr * Math.hypot(b[0] - a[0], b[1] - a[1]))) < 0.05;
    const cerca = (p) => (Math.hypot(p[0] - cum[0][0], p[1] - cum[0][1]) < Math.hypot(p[0] - cum[1][0], p[1] - cum[1][1]) ? cum[0] : cum[1]);
    const vert = [], vertI = [];
    for (let i = 0; i < 4; i++) {
      const a = esq[i], b = esq[(i + 1) % 4];
      if (par(a, b)) {
        const ca = cerca(a), cb = cerca(b);
        const quad = [[a, t.alero], [b, t.alero], [cb, t.h_cumbrera], [ca, t.h_cumbrera]];
        const P = quad.map(([p, y]) => new THREE.Vector3(X(p), y, Z(p)));
        vert.push(P[0], P[1], P[2], P[0], P[2], P[3]);
      } else {
        const c = cerca(a);
        const P = [V3(a, t.alero), V3(b, t.alero), V3(c, t.h_cumbrera)];
        vertI.push(...P);
      }
    }
    const geo = new THREE.BufferGeometry().setFromPoints(vert);
    geo.computeVertexNormals();
    const techo = new THREE.Mesh(geo, M.techo);
    techo.castShadow = true; techo.receiveShadow = true;
    EDIF.add(techo);
    const geoI = new THREE.BufferGeometry().setFromPoints(vertI);
    geoI.computeVertexNormals();
    const hastial = new THREE.Mesh(geoI, new THREE.MeshStandardMaterial({ color: 0xd9cbb5, roughness: 0.9, side: THREE.DoubleSide }));
    hastial.castShadow = true;
    EDIF.add(hastial);
  }
  // chimenea de los hornos
  for (const sc_ of [10.7, 12.8]) {
    const p = SD(sc_, 12.3);
    const ch = new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.2, E.chimenea.altura - N2, 16), M.aceroClaro);
    ch.position.set(X(p), (N2 + E.chimenea.altura) / 2, Z(p));
    ch.castShadow = true;
    EDIF.add(ch);
    const som = new THREE.Mesh(new THREE.ConeGeometry(0.38, 0.3, 16), M.acero);
    som.position.set(X(p), E.chimenea.altura + 0.25, Z(p));
    EDIF.add(som);
  }
  // ascensor panorámico
  const asc = E.ascensor;
  for (const p of asc) EDIF.add(poste(p, 0, N2 + 3.4, 0.1, M.aceroClaro));
  for (let i = 0; i < 4; i++) {
    const a = asc[i], b = asc[(i + 1) % 4];
    EDIF.add(caja(a, b, 0.05, N2 + 3.35, 0.03, M.vidrio, false));
    for (const y of [0.1, N2, N2 + 3.35]) EDIF.add(caja(a, b, y - 0.05, y + 0.05, 0.08, M.aceroClaro));
  }
  EDIF.add(prisma(asc, N2 + 3.35, N2 + 3.5, M.aceroClaro));
  // escalera exterior (tramos de 10 pasos)
  const ee = E.escalera_exterior;
  const [s0, s1, s2, s3, s4, s5] = ee.s;
  const dd0 = ee.d0, dd1 = ee.d1;
  const peld = (sa, sb, y) => EDIF.add(prisma([SD(sa, dd0), SD(sb, dd0), SD(sb, dd1), SD(sa, dd1)], y - 0.05, y, M.acero));
  for (let i = 0; i < 11; i++) peld(s1 + i * ee.huella, s1 + (i + 1) * ee.huella, (i + 1) * ee.contrapaso);
  peld(s2, s3, 11 * ee.contrapaso);
  for (let i = 0; i < 11; i++) peld(s3 + i * ee.huella, s3 + (i + 1) * ee.huella, (11 + i + 1) * ee.contrapaso);
  peld(s4, s5, N2);
  for (const [sa, sb, ya, yb] of [[s1, s2, 0, 11 * ee.contrapaso], [s3, s4, 11 * ee.contrapaso, N2]]) {
    const a = SD(sa, dd0 + 0.03), b = SD(sb, dd0 + 0.03);
    const L = Math.hypot(b[0] - a[0], b[1] - a[1]);
    const zanca = new THREE.Mesh(new THREE.BoxGeometry(L, 0.25, 0.08), M.acero);
    const c = interp(a, b, 0.5);
    zanca.position.set(X(c), (ya + yb) / 2 - 0.1, Z(c));
    zanca.rotation.order = 'YZX';
    zanca.rotation.y = Math.atan2(b[1] - a[1], b[0] - a[0]);
    zanca.rotation.z = Math.atan2(yb - ya, L);
    zanca.castShadow = true;
    EDIF.add(zanca);
  }
  for (const s of [s2, s3, s4, s5]) EDIF.add(poste(SD(s, dd0 + 0.05), 0, s >= s4 ? N2 + 1.0 : 11 * ee.contrapaso + 1.0, 0.08, M.acero));
  // barra del bar
  EDIF.add(prisma(E.barra2, N2, N2 + 1.1, M.maderaClara));
}

// ------------------------------------------------------------------ mesas, sombrillas y árboles
function mesaCuadrada(poly, y0, mat = M.mesa) {
  const g = new THREE.Group();
  const cx = poly.reduce((s, p) => s + p[0], 0) / poly.length, cv = poly.reduce((s, p) => s + p[1], 0) / poly.length;
  const lado = Math.hypot(poly[1][0] - poly[0][0], poly[1][1] - poly[0][1]);
  const top = new THREE.Mesh(new THREE.BoxGeometry(lado, 0.05, lado), mat);
  top.position.set(cx, y0 + 0.75, -cv); top.castShadow = true; g.add(top);
  const pata = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.04, 0.72, 8), M.acero);
  pata.position.set(cx, y0 + 0.37, -cv); g.add(pata);
  const r = lado / 2 + 0.3;
  const lados = lado < 0.75 ? [[0, r], [0, -r]] : [[r, 0], [-r, 0], [0, r], [0, -r]];
  const ang = Math.atan2(poly[1][1] - poly[0][1], poly[1][0] - poly[0][0]);
  for (const [dx, dz] of lados) {
    const p = rotar([cx + dx, cv + dz], [cx, cv], ang);
    const s = new THREE.Mesh(new THREE.BoxGeometry(0.42, 0.45, 0.42), M.silla);
    s.position.set(p[0], y0 + 0.225, -p[1]); s.castShadow = true; g.add(s);
  }
  return g;
}
for (const m of D.mesas_1) G.add(mesaCuadrada(m, 0.04));
for (const m of D.mesas_2) G.add(mesaCuadrada(m, N2));

function sombrilla(s) {
  const g = new THREE.Group();
  const h = s.lado / 2;
  const mastil = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.035, 2.85, 10), M.aceroClaro);
  mastil.position.y = 1.425; mastil.castShadow = true; g.add(mastil);
  const v = [[-h, -h], [h, -h], [h, h], [-h, h]];
  const pts = [];
  for (let i = 0; i < 4; i++) {
    const a = v[i], b = v[(i + 1) % 4];
    pts.push(new THREE.Vector3(a[0], 2.2, a[1]), new THREE.Vector3(b[0], 2.2, b[1]), new THREE.Vector3(0, 2.75, 0));
  }
  const geo = new THREE.BufferGeometry().setFromPoints(pts);
  geo.computeVertexNormals();
  const lona = new THREE.Mesh(geo, M.lona);
  lona.castShadow = true; lona.receiveShadow = true;
  g.add(lona);
  for (let i = 0; i < 4; i++) {                     // faldón
    const a = v[i], b = v[(i + 1) % 4];
    const f = new THREE.Mesh(new THREE.BoxGeometry(s.lado, 0.22, 0.01), M.lona);
    f.position.set((a[0] + b[0]) / 2, 2.1, (a[1] + b[1]) / 2);
    f.rotation.y = -Math.atan2(b[1] - a[1], b[0] - a[0]);
    g.add(f);
  }
  // mesa y sillas
  const larga = s.mesa === '6';
  if (s.mesa === '6' || s.mesa === '4') {
    const top = new THREE.Mesh(new THREE.BoxGeometry(larga ? 1.8 : 0.9, 0.05, 0.9), M.mesa);
    top.position.y = 0.75; top.castShadow = true; g.add(top);
    for (const [dx, dz] of (larga ? [[-0.75, -0.35], [0.75, -0.35], [-0.75, 0.35], [0.75, 0.35]] : [[0, 0]])) {
      const pata = new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.72, 0.06), M.mesa);
      pata.position.set(dx, 0.36, dz); g.add(pata);
    }
    const sillas = larga ? [[-0.6, 0.8], [0, 0.8], [0.6, 0.8], [-0.6, -0.8], [0, -0.8], [0.6, -0.8]]
      : [[0, 0.8], [0, -0.8], [0.8, 0], [-0.8, 0]];
    for (const [dx, dz] of sillas) {
      const si = new THREE.Mesh(new THREE.BoxGeometry(0.42, 0.45, 0.42), M.silla);
      si.position.set(dx, 0.225, dz); si.castShadow = true; g.add(si);
      const resp = new THREE.Mesh(new THREE.BoxGeometry(0.42, 0.45, 0.04), M.silla);
      resp.position.set(dx, 0.67, dz + Math.sign(dz || 1) * 0.2); g.add(resp);
    }
  }
  g.position.set(X(s.centro), 0.01, Z(s.centro));
  g.rotation.y = THREE.MathUtils.degToRad(s.ang + (larga ? 90 : 0));
  return g;
}
if (!EVENTO) {
  for (const s of D.sombrillas) if (s.etapas.includes(ETAPA)) G.add(sombrilla(s));
} else {
  for (const c of D.pisos.mesas_evento) {
    const g = new THREE.Group();
    const top = new THREE.Mesh(new THREE.CylinderGeometry(0.75, 0.75, 0.05, 32), M.mantel);
    top.position.y = 0.76; top.castShadow = true; g.add(top);
    const falda = new THREE.Mesh(new THREE.CylinderGeometry(0.76, 0.78, 0.7, 32, 1, true), M.mantel);
    falda.position.y = 0.4; g.add(falda);
    for (let k = 0; k < 8; k++) {
      const a = (k / 8) * Math.PI * 2;
      const si = new THREE.Mesh(new THREE.BoxGeometry(0.42, 0.9, 0.42), new THREE.MeshStandardMaterial({ color: 0xf6f3ec, roughness: 0.7 }));
      si.position.set(Math.cos(a) * 1.15, 0.45, Math.sin(a) * 1.15); si.castShadow = true; g.add(si);
    }
    g.position.set(X(c), 0.01, Z(c));
    G.add(g);
  }
}

const azar = (() => { let a = 12345; return () => { a = (a * 1103515245 + 12345) % 2147483648; return a / 2147483648; }; })();
function arbol(a) {
  const g = new THREE.Group();
  const r = a.copa / 2;
  if (a.tipo === 'palmera') {
    const h = 4.2 + r;
    const tr = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.18, h, 8), M.tronco);
    tr.position.y = h / 2; tr.castShadow = true; g.add(tr);
    for (let k = 0; k < 9; k++) {
      const hoja = new THREE.Mesh(new THREE.ConeGeometry(0.28, r * 2.2, 4, 1, true), M.hojasPalma);
      hoja.position.y = h;
      hoja.rotation.z = Math.PI / 2 - 0.35;
      const piv = new THREE.Group(); piv.add(hoja); hoja.position.set(r * 1.0, h - 0.25, 0);
      piv.rotation.y = (k / 9) * Math.PI * 2 + azar() * 0.3;
      piv.children[0].castShadow = true;
      g.add(piv);
    }
  } else {
    const h = a.tipo === 'arbusto' ? 0.9 : 2.6 + r;
    const tr = new THREE.Mesh(new THREE.CylinderGeometry(0.1, 0.16, h, 8), M.tronco);
    tr.position.y = h / 2; tr.castShadow = true; g.add(tr);
    for (let k = 0; k < 6; k++) {
      const bola = new THREE.Mesh(new THREE.IcosahedronGeometry(r * (0.55 + azar() * 0.25), 1), M.hojas);
      bola.position.set((azar() - 0.5) * r, h + (azar() - 0.2) * r * 0.6, (azar() - 0.5) * r);
      bola.castShadow = true; bola.receiveShadow = true;
      g.add(bola);
    }
  }
  g.position.set(X(a.p), 0, Z(a.p));
  return g;
}
for (const a of D.arboles) if ((a.etapa || 1) <= ETAPA) G.add(arbol(a));

// ------------------------------------------------------------------ piscina (2.ª etapa)
if (ETAPA >= 2) {
  const P = D.piscina;
  G.add(prisma(P.anden, 0.0, 0.08, M.anden));
  G.add(prisma(P.relajo, 0.0, 0.06, M.maderaClara));
  G.add(prisma(P.poly, 0.0, 0.085, M.agua));
  G.add(prisma(P.ninos, 0.0, 0.085, M.agua));
  G.add(prisma(P.pediluvio, 0.0, 0.07, M.agua));
  for (const pol of [P.vest_damas, P.vest_varones, P.cuarto_maquinas]) G.add(prisma(pol, 0, P.altura_vestidores, M.tarrajeoBlanco));
  G.add(prisma(P.vestidores, P.altura_vestidores, P.altura_vestidores + 0.15, M.concreto));
  G.add(prisma(P.paso_limpio, 0, 0.06, M.anden));
  for (let i = 0; i < P.cerco.length - 1; i++) {
    G.add(caja(P.cerco[i], P.cerco[i + 1], 0.05, P.cerco_altura, 0.02, M.vidrio, false));
    G.add(caja(P.cerco[i], P.cerco[i + 1], P.cerco_altura - 0.03, P.cerco_altura + 0.02, 0.05, M.aceroClaro));
  }
  for (const c of P.camillas) G.add(prisma(c, 0.25, 0.4, new THREE.MeshStandardMaterial({ color: 0xf4f4f0, roughness: 0.6 })));
  for (const h of P.hamacas) G.add(prisma(h, 0.45, 0.55, new THREE.MeshStandardMaterial({ color: 0xd9a441, roughness: 0.8 })));
}

// ------------------------------------------------------------------ autos
{
  const tipos = ['suv', 'sedan', 'pickup', 'hatchback'];
  D.autos.forEach((a, i) => {
    const v = crearVehiculo(a.tipo || tipos[i % 4], { color: COLORES_AUTOS[(i * 3 + 1) % COLORES_AUTOS.length], seed: 40 + i });
    const f = [a.frente[0], -a.frente[1]];
    const hx = -f[0], hz = -f[1];                // de culata hacia el cerco, frente a la calzada
    v.position.set(X(a.centro), 0.03, Z(a.centro));
    v.rotation.y = Math.atan2(-hz, hx);
    scene.add(v);
  });
}

// ------------------------------------------------------------------ entorno urbano (del recorrido del estacionamiento)
{
  const v1 = D.vanos.find((v) => v.codigo === 'V-1');
  const a = [v1.a[0], -v1.a[1]], b = [v1.b[0], -v1.b[1]];
  const ctx = { ...ctxParking, accesos: [{ codigo: 'V-1', tipo: 'porton', a, b, centro: [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2] }] };
  crearEntorno(scene, ctx, { renderer, camera });
}

// reflejos moderados
scene.traverse((o) => [].concat(o.material || []).forEach((m) => { if (m && 'envMapIntensity' in m) m.envMapIntensity = 0.5; }));

function ajustarSombra(alta) {
  const R = alta ? 70 : 45;
  sc.left = sc.bottom = -R; sc.right = sc.top = R;
  sc.updateProjectionMatrix();
}
function vista(pos, obj, fov = 40) {
  camera.fov = fov;
  camera.position.set(...pos);
  camera.lookAt(new THREE.Vector3(...obj));
  camera.updateProjectionMatrix();
  ajustarSombra(pos[1] > 20);
  renderer.render(scene, camera);
}
window.APP = { vista, centro: centro.toArray(), SD: (s, d) => { const p = SD(s, d); return [X(p), Z(p)]; },
  punto: (p) => [X(p), Z(p)], datos: D, scene, camera, renderer };
if (VISOR) {
  const controls = new OrbitControls(camera, canvas);
  controls.target.copy(centro);
  camera.position.copy(centro).add(new THREE.Vector3(-40, 35, 40));
  controls.update();
  renderer.setAnimationLoop(() => { controls.update(); renderer.render(scene, camera); });
}
window.APP.listo = true;
