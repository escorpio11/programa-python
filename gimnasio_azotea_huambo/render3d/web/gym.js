// AZOTEA GYM - modelo 3D (three.js) a partir de escena.json (generado por diseno.py).
// Convención: x del plano -> X, y del plano -> Z, altura -> Y.
// Parámetros de URL: ?w=&h= tamaño | &modo=noche | &visor=1 (órbita + botones) | &gente=0 | &ao=0
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { Reflector } from 'three/addons/objects/Reflector.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { GTAOPass } from 'three/addons/postprocessing/GTAOPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { MAT, G, caja, viga, tubo, cojin, crearMaquina, portaDiscos, persona } from './maquinas.js';

const OPC = Object.assign({}, Object.fromEntries(new URLSearchParams(location.search)), window.GYM_OPC || {});
const canvas = OPC.canvas || document.getElementById('lienzo');
const VISOR = OPC.visor === '1' || OPC.visor === true;
let ANCHO = +OPC.w || canvas.clientWidth || window.innerWidth;
let ALTO = +OPC.h || canvas.clientHeight || window.innerHeight;
let NOCHE = OPC.modo === 'noche';
const CON_AO = OPC.ao !== '0' && OPC.ao !== false;
const VER = String(OPC.ver || 'A').toUpperCase();
const D = await (await fetch(new URL(`./escena${VER === 'A' ? '' : '_' + VER}.json`, import.meta.url))).json();
const { L, W, T } = D;
const XC = D.x_cercha, HT = D.h_techo;

// ------------------------------------------------------------------ utilidades
const std = (color, rough, metal, extra = {}) => new THREE.MeshStandardMaterial({ color, roughness: rough, metalness: metal, ...extra });
function hTecho(x) {                       // altura libre bajo cercha
  const p = Object.keys(HT).map((k) => [XC[k], HT[k]]).sort((a, b) => a[0] - b[0]);
  let i = 0;
  while (i < p.length - 2 && x > p[i + 1][0]) i++;
  const [xa, ha] = p[i], [xb, hb] = p[i + 1];
  return ha + (hb - ha) * (x - xa) / (xb - xa);
}
function lienzo(w, h, pintar) {
  const c = document.createElement('canvas'); c.width = w; c.height = h;
  pintar(c.getContext('2d'), w, h);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8;
  return t;
}
function repetir(t, rx, ry) { t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(rx, ry); return t; }
let _sem = 7;
const azar = () => { _sem = (_sem * 16807) % 2147483647; return (_sem - 1) / 2147483646; };
const FUENTE = '"Inter Display", "Inter", "Helvetica Neue", Arial, sans-serif';

// ------------------------------------------------------------------ texturas de lienzo
const texCaucho = (moteado = '#8a8e96', prob = 0.12) => repetir(lienzo(512, 512, (c, w, h) => {
  c.fillStyle = '#35373b'; c.fillRect(0, 0, w, h);
  for (let i = 0; i < 5200; i++) {
    const g = 44 + Math.floor(azar() * 24); c.fillStyle = `rgb(${g},${g},${g + 2})`;
    c.fillRect(azar() * w, azar() * h, 1 + azar() * 2, 1 + azar() * 2);
  }
  for (let i = 0; i < 2600; i++) { c.fillStyle = azar() < prob ? '#d2d5da' : moteado; c.globalAlpha = 0.4 + azar() * 0.5; c.fillRect(azar() * w, azar() * h, 1 + azar() * 1.6, 1 + azar() * 1.6); }
  c.globalAlpha = 1; c.strokeStyle = '#1f2023'; c.lineWidth = 3; c.strokeRect(0, 0, w, h);
}), 1, 1);
const texGrass = () => repetir(lienzo(512, 512, (c, w, h) => {
  c.fillStyle = '#3c8a3a'; c.fillRect(0, 0, w, h);
  for (let i = 0; i < 9000; i++) {
    const v = azar(); c.strokeStyle = v < 0.33 ? '#2f7431' : v < 0.66 ? '#4fa449' : '#3f9340'; c.globalAlpha = 0.6;
    const x = azar() * w, y = azar() * h; c.beginPath(); c.moveTo(x, y); c.lineTo(x + (azar() - 0.5) * 5, y + 4 + azar() * 6); c.stroke();
  }
}), 0.8, 0.8);
const texVinilico = () => repetir(lienzo(1024, 512, (c, w, h) => {
  const filas = 6, alto = h / filas;
  for (let f = 0; f < filas; f++) {
    const desfase = (f % 2) * w * 0.37;
    for (let k = -1; k < 2; k++) {
      const x = k * w / 1.6 + desfase, t = 150 + Math.floor(azar() * 26);
      c.fillStyle = `rgb(${t + 44},${t + 12},${t - 34})`; c.fillRect(x, f * alto, w / 1.6, alto);
      for (let i = 0; i < 60; i++) { c.strokeStyle = `rgba(110,78,40,${0.05 + azar() * 0.12})`; c.beginPath(); const y = f * alto + azar() * alto; c.moveTo(x, y); c.bezierCurveTo(x + w * 0.2, y + (azar() - 0.5) * 6, x + w * 0.4, y + (azar() - 0.5) * 6, x + w / 1.6, y); c.stroke(); }
      c.strokeStyle = 'rgba(70,48,24,0.55)'; c.lineWidth = 1.5; c.strokeRect(x, f * alto, w / 1.6, alto);
    }
  }
}), 1 / 2.4, 1 / 1.2);
const texBaldosa = () => repetir(lienzo(256, 256, (c, w, h) => {
  c.fillStyle = '#d9dcdd'; c.fillRect(0, 0, w, h);
  for (let i = 0; i < 900; i++) { c.fillStyle = `rgba(120,125,130,${azar() * 0.12})`; c.fillRect(azar() * w, azar() * h, 2, 2); }
  c.strokeStyle = '#a9adb0'; c.lineWidth = 3; c.strokeRect(0, 0, w, h);
}), 1 / 0.3, 1 / 0.3);
const texMuro = (base = [44, 46, 51]) => repetir(lienzo(256, 256, (c, w, h) => {
  c.fillStyle = `rgb(${base})`; c.fillRect(0, 0, w, h);
  for (let i = 0; i < 2600; i++) { const d = (azar() - 0.5) * 12; c.fillStyle = `rgba(${base[0] + d},${base[1] + d},${base[2] + d},0.5)`; c.fillRect(azar() * w, azar() * h, 2 + azar() * 4, 2 + azar() * 4); }
}), 0.6, 0.6);
const texCalamina = () => lienzo(256, 64, (c, w, h) => {
  const g = c.createLinearGradient(0, 0, w, 0);
  for (let i = 0; i <= 8; i++) { const k = i / 8; g.addColorStop(k, i % 2 ? '#8f959c' : '#cfd3d8'); }
  c.fillStyle = g; c.fillRect(0, 0, w, h);
});
const texPoli = () => repetir(lienzo(128, 64, (c, w, h) => {
  c.fillStyle = '#f4f6f6'; c.fillRect(0, 0, w, h);
  for (let x = 0; x < w; x += 8) { c.fillStyle = 'rgba(160,172,178,0.5)'; c.fillRect(x, 0, 1.5, h); }
}), 4, 1);
function texLogo() {
  return lienzo(1024, 1570, (c, w, h) => {
    c.fillStyle = '#0f1012'; c.fillRect(0, 0, w, h);
    // montañas + mancuerna
    c.strokeStyle = '#e02a2e'; c.lineWidth = 14; c.lineJoin = 'round'; c.beginPath();
    c.moveTo(210, 520); c.lineTo(400, 300); c.lineTo(500, 410); c.lineTo(610, 250); c.lineTo(814, 520); c.stroke();
    c.fillStyle = '#f4f4f1'; c.fillRect(250, 548, 524, 20);
    for (const x of [214, 762]) { c.fillRect(x, 508, 48, 100); } for (const x of [172, 818]) { c.fillRect(x, 528, 34, 60); }
    c.textAlign = 'center'; c.fillStyle = '#f4f4f1'; c.font = `900 200px ${FUENTE}`; c.fillText('AZOTEA', w / 2, 850);
    c.fillStyle = '#e02a2e'; c.font = `900 290px ${FUENTE}`; c.fillText('GYM', w / 2, 1110);
    c.fillStyle = '#c9cbd0'; c.font = `600 46px ${FUENTE}`; c.fillText('ENTRENA EN LAS ALTURAS', w / 2, 1215);
    c.fillStyle = '#7d8087'; c.font = `500 36px ${FUENTE}`; c.fillText('HUAMBO  ·  AMAZONAS', w / 2, 1290);
    c.fillStyle = '#e02a2e'; c.fillRect(392, 1330, 240, 8);
  });
}
function texMural() {
  return lienzo(1400, 1024, (c, w, h) => {
    c.fillStyle = '#c4181f'; c.fillRect(0, 0, w, h);
    c.fillStyle = 'rgba(0,0,0,0.16)';
    for (let i = -6; i < 16; i++) { c.beginPath(); c.moveTo(i * 150, h); c.lineTo(i * 150 + 70, h); c.lineTo(i * 150 + 70 + h * 0.6, 0); c.lineTo(i * 150 + h * 0.6, 0); c.fill(); }
    c.fillStyle = '#ffffff'; c.textAlign = 'left'; c.font = `900 205px ${FUENTE}`;
    c.fillText('MÁS', 90, 300); c.fillText('FUERTE', 90, 500);
    c.fillStyle = '#111214'; c.fillText('CADA DÍA', 90, 700);
    c.fillStyle = '#ffffff'; c.font = `700 62px ${FUENTE}`; c.fillText('AZOTEA GYM · HUAMBO', 96, 840);
  });
}
function texLetrero(txt, fondo = '#111214', color = '#f4f4f1') {
  return lienzo(768, 160, (c, w, h) => {
    c.fillStyle = fondo; c.fillRect(0, 0, w, h); c.fillStyle = '#e02a2e'; c.fillRect(0, h - 14, w, 14);
    c.fillStyle = color; c.textAlign = 'center'; c.textBaseline = 'middle'; c.font = `800 78px ${FUENTE}`; c.fillText(txt, w / 2, h / 2 - 6);
  });
}
function texPuerta(txt) {
  return lienzo(256, 256, (c, w, h) => {
    c.fillStyle = '#17181b'; c.fillRect(0, 0, w, h); c.fillStyle = '#f4f4f1';
    c.beginPath(); c.arc(128, 62, 26, 0, 7); c.fill(); c.fillRect(96, 96, 64, 78); c.fillRect(100, 170, 24, 44); c.fillRect(132, 170, 24, 44);
    c.textAlign = 'center'; c.font = `800 30px ${FUENTE}`; c.fillText(txt, w / 2, 246);
  });
}

// ------------------------------------------------------------------ materiales de arquitectura
const M_ = {
  caucho: std(0xffffff, 0.92, 0, { map: repetir(texCaucho(), 1, 1) }),
  cauchoPL: std(0xffffff, 0.92, 0, { map: repetir(texCaucho('#b0383c', 0.06), 1, 1) }),
  grass: std(0xffffff, 0.95, 0, { map: texGrass() }),
  vinilico: std(0xffffff, 0.55, 0, { map: texVinilico() }),
  baldosa: std(0xffffff, 0.35, 0, { map: texBaldosa() }),
  losa: std(0xb9b6ae, 0.9, 0),
  parapeto: std(0xffffff, 0.88, 0, { map: texMuro([46, 48, 53]) }),
  bano: std(0xffffff, 0.85, 0, { map: texMuro([232, 230, 224]) }),
  banoInt: std(0xeef1f2, 0.4, 0),
  concreto: std(0x8f8e89, 0.9, 0),
  acero: std(0x141517, 0.5, 0.6),
  aceroGris: std(0x55585d, 0.5, 0.7),
  calamina: std(0xc4c8cd, 0.42, 0.75, { side: THREE.DoubleSide }),
  madera: std(0xb07f45, 0.62, 0),
  maderaOsc: std(0x7b5630, 0.6, 0),
  negroMate: std(0x121315, 0.7, 0.1),
  blanco: std(0xf3f3f0, 0.6, 0),
  rojo: std(0xd81f26, 0.5, 0.1),
  panel: std(0xffffff, 0.85, 0, { map: texMuro([38, 40, 44]) }),
  vidrio: new THREE.MeshPhysicalMaterial({ color: 0xcfe6ee, roughness: 0.05, metalness: 0, transparent: true, opacity: 0.16, side: THREE.DoubleSide, depthWrite: false }),
  poli: std(0xf2f5f5, 0.6, 0, { map: texPoli(), transparent: true, opacity: 0.9, side: THREE.DoubleSide, emissive: 0xffffff, emissiveIntensity: 0.32 }),
  luz: std(0xfafcfd, 0.6, 0, { map: texPoli(), emissive: 0xffffff, emissiveIntensity: 0.8, side: THREE.DoubleSide }),
  transl: std(0xffffff, 0.6, 0, { emissive: 0xffffff, emissiveIntensity: 1.2, side: THREE.DoubleSide, transparent: true, opacity: 0.92 }),
  led: std(0xffffff, 0.4, 0, { emissive: 0xffffff, emissiveIntensity: 2.2 }),
  ledRojo: std(0xff3b3b, 0.4, 0, { emissive: 0xff2222, emissiveIntensity: 1.6 }),
  hoja: std(0x2f7d3b, 0.7, 0, { side: THREE.DoubleSide }),
  tanque: std(0x151618, 0.6, 0.1),
  loza: std(0xf7f7f5, 0.25, 0.05),
};
{ const t = texCalamina(); t.wrapS = t.wrapT = THREE.RepeatWrapping; M_.calamina.map = t; M_.calamina.bumpMap = t; M_.calamina.bumpScale = 0.6; }

// ------------------------------------------------------------------ escena y render
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(VISOR ? Math.min(window.devicePixelRatio, 2) : 1);
renderer.setSize(ANCHO, ALTO, false);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.05;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(55, ANCHO / ALTO, 0.08, 2500);
const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;

const grupos = { techo: G(), cerramientoAlto: G(), gente: G(), entorno: G(), fijo: G(), techoBano: G() };
for (const k in grupos) { grupos[k].name = k; scene.add(grupos[k]); }
const F = grupos.fijo;
const sombra = (o, c = true, r = true) => { o.traverse((m) => { if (m.isMesh) { m.castShadow = c; m.receiveShadow = r; } }); return o; };
const forma = (pts) => { const s = new THREE.Shape(); pts.forEach((p, i) => (i ? s.lineTo(p[0], -p[1]) : s.moveTo(p[0], -p[1]))); return s; };
const rectPts = (r) => [[r[0], r[1]], [r[2], r[1]], [r[2], r[3]], [r[0], r[3]]];
function suelo(pts, y, mat, huecos = []) {
  const s = forma(pts); for (const hq of huecos) s.holes.push(forma(hq));
  const g = new THREE.ShapeGeometry(s);
  // uv en metros (x, z)
  const pos = g.attributes.position, uv = g.attributes.uv;
  for (let i = 0; i < pos.count; i++) uv.setXY(i, pos.getX(i), pos.getY(i));
  const m = new THREE.Mesh(g, mat); m.rotation.x = -Math.PI / 2; m.position.y = y; m.receiveShadow = true;
  return m;
}
function muro(x0, y0, x1, y1, z0, z1, mat) { return caja(x1 - x0, z1 - z0, y1 - y0, mat, (x0 + x1) / 2, (z0 + z1) / 2, (y0 + y1) / 2); }

// ------------------------------------------------------------------ losa, pisos y vacíos
const E = D.escalera, TE = D.tragaluces[0].rect, TS = D.tragaluces[1].rect;
const huecoEsc = [[E.rect[0], E.rect[1]], [E.rect[2], E.rect[1]], [E.rect[2], 1.17], [E.vano[0], 1.17], [E.vano[0], E.rect[3]], [E.rect[0], E.rect[3]]];
const contorno = [[0, D.Y_BLOQUE], [D.X_BANO_D + T, D.Y_BLOQUE], [D.X_BANO_D + T, 0], [L, 0], [L, W], [0, W]];
const huecos = [rectPts(TE), rectPts(TS), huecoEsc];
F.add(suelo(contorno, 0, M_.caucho, huecos));
{ // canto y fondo de losa
  const s = forma(contorno); for (const hq of huecos) s.holes.push(forma(hq));
  const g = new THREE.ExtrudeGeometry(s, { depth: 0.25, bevelEnabled: false });
  const m = new THREE.Mesh(g, M_.losa); m.rotation.x = -Math.PI / 2; m.position.y = -0.2505; m.castShadow = true; F.add(m);
}
for (const p of D.pisos) {
  if (p.id === 'vinilico') F.add(suelo(p.poligono, 0.004, M_.vinilico));
  if (p.id === 'caucho_pl') {
    F.add(suelo(rectPts(p.rect), 0.002, M_.cauchoPL));
    const [a, b, c, d] = p.rect;
    for (const [x0, y0, x1, y1] of [[a, d - 0.05, c, d], [c - 0.05, b, c, d]]) F.add(suelo(rectPts([x0, y0, x1, y1]), 0.005, M_.rojo));
  }
  if (p.id === 'caucho_cardio') {
    F.add(suelo(rectPts(p.rect), 0.002, M_.cauchoPL));
    const [a, b, c, d] = p.rect;
    for (const [x0, y0, x1, y1] of [[a, b, c, b + 0.05], [a, b, a + 0.05, d], [c - 0.05, b, c, d]]) F.add(suelo(rectPts([x0, y0, x1, y1]), 0.005, M_.rojo));
  }
  if (p.id === 'grass') {
    const [a, b, c, d] = p.rect;
    const g = caja(c - a, 0.014, d - b, M_.grass, (a + c) / 2, 0.007, (b + d) / 2); g.castShadow = false;
    // uv en metros
    g.material = M_.grass.clone(); g.material.map = texGrass(); g.material.map.repeat.set((c - a) * 0.9, (d - b) * 0.9); F.add(g);
    for (const [x0, y0, x1, y1] of [[a, b, c, b + 0.06], [a, d - 0.06, c, d], [a, b, a + 0.06, d], [c - 0.06, b, c, d]]) F.add(suelo(rectPts([x0, y0, x1, y1]), 0.016, M_.blanco));
  }
}
if (D.zona_seguridad) {            // franja libre detrás de las cintas, marcada en el piso
  const [a, b, c, d] = D.zona_seguridad, am = std(0xf2c200, 0.7, 0);
  for (let x = a; x < c - 0.01; x += 0.5) F.add(suelo(rectPts([x, b, Math.min(c, x + 0.28), b + 0.05]), 0.006, am));
  for (const x of [a, c - 0.05]) for (let y = b; y < d - 0.01; y += 0.5) F.add(suelo(rectPts([x, y, x + 0.05, Math.min(d, y + 0.28)]), 0.006, am));
}
// vacíos: tragaluces (pozo de luz) y caja de escalera
function pozo(r, prof, mat) {
  const g = G(), [a, b, c, d] = r;
  g.add(muro(a - 0.05, b - 0.05, a, d + 0.05, -prof, -0.25, mat), muro(c, b - 0.05, c + 0.05, d + 0.05, -prof, -0.25, mat));
  g.add(muro(a, b - 0.05, c, b, -prof, -0.25, mat), muro(a, d, c, d + 0.05, -prof, -0.25, mat));
  g.add(muro(a, b, c, d, -prof - 0.05, -prof, std(0x9a9890, 0.9, 0)));
  return sombra(g, false, true);
}
F.add(pozo(TE, 5.6, std(0xe9e6dc, 0.9, 0)), pozo(TS, 5.6, std(0xe9e6dc, 0.9, 0)));
{ // escalera (esquemática): descanso de llegada + peldaños que bajan
  const g = G(), [a, b, c, d] = E.rect, es = E.espina, mE = std(0xa9a69c, 0.85, 0);
  g.add(pozo([a, b, c, d], 3.2, std(0xdedbd2, 0.9, 0)));
  g.add(muro(E.vano[0], 1.17, c, d, -0.2, 0.004, mE));                       // descanso
  const ancho = c - es[2];
  for (let i = 0; i < 5; i++) g.add(muro(es[2], 1.17 - (i + 1) * 0.21, c, 1.17 - i * 0.21, -0.2 - (i + 1) * 0.18, -(i + 1) * 0.18, mE));
  for (let i = 0; i < 9; i++) g.add(muro(a + 0.03, 0.35 + i * 0.19, es[0], 0.35 + (i + 1) * 0.19, -1.6 - i * 0.18, -1.42 - i * 0.18, mE));
  g.add(muro(es[0], es[1], es[2], es[3], -3.2, 1.0, M_.parapeto));           // espina central
  g.add(muro(a, b, a + 0.06, d, -0.25, 1.0, M_.parapeto));                   // murete hacia el tragaluz
  // baranda del descanso
  for (const y of [0.55, 0.95]) g.add(tubo([E.vano[0] + 0.03, y, 1.17], [c - 0.03, y, 1.17], 0.02, M_.acero));
  for (const x of [E.vano[0] + 0.03, c - 0.03]) g.add(tubo([x, 0, 1.17], [x, 0.95, 1.17], 0.02, M_.acero));
  void ancho; F.add(sombra(g));
}

// ------------------------------------------------------------------ muros existentes
for (const [x0, y0, x1, y1, h, clave] of D.muros) {
  const mat = clave === 'bano' ? M_.bano : M_.parapeto;
  F.add(muro(x0, y0, x1, y1, 0, h, mat));
}
for (const [x0, y0, x1, y1, h] of D.columnas) F.add(muro(x0 - 0.005, y0 - 0.005, x1 + 0.005, y1 + 0.005, 0, h, M_.parapeto));
{ // baños: piso elevado, techo, dinteles, puertas y aparatos
  const g = G(), HB = D.H_BANO;
  for (const b of D.banos) {
    const [a, y0, c, y1] = b.rect;
    g.add(muro(a, y0, c, y1 + 0.24, 0, 0.15, M_.baldosa.clone()));
    g.children.at(-1).material = M_.baldosa;
    const [dx0, dy0, dx1, dy1] = b.ducha;
    g.add(muro(dx0, dy0, dx1, dy1, 0.13, 0.152, std(0x9fb4bd, 0.3, 0)));
    const vx = (dx1 < c - 0.05) ? dx1 : dx0;                                     // mampara de vidrio
    g.add(muro(vx - 0.005, dy0, vx + 0.005, dy1, 0.15, 2.05, M_.vidrio));
    const [ix, iy] = b.inodoro;
    g.add(cojin(0.38, 0.38, 0.5, M_.loza, ix, 0.34, iy + 0.05, 0.08), cojin(0.4, 0.36, 0.18, M_.loza, ix, 0.62, iy - 0.26, 0.04));
    const [lx, ly] = b.lavatorio;
    g.add(cojin(0.46, 0.14, 0.38, M_.loza, lx, 0.92, ly, 0.05), tubo([lx, 0.15, ly], [lx, 0.86, ly], 0.05, M_.loza));
  }
  // dinteles sobre puertas y hojas
  for (const p of D.puertas) {
    const y = p.y, e = 0.055;
    g.add(muro(p.x0, y - e, p.x1, y + e, 2.1, HB, M_.bano));
    const hoja = caja(p.x1 - p.x0 - 0.03, 1.95, 0.04, M_.madera, (p.x0 + p.x1) / 2, 0.15 + 0.975, y);
    g.add(hoja);
    g.add(caja(0.02, 0.12, 0.07, MAT.cromo, p.bisagra === 'x1' ? p.x0 + 0.07 : p.x1 - 0.07, 1.15, y + 0.03));
    const placa = new THREE.Mesh(new THREE.PlaneGeometry(0.26, 0.26), new THREE.MeshStandardMaterial({ map: texPuerta(p.id === 'P-1' ? 'DUCHA' : 'SS.HH.'), roughness: 0.6 }));
    placa.position.set((p.x0 + p.x1) / 2, 1.72, y + 0.022); g.add(placa);
    g.add(muro(p.x0, y - 0.1, p.x1, y + 0.3, 0, 0.15, M_.concreto));             // grada de ingreso (+0.15)
  }
  g.add(muro(1.79, 1.70, 2.40, 1.81, 2.1, HB, M_.bano));
  F.add(sombra(g));
  // techo del bloque de baños
  const tb = muro(0, D.Y_BLOQUE, D.X_BANO_D + T, 2.05, HB, HB + 0.06, std(0xe8e6e0, 0.8, 0));
  grupos.techoBano.add(sombra(tb));
  // franja de color y rótulo del bloque de servicios
  const rot = new THREE.Mesh(new THREE.PlaneGeometry(1.5, 0.3), new THREE.MeshStandardMaterial({ map: texLetrero('SS.HH. · DUCHAS', '#e8e6e0', '#17181b'), roughness: 0.7 }));
  rot.position.set(3.5, 2.2, 2.052); F.add(rot);
}

// ------------------------------------------------------------------ tanque, tragaluz SO, lavadero y celosías
{
  const g = G(), tq = D.tanque, [a, b, c, d] = tq.plataforma;
  for (const [x, y] of [[a + 0.06, b + 0.06], [c - 0.06, b + 0.06], [a + 0.06, d - 0.06], [c - 0.06, d - 0.06]]) g.add(viga([x, 0, y], [x, tq.base, y], 0.075, 0.075, M_.acero));
  for (const y of [b + 0.06, (b + d) / 2, d - 0.06]) g.add(viga([a, tq.base - 0.04, y], [c, tq.base - 0.04, y], 0.075, 0.075, M_.acero));
  for (const x of [a + 0.06, c - 0.06]) g.add(viga([x, tq.base - 0.04, b], [x, tq.base - 0.04, d], 0.075, 0.075, M_.acero));
  g.add(muro(a, b, c, d, tq.base, tq.base + 0.02, M_.aceroGris));
  const r = tq.diam / 2, cx = tq.centro[0], cz = tq.centro[1];
  const cuerpo = new THREE.Mesh(new THREE.CylinderGeometry(r, r * 0.97, tq.alto * 0.78, 40), M_.tanque); cuerpo.position.set(cx, tq.base + 0.02 + tq.alto * 0.39, cz); g.add(cuerpo);
  for (let i = 1; i < 5; i++) { const an = new THREE.Mesh(new THREE.TorusGeometry(r * 0.99, 0.014, 8, 40), M_.tanque); an.rotation.x = Math.PI / 2; an.position.set(cx, tq.base + i * tq.alto * 0.155, cz); g.add(an); }
  const domo = new THREE.Mesh(new THREE.SphereGeometry(r, 40, 12, 0, Math.PI * 2, 0, Math.PI / 2), M_.tanque); domo.scale.y = 0.42; domo.position.set(cx, tq.base + 0.02 + tq.alto * 0.78, cz); g.add(domo);
  const tapa = new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.22, 0.07, 24), M_.tanque); tapa.position.set(cx, tq.base + tq.alto - 0.02, cz); g.add(tapa);
  // malla anticaída sobre el tragaluz SO
  const [ta, tb2, tc, td] = TS;
  for (let x = ta + 0.08; x < tc; x += 0.13) g.add(tubo([x, 1.0, tb2], [x, 1.0, td], 0.006, M_.aceroGris, 6));
  for (let y = tb2 + 0.08; y < td; y += 0.13) g.add(tubo([ta, 1.0, y], [tc, 1.0, y], 0.006, M_.aceroGris, 6));
  // lavadero de dos pozas
  const lv = D.lavadero.rect, hl = D.lavadero.alto;
  g.add(muro(lv[0], lv[1], lv[2], lv[3], 0, hl - 0.22, M_.baldosa));
  for (const [y0, y1] of [[lv[1], (lv[1] + lv[3]) / 2 - 0.02], [(lv[1] + lv[3]) / 2 + 0.02, lv[3]]]) {
    g.add(muro(lv[0], y0, lv[0] + 0.05, y1, hl - 0.22, hl, M_.loza), muro(lv[2] - 0.05, y0, lv[2], y1, hl - 0.22, hl, M_.loza));
    g.add(muro(lv[0], y0, lv[2], y0 + 0.05, hl - 0.22, hl, M_.loza), muro(lv[0], y1 - 0.05, lv[2], y1, hl - 0.22, hl, M_.loza));
    g.add(tubo([lv[0] + 0.06, hl + 0.02, (y0 + y1) / 2], [lv[0] + 0.06, hl + 0.2, (y0 + y1) / 2], 0.012, MAT.cromo), tubo([lv[0] + 0.06, hl + 0.2, (y0 + y1) / 2], [lv[0] + 0.2, hl + 0.17, (y0 + y1) / 2], 0.012, MAT.cromo));
  }
  F.add(sombra(g));
  // celosías de listones (ocultan tanque y lavadero desde la sala)
  const cel = G();
  for (const [x0, y0, x1, y1, h] of D.celosias) {
    const n = Math.max(2, Math.round(Math.hypot(x1 - x0, y1 - y0) / 0.075));
    for (let i = 0; i <= n; i++) { const k = i / n; cel.add(caja(0.035, h - 0.05, 0.035, M_.madera, x0 + (x1 - x0) * k, h / 2 + 0.03, y0 + (y1 - y0) * k)); }
    for (const z of [0.05, h * 0.5, h]) cel.add(viga([x0, z, y0], [x1, z, y1], 0.03, 0.05, M_.acero));
  }
  // forro de la plataforma del tanque hacia el vestíbulo
  for (let y = b + 0.03; y < d; y += 0.075) cel.add(caja(0.03, 1.3, 0.035, M_.madera, c + 0.03, 1.0 + 0.65, y));
  F.add(sombra(cel));
}

// ------------------------------------------------------------------ cerramiento sobre el parapeto
function lamas(g, a, b, z0, z1, mat) {
  const n = Math.max(1, Math.floor((z1 - z0) / 0.1)), h = (z1 - z0) / n;
  const dx = b[0] - a[0], dz = b[1] - a[1], largo = Math.hypot(dx, dz), ang = Math.atan2(dz, dx);
  for (let i = 0; i < n; i++) {
    const l = new THREE.Mesh(new THREE.BoxGeometry(largo, 0.006, 0.085), mat);
    l.position.set((a[0] + b[0]) / 2, z0 + (i + 0.5) * h, (a[1] + b[1]) / 2);
    l.rotation.set(0.7, -ang, 0, 'YXZ'); l.castShadow = true; g.add(l);
  }
}
const espejos = [];
{
  const alto = grupos.cerramientoAlto, HP = D.H_PARAPETO;
  for (const [x0, y0, x1, y1, tipo] of D.cerramiento) {
    const g = G(), horiz = Math.abs(y1 - y0) < 1e-6;
    const fijoY = horiz ? (y0 === 0 ? T / 2 : y0 === W ? W - T / 2 : y0 - T / 2) : null;
    const fijoX = horiz ? null : (x0 === 0 ? T / 2 : x0 === L ? L - T / 2 : x0 - T / 2);
    const P = (t) => horiz ? [x0 + (x1 - x0) * t, fijoY] : [fijoX, y0 + (y1 - y0) * t];
    const largo = horiz ? Math.abs(x1 - x0) : Math.abs(y1 - y0);
    const n = Math.max(1, Math.round(largo / 1.22));
    const tope = (p) => (tipo === 'muro_luz' || tipo === 'panel') ? 2.4 : hTecho(p[0]) + 0.02;
    const zMed = (tipo === 'muro_luz' || tipo === 'panel') ? 2.4 : 2.2;
    for (let i = 0; i <= n; i++) { const p = P(i / n); g.add(viga([p[0], HP, p[1]], [p[0], tope(p), p[1]], 0.05, 0.05, M_.acero)); }
    for (let i = 0; i < n; i++) {
      const a = P(i / n), b = P((i + 1) / n), cx = (a[0] + b[0]) / 2, cy = (a[1] + b[1]) / 2, lb = largo / n - 0.05;
      const matP = tipo === 'ventanal' ? M_.vidrio : tipo === 'policarbonato' ? M_.poli : tipo === 'muro_luz' ? M_.luz : M_.panel;
      const pl = new THREE.Mesh(new THREE.BoxGeometry(horiz ? lb : 0.012, zMed - HP - 0.05, horiz ? 0.012 : lb), matP);
      pl.position.set(cx, (HP + zMed) / 2, cy); pl.castShadow = tipo !== 'ventanal'; pl.receiveShadow = tipo !== 'ventanal'; pl.renderOrder = tipo === 'ventanal' ? 5 : 0; g.add(pl);
      g.add(viga([a[0], HP + 0.02, a[1]], [b[0], HP + 0.02, b[1]], 0.05, 0.04, M_.acero));
      g.add(viga([a[0], zMed, a[1]], [b[0], zMed, b[1]], 0.05, 0.04, M_.acero));
      if (zMed < 2.3) { g.add(viga([a[0], tope(a), a[1]], [b[0], tope(b), b[1]], 0.05, 0.04, M_.acero)); lamas(g, a, b, zMed + 0.03, Math.min(tope(a), tope(b)) - 0.03, M_.aceroGris); }
    }
    g.userData.lado = horiz ? (y0 === 0 ? 'A' : y0 === W ? 'B' : 'interior') : (x0 === 0 ? 'mercado' : x0 === L ? 'calle' : 'interior');
    alto.add(sombra(g));
    if (tipo === 'panel') {            // mural hacia la zona de peso libre
      const mur = new THREE.Mesh(new THREE.PlaneGeometry(largo - 0.06, 1.38), new THREE.MeshStandardMaterial({ map: texMural(), roughness: 0.75 }));
      mur.rotation.y = Math.PI / 2; mur.position.set(x0 + 0.004, 1.7, (y0 + y1) / 2); alto.add(mur);
    }
  }
  // espejos sobre tablero, delante del parapeto y del panel del fondo
  for (const [a, b] of D.espejos) {
    const tab = muro(a - 0.03, T, b + 0.03, T + 0.02, 0.3, 2.2, M_.negroMate); F.add(tab);
    const esp = new Reflector(new THREE.PlaneGeometry(b - a, 1.8), { clipBias: 0.003, textureWidth: Math.min(2048, ANCHO), textureHeight: Math.min(1152, ALTO), color: 0xb9bdc2 });
    esp.position.set((a + b) / 2, 1.25, T + 0.022); F.add(esp); espejos.push(esp);
    for (let x = a + 1.0; x < b - 0.2; x += 1.0) F.add(muro(x - 0.003, T + 0.02, x + 0.003, T + 0.024, 0.35, 2.15, M_.negroMate));
  }
}
{ // tira LED de acento en el borde interior del parapeto
  const y = D.H_PARAPETO - 0.03;
  F.add(muro(0.3, W - T - 0.012, L - T, W - T, y, y + 0.018, M_.ledRojo), muro(L - T - 0.012, T, L - T, W - T, y, y + 0.018, M_.ledRojo), muro(D.espejos[0][1] + 0.1, T, L - T, T + 0.012, y, y + 0.018, M_.ledRojo));
}
// marco de la llegada de escalera (puerta-reja abierta) y rótulo de ingreso
{
  const g = G(), [v0, v1] = E.vano, y = D.Y_HALL0 - T / 2;
  for (const x of [v0 + 0.03, v1 - 0.03]) g.add(viga([x, 0, y], [x, 2.4, y], 0.06, 0.06, M_.acero));
  g.add(viga([v0, 2.4, y], [v1, 2.4, y], 0.06, 0.06, M_.acero), viga([v0, 2.1, y], [v1, 2.1, y], 0.06, 0.05, M_.acero));
  const rot = new THREE.Mesh(new THREE.PlaneGeometry(v1 - v0 - 0.1, 0.24), new THREE.MeshStandardMaterial({ map: texLetrero('BIENVENIDOS'), roughness: 0.6, emissive: 0xffffff, emissiveMap: texLetrero('BIENVENIDOS'), emissiveIntensity: 0.25 }));
  rot.position.set((v0 + v1) / 2, 2.25, y + 0.035); g.add(rot);
  // hoja de reja abierta contra el mostrador... (gira hacia la escalera)
  const hoja = G(); for (let i = 0; i < 7; i++) hoja.add(tubo([0, 0.05, -i * 0.14 - 0.05], [0, 2.05, -i * 0.14 - 0.05], 0.009, M_.acero, 6));
  hoja.add(viga([0, 0.05, 0], [0, 0.05, -0.93], 0.03, 0.03, M_.acero), viga([0, 2.05, 0], [0, 2.05, -0.93], 0.03, 0.03, M_.acero), viga([0, 1.05, 0], [0, 1.05, -0.93], 0.03, 0.03, M_.acero));
  hoja.position.set(v1 - 0.07, 0, y - 0.03); g.add(hoja);
  F.add(sombra(g));
}

// ------------------------------------------------------------------ techo metálico (cerchas, correas, calamina)
{
  const g = grupos.techo, PE = D.peralte;
  const cerchaP = (x, z0, z1, h) => {
    const c = G(), n = Math.round((z1 - z0) / 0.57), p = (z1 - z0) / n;
    c.add(viga([x, h + 0.025, z0], [x, h + 0.025, z1], 0.05, 0.05, M_.acero), viga([x, h + PE - 0.025, z0], [x, h + PE - 0.025, z1], 0.05, 0.05, M_.acero));
    for (let i = 0; i <= n; i++) c.add(viga([x, h + 0.05, z0 + i * p], [x, h + PE - 0.05, z0 + i * p], 0.025, 0.025, M_.acero));
    for (let i = 0; i < n; i++) c.add(viga([x, h + 0.05, z0 + (i + (i % 2)) * p], [x, h + PE - 0.05, z0 + (i + 1 - (i % 2)) * p], 0.025, 0.025, M_.acero));
    return c;
  };
  for (const k of Object.keys(XC)) g.add(cerchaP(XC[k], k === '7' ? D.Y_BLOQUE : 0, W, HT[k]));
  // cerchas secundarias (a lo largo de x)
  for (const z of D.cerchas_sec_y) {
    const paso = 0.6, n = Math.round(L / paso);
    for (let i = 0; i < n; i++) {
      const xa = i * L / n, xb = (i + 1) * L / n, ha = hTecho(xa), hb = hTecho(xb);
      g.add(viga([xa, ha + 0.02, z], [xb, hb + 0.02, z], 0.03, 0.03, M_.acero), viga([xa, ha + PE - 0.02, z], [xb, hb + PE - 0.02, z], 0.03, 0.03, M_.acero));
      g.add(i % 2 ? viga([xa, ha + PE - 0.03, z], [xb, hb + 0.03, z], 0.02, 0.02, M_.acero) : viga([xa, ha + 0.03, z], [xb, hb + PE - 0.03, z], 0.02, 0.02, M_.acero));
    }
  }
  for (let x = 0.75; x < L; x += 1.18) g.add(viga([x, hTecho(x) + PE + 0.02, -0.1], [x, hTecho(x) + PE + 0.02, W + 0.1], 0.03, 0.04, M_.aceroGris));
  // calamina por paños; translúcida sobre los tragaluces [P3]
  const xs = [...new Set([-0.1, 0.15, L + 0.1, ...Object.values(XC), ...D.translucido.flatMap((r) => [r[0], r[2]])])].sort((a, b) => a - b);
  const zs = [...new Set([-0.1, W + 0.1, ...D.translucido.flatMap((r) => [r[1], r[3]])])].sort((a, b) => a - b);
  for (let i = 0; i < xs.length - 1; i++) for (let j = 0; j < zs.length - 1; j++) {
    const xa = xs[i], xb = xs[i + 1], za = Math.max(zs[j], (xb <= D.X_BANO_D + T + 1e-6 ? D.Y_BLOQUE - 0.1 : -0.1)), zb = zs[j + 1];
    if (zb - za < 0.05 || xb - xa < 0.02) continue;
    const cx = (xa + xb) / 2, cz = (za + zb) / 2;
    const tr = D.translucido.some((r) => cx > r[0] && cx < r[2] && cz > r[1] && cz < r[3]);
    const ya = hTecho(xa) + PE + 0.05, yb = hTecho(xb) + PE + 0.05;
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.Float32BufferAttribute([xa, ya, za, xb, yb, za, xb, yb, zb, xa, ya, zb], 3));
    geo.setAttribute('uv', new THREE.Float32BufferAttribute([za / 1.0, xa, za / 1.0, xb, zb / 1.0, xb, zb / 1.0, xa], 2));
    geo.setIndex([0, 2, 1, 0, 3, 2]); geo.computeVertexNormals();
    const m = new THREE.Mesh(geo, tr ? M_.transl : M_.calamina); m.castShadow = !tr; m.receiveShadow = true; m.userData.transl = tr; g.add(m);
  }
  g.traverse((m) => { if (m.isMesh && !m.userData.transl) m.castShadow = true; });
}

// ------------------------------------------------------------------ recepción, lockers, banca
{
  const R = D.recepcion, g = G();
  const [a, b, c, d] = R.mostrador, hm = R.alto_mostrador;
  g.add(muro(a + 0.04, b, c - 0.02, d, 0.08, hm - 0.04, M_.negroMate));
  for (let y = b + 0.03; y < d; y += 0.07) g.add(caja(0.025, hm - 0.2, 0.04, M_.madera, c - 0.008, (hm - 0.04) / 2 + 0.06, y));   // frente de listones
  g.add(muro(a - 0.02, b, c + 0.05, d + 0.04, hm - 0.04, hm, MAT.marco));                               // tablero superior
  g.add(muro(a - 0.32, b, a + 0.04, d, 0.72, 0.75, M_.maderaOsc));                                      // mesa de trabajo
  g.add(muro(a - 0.32, d - 0.04, a + 0.04, d, 0, 0.72, M_.negroMate));
  g.add(muro(c + 0.0, b + 0.04, c + 0.012, d - 0.02, 0.06, 0.09, M_.ledRojo));                          // LED en zócalo
  g.add(muro(c + 0.03, b + 0.04, c + 0.045, d - 0.02, hm - 0.075, hm - 0.05, M_.led));
  // laptop, lector y folletos
  g.add(caja(0.3, 0.015, 0.22, MAT.gris, a - 0.12, 0.76, (b + d) / 2), caja(0.3, 0.2, 0.012, MAT.marco, a - 0.12 + 0.0, 0.86, (b + d) / 2 - 0.11));
  g.add(caja(0.09, 0.05, 0.16, M_.negroMate, a + 0.3, hm + 0.025, d - 0.3), caja(0.2, 0.012, 0.28, M_.blanco, a + 0.26, hm + 0.006, b + 0.4));
  // taburete
  const yt = (b + d) / 2 + 0.15;
  g.add(tubo([5.55, 0, yt], [5.55, 0.62, yt], 0.025, MAT.cromo), cojin(0.36, 0.07, 0.36, MAT.tapiz, 5.55, 0.66, yt, 0.03), caja(0.4, 0.02, 0.4, MAT.marco, 5.55, 0.01, yt));
  // panel de marca (hacia el ingreso) retroiluminado
  const [pa, pb, pc, pd] = R.panel_marca, hp = R.alto_panel;
  g.add(muro(pa, pb, pc, pd, 0, hp, M_.negroMate));
  const wl = pd - pb - 0.04, hl2 = Math.min(hp - 0.04, wl * 1570 / 1024);
  const logo = new THREE.Mesh(new THREE.PlaneGeometry(wl, hl2), new THREE.MeshStandardMaterial({ map: texLogo(), roughness: 0.55, emissive: 0xffffff, emissiveMap: texLogo(), emissiveIntensity: 0.55 }));
  logo.rotation.y = Math.PI / 2; logo.position.set(pc + 0.004, hp - 0.02 - hl2 / 2, (pb + pd) / 2); g.add(logo);
  g.add(muro(pc, pb, pc + 0.02, pd, hp, hp + 0.02, M_.ledRojo));
  // estante de productos detrás del mostrador (contra el muro de luz)
  const [ea, eb, ec, ed] = R.estante;
  for (const z of [0.45, 0.85, 1.25, 1.65]) g.add(muro(ea, eb, ec, ed, z, z + 0.025, M_.maderaOsc));
  for (const x of [ea, ec - 0.03]) g.add(muro(x, eb, x + 0.03, ed, 0, 1.9, M_.negroMate));
  const col = [0xd81f26, 0xf2f2ef, 0x1f6f8b, 0xe2b007, 0x17181b];
  for (const z of [0.475, 0.875, 1.275, 1.675]) for (let x = ea + 0.1; x < ec - 0.08; x += 0.13) {
    const h = 0.14 + azar() * 0.12, r = 0.04 + azar() * 0.015;
    const bt = new THREE.Mesh(new THREE.CylinderGeometry(r, r, h, 12), std(col[Math.floor(azar() * col.length)], 0.5, 0)); bt.position.set(x, z + h / 2, eb + 0.14); g.add(bt);
  }
  // lockers (4 x 3) espalda con espalda con el panel
  const [la, lb, lc, ld] = R.lockers, hl = R.alto_lockers, nc = 4, nf = 3;
  g.add(muro(la, lb, lc, ld, 0.08, hl + 0.08, MAT.marco2), muro(la + 0.03, lb + 0.03, lc, ld - 0.03, 0, 0.08, M_.negroMate));
  const pal = [0x2a2c31, 0xb07f45, 0x2a2c31, 0xd81f26];
  for (let i = 0; i < nc; i++) for (let j = 0; j < nf; j++) {
    const py = lb + (i + 0.5) * (ld - lb) / nc, pz = 0.08 + (j + 0.5) * hl / nf;
    g.add(caja(0.018, hl / nf - 0.03, (ld - lb) / nc - 0.03, std(pal[(i + j * 3) % 4], 0.55, 0.2), la - 0.006, pz, py));
    g.add(caja(0.02, 0.07, 0.02, MAT.cromo, la - 0.02, pz, py + (ld - lb) / nc / 2 - 0.05));
    for (let v = 0; v < 3; v++) g.add(caja(0.004, 0.006, 0.12, M_.negroMate, la - 0.016, pz + hl / nf / 2 - 0.07 - v * 0.02, py - 0.02));
  }
  // banca de listones
  const [ba, bb, bc, bd] = R.banca;
  for (let y = bb + 0.03; y < bd; y += 0.075) g.add(muro(ba, y, bc, y + 0.055, 0.42, 0.455, M_.madera));
  for (const x of [ba + 0.06, bc - 0.06]) g.add(viga([x, 0, bb + 0.05], [x, 0.42, bb + 0.05], 0.04, 0.04, M_.acero), viga([x, 0, bd - 0.05], [x, 0.42, bd - 0.05], 0.04, 0.04, M_.acero), viga([x, 0.4, bb + 0.05], [x, 0.4, bd - 0.05], 0.04, 0.04, M_.acero));
  // felpudo de ingreso y dispensador de agua
  g.add(muro(E.vano[0] + 0.08, D.Y_HALL0 + 0.1, E.vano[1] - 0.08, D.Y_HALL0 + 0.75, 0.004, 0.012, std(0x202225, 0.95, 0)));
  const xd = E.vano[1] + 0.32, yd = D.Y_HALL0 + 0.02;
  g.add(muro(xd - 0.16, yd - 0.15, xd + 0.16, yd + 0.17, 0, 1.0, M_.blanco));
  const bid = new THREE.Mesh(new THREE.CylinderGeometry(0.135, 0.135, 0.36, 20), new THREE.MeshPhysicalMaterial({ color: 0x8fc8ec, roughness: 0.1, transparent: true, opacity: 0.6 })); bid.position.set(xd, 1.19, yd + 0.01); g.add(bid);
  F.add(sombra(g));
}

// ------------------------------------------------------------------ máquinas y accesorios
for (const m of D.maquinas) F.add(sombra(crearMaquina(m)));
for (const [x, y] of D.porta_discos) { const p = portaDiscos(); p.position.set(x, 0, y); p.rotation.y = 0.5; F.add(sombra(p)); }
if (D.zona_funcional) { // zona funcional: cajón pliométrico, pesas rusas, colchonetas, rodillo
  const g = G(), [a, b, c, d] = D.zona_funcional;
  g.add(cojin(0.6, 0.5, 0.75, M_.madera, c - 0.5, 0.265, b + 0.55, 0.01));
  for (const [i, col] of [[0, 0xd81f26], [1, 0x1f6f8b], [2, 0xe2b007]]) {
    const r = 0.085 + i * 0.012, x = a + 0.35 + i * 0.3, z = b + 0.3;
    const e = new THREE.Mesh(new THREE.SphereGeometry(r, 18, 14), std(col, 0.5, 0.2)); e.position.set(x, r + 0.014, z); g.add(e);
    const asa = new THREE.Mesh(new THREE.TorusGeometry(r * 0.62, 0.014, 8, 18, Math.PI), MAT.marco); asa.position.set(x, r * 1.75 + 0.014, z); g.add(asa);
  }
  g.add(cojin(0.6, 0.02, 1.75, std(0x1f6f8b, 0.9, 0), a + 0.55, 0.026, d - 1.05, 0.008), cojin(0.6, 0.02, 1.75, std(0x4b3f72, 0.9, 0), a + 1.3, 0.026, d - 1.05, 0.008));
  const rod = new THREE.Mesh(new THREE.CylinderGeometry(0.075, 0.075, 0.45, 18), std(0x17181b, 0.9, 0)); rod.rotation.z = Math.PI / 2; rod.position.set(a + 0.55, 0.11, d - 1.7); g.add(rod);
  const pel = new THREE.Mesh(new THREE.SphereGeometry(0.31, 24, 18), std(0xc9cdd2, 0.5, 0.05)); pel.position.set(c - 0.42, 0.324, d - 0.45); g.add(pel);
  F.add(sombra(g));
}
function planta(x, z, s = 1) {
  const g = G(), verde = [0x2f7d3b, 0x3a8f45, 0x276b33];
  g.add(caja(0.36 * s, 0.4 * s, 0.36 * s, M_.negroMate, 0, 0.2 * s, 0), tubo([0, 0.4 * s, 0], [0, 0.95 * s, 0], 0.018 * s, M_.maderaOsc, 8));
  for (let i = 0; i < 9; i++) {
    const an = i * 2.4, r = (0.2 + (i % 3) * 0.05) * s, e = new THREE.Mesh(new THREE.SphereGeometry(r, 10, 8), std(verde[i % 3], 0.85, 0));
    e.position.set(Math.sin(an) * 0.17 * s, (0.95 + (i % 4) * 0.16) * s, Math.cos(an) * 0.17 * s); e.scale.y = 0.85; e.castShadow = true; g.add(e);
  }
  g.position.set(x, 0, z); return g;
}
F.add(planta(4.33, 2.44, 0.8), planta(L - 0.45, 1.88, 0.85));

// ------------------------------------------------------------------ luminarias, ventiladores, señalética
const luces = [];
{
  const g = G();
  for (const [x, z] of D.luminarias) {
    const y = hTecho(x) - 0.06;
    g.add(caja(0.09, 0.045, 1.2, M_.negroMate, x, y + 0.02, z)); const tubL = caja(0.07, 0.012, 1.16, M_.led, x, y - 0.008, z); tubL.castShadow = false; g.add(tubL);
    for (const dz of [-0.45, 0.45]) g.add(tubo([x, y + 0.04, z + dz], [x, y + 0.42, z + dz], 0.003, M_.acero, 5));
  }
  for (const [x, z, dir] of D.ventiladores) {
    const v = G(), y = 2.02;
    const aro = new THREE.Mesh(new THREE.TorusGeometry(0.24, 0.012, 8, 28), M_.acero); v.add(aro);
    for (let i = 0; i < 10; i++) { const r = tubo([0, 0, 0], [0.24 * Math.cos(i * 0.628), 0.24 * Math.sin(i * 0.628), 0.03], 0.003, M_.acero, 4); v.add(r); }
    for (let i = 0; i < 3; i++) { const pa = new THREE.Mesh(new THREE.CircleGeometry(0.2, 12, i * 2.09, 0.9), std(0x3a3d42, 0.5, 0.3, { side: THREE.DoubleSide })); pa.position.z = -0.03; v.add(pa); }
    v.add(caja(0.1, 0.1, 0.16, M_.acero, 0, 0, -0.1), viga([0, -0.02, -0.16], [0, -0.05, -0.32], 0.035, 0.035, M_.acero));
    v.position.set(x, y, z); v.rotation.y = { S: 0, N: Math.PI, E: Math.PI / 2, O: -Math.PI / 2 }[dir]; v.rotation.x = 0.2; g.add(v);
  }
  for (const [x, z] of D.extintores) {
    g.add(new THREE.Mesh(new THREE.CylinderGeometry(0.065, 0.065, 0.42, 16), M_.rojo).translateX(x).translateY(1.25).translateZ(z));
    g.add(caja(0.05, 0.1, 0.05, M_.negroMate, x, 1.5, z));
    g.add(caja(0.2, 0.2, 0.01, std(0xd81f26, 0.6, 0), x, 1.82, z));
  }
  // letreros colgantes por zona
  const letreros = [['RECEPCIÓN', 6.9, 3.3, Math.PI / 2], ['PESO LIBRE', (D.espejos[0][0] + D.espejos[0][1]) / 2, 1.45, 0], ['TREN INFERIOR', L - 2.1, 3.9, Math.PI / 2],
    ['TREN SUPERIOR', D.maquinas.find((m) => m.tipo === 'crossover').c[0], 4.75, 0], ['SS.HH. · LOCKERS', 3.0, VER === 'A' ? 3.6 : 3.0, 0]];
  if (D.maquinas.some((m) => m.tipo === 'cinta')) letreros.push(['CARDIO', 2.6, 4.5, 0]);
  for (const [txt, x, z, giro] of letreros) {
    const y = hTecho(x) - 0.28, t = texLetrero(txt);
    const s = new THREE.Mesh(new THREE.BoxGeometry(0.96, 0.2, 0.016), [M_.negroMate, M_.negroMate, M_.negroMate, M_.negroMate, new THREE.MeshStandardMaterial({ map: t, roughness: 0.6 }), new THREE.MeshStandardMaterial({ map: t, roughness: 0.6 })]);
    s.position.set(x, y, z); s.rotation.y = giro; g.add(s);
    for (const dd of [-0.4, 0.4]) g.add(tubo([x + Math.cos(giro) * dd, y + 0.1, z - Math.sin(giro) * dd], [x + Math.cos(giro) * dd, y + 0.3, z - Math.sin(giro) * dd], 0.003, M_.acero, 5));
  }
  // parlantes y botiquín
  for (const [x, z] of [[XC['3'] - 0.3, 0.6], [XC['3'] - 0.3, W - 0.6], [XC['5'] + 0.3, W - 0.6]]) g.add(caja(0.2, 0.3, 0.18, M_.negroMate, x, hTecho(x) - 0.2, z));
  g.add(caja(0.3, 0.3, 0.1, M_.blanco, E.vano[1] + T + 0.06, 1.5, 1.2), caja(0.012, 0.16, 0.05, std(0x2a9a4b, 0.6, 0), E.vano[1] + T + 0.115, 1.5, 1.2), caja(0.012, 0.05, 0.16, std(0x2a9a4b, 0.6, 0), E.vano[1] + T + 0.116, 1.5, 1.2));
  F.add(sombra(g, true, true));
}

// ------------------------------------------------------------------ personas
{
  const g = grupos.gente;
  const pon = (p, x, z, giro) => { p.position.set(x, 0, z); p.rotation.y = giro; g.add(sombra(p)); return p; };
  pon(persona({ polo: 3, brazoI: [0.25, 0.9, 0.1, 1.3], brazoD: [0.2, 0.2, 0.1, 0.5] }), 5.62, 3.05, Math.PI / 2);                       // recepcionista
  pon(persona({ polo: 2, alto: 1.64, brazoI: [0.15, 0.3, 0.1, 1.2], brazoD: [0.1, 0, 0.1, 0.1] }), 6.98, 2.95, -Math.PI / 2);            // socia en el mostrador
  pon(persona({ polo: 1, alto: 1.76, brazoI: [1.25, 0.25, 1.1, 0.5], brazoD: [1.25, 0.25, 1.1, 0.5], paso: 0.16 }), D.maquinas.find((m) => m.tipo === 'crossover').c[0], 5.0, Math.PI);   // crossover
  if (D.zona_funcional) pon(persona({ polo: 4, alto: 1.62, brazoI: [2.9, 0.05, 2.9, 0.1], brazoD: [2.9, 0.05, 2.9, 0.1] }), D.zona_funcional[0] + 1.3, D.zona_funcional[3] - 1.0, -0.5);  // estiramiento
  const ct = D.maquinas.find((m) => m.tipo === 'cinta');
  if (ct) { const r = pon(persona({ polo: 4, alto: 1.68, brazoI: [0.2, 0.7, 0.2, 1.7], brazoD: [0.2, -0.5, 0.2, 1.2], paso: 0.3 }), ct.c[0], ct.c[1] + 0.25, 0); r.position.y = 0.23; }   // corriendo
  pon(persona({ polo: 5, alto: 1.72, brazoI: [0.1, -0.35, 0.1, 0.2], brazoD: [0.1, 0.4, 0.1, 0.7], paso: 0.24 }), 4.2, VER === 'A' ? 4.0 : 3.75, 1.1);        // caminando al vestuario
  if (OPC.gente === '0' || OPC.gente === false) g.visible = false;
}

// ------------------------------------------------------------------ entorno: edificio, pueblo, cerros y cielo
const cielo = new THREE.Mesh(new THREE.SphereGeometry(1800, 40, 20), new THREE.ShaderMaterial({
  side: THREE.BackSide, depthWrite: false, fog: false,
  uniforms: { cenit: { value: new THREE.Color() }, horizonte: { value: new THREE.Color() }, suelo: { value: new THREE.Color() } },
  vertexShader: 'varying vec3 vP; void main(){ vP = position; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }',
  fragmentShader: 'uniform vec3 cenit; uniform vec3 horizonte; uniform vec3 suelo; varying vec3 vP; void main(){ float h = normalize(vP).y; vec3 c = h > 0.0 ? mix(horizonte, cenit, pow(h, 0.55)) : mix(horizonte, suelo, min(1.0, -h * 6.0)); gl_FragColor = vec4(c, 1.0); }',
}));
scene.add(cielo);
{
  const g = grupos.entorno, NIV = -8.6;
  // edificio bajo la losa
  g.add(muro(0.1, D.Y_BLOQUE + 0.1, L - 0.1, W - 0.1, NIV, -0.25, std(0xe9e2d0, 0.9, 0)));
  for (let p = 0; p < 3; p++) for (let i = 0; i < 4; i++) g.add(caja(0.02, 1.1, 1.3, std(0x3b4a58, 0.2, 0.3), L - 0.09, NIV + 1.6 + p * 2.8, 1.2 + i * 1.5));
  const terreno = new THREE.Mesh(new THREE.CircleGeometry(900, 48), std(0x5d7a48, 1, 0)); terreno.rotation.x = -Math.PI / 2; terreno.position.y = NIV; terreno.receiveShadow = true; g.add(terreno);
  g.add(muro(L + 1.6, -60, L + 8.4, 70, NIV, NIV + 0.03, std(0x4a4b4e, 0.95, 0)), muro(-60, W + 1.5, 90, W + 7.5, NIV, NIV + 0.035, std(0x4a4b4e, 0.95, 0)));
  // casas del pueblo
  const techos = [0x9a4a35, 0xb9bec4, 0x7d8a93, 0xa3553c, 0xc9cdd2], muros = [0xe9e2d0, 0xd9c7a8, 0xf0ede4, 0xc9d6d2, 0xe6d3b8];
  _sem = 91;
  for (let i = 0; i < 150; i++) {
    const ang = azar() * Math.PI * 2, dist = 14 + azar() * 210, x = L / 2 + Math.cos(ang) * dist, z = W / 2 + Math.sin(ang) * dist;
    if (x > -4 && x < L + 9 && z > -5 && z < W + 8) continue;
    if ((x > L + 1 && x < L + 9) || (z > W + 1 && z < W + 8)) continue;
    const a = 5 + azar() * 6, b = 6 + azar() * 7, h = 2.8 + Math.floor(azar() * 3) * 2.7;
    const casa = caja(a, h, b, std(muros[i % 5], 0.9, 0), x, NIV + h / 2, z); casa.rotation.y = azar() * 0.3; g.add(casa);
    const te = caja(a + 0.5, 0.12, b + 0.5, std(techos[i % 5], 0.6, 0.3), x, NIV + h + 0.25, z); te.rotation.set(0, casa.rotation.y, 0.12); g.add(te);
  }
  // árboles
  for (let i = 0; i < 120; i++) {
    const ang = azar() * Math.PI * 2, dist = 25 + azar() * 330, x = L / 2 + Math.cos(ang) * dist, z = W / 2 + Math.sin(ang) * dist, s = 2.5 + azar() * 3.5;
    const copa = new THREE.Mesh(new THREE.SphereGeometry(s, 8, 6), std(azar() < 0.5 ? 0x356b33 : 0x41803c, 1, 0)); copa.position.set(x, NIV + s * 1.25, z); copa.scale.y = 1.25; g.add(copa);
  }
  // cerros
  for (let k = 0; k < 3; k++) {
    const R0 = 330 + k * 210, seg = 96, alt = 70 + k * 85, geo = new THREE.BufferGeometry(), pos = [], colr = [];
    const base = new THREE.Color([0x4f7f46, 0x5c8a5a, 0x7c9c8f][k]), cima = new THREE.Color([0x3f6d3b, 0x4d7b55, 0x8fa9a3][k]);
    for (let i = 0; i <= seg; i++) {
      const a = i / seg * Math.PI * 2;
      const h = alt * (0.45 + 0.3 * Math.sin(a * 3 + k * 1.7) + 0.2 * Math.sin(a * 7 + k) + 0.12 * Math.sin(a * 13 + k * 4));
      pos.push(Math.cos(a) * R0 + L / 2, NIV - 2, Math.sin(a) * R0 + W / 2, Math.cos(a) * (R0 + 120) + L / 2, NIV + Math.max(12, h), Math.sin(a) * (R0 + 120) + W / 2);
      colr.push(base.r, base.g, base.b, cima.r, cima.g, cima.b);
    }
    const idx = []; for (let i = 0; i < seg; i++) { const p = i * 2; idx.push(p, p + 1, p + 2, p + 1, p + 3, p + 2); }
    geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); geo.setAttribute('color', new THREE.Float32BufferAttribute(colr, 3)); geo.setIndex(idx); geo.computeVertexNormals();
    g.add(new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ vertexColors: true, side: THREE.DoubleSide, fog: false })));
  }
  // nubes
  for (let i = 0; i < 16; i++) {
    const a = azar() * Math.PI * 2, n = new THREE.Mesh(new THREE.SphereGeometry(40 + azar() * 50, 10, 8), new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.75, fog: false }));
    n.scale.set(2.6, 0.35, 1.2); n.position.set(Math.cos(a) * 900, 260 + azar() * 220, Math.sin(a) * 900); n.userData.nube = true; g.add(n);
  }
}

// ------------------------------------------------------------------ iluminación (día / noche)
const hemi = new THREE.HemisphereLight(0xffffff, 0x4a4a50, 1);
const sol = new THREE.DirectionalLight(0xfff0d8, 3);
sol.castShadow = true; sol.shadow.mapSize.set(4096, 4096); sol.shadow.bias = -0.0004; sol.shadow.normalBias = 0.03;
Object.assign(sol.shadow.camera, { left: -13, right: 13, top: 10, bottom: -10, near: 1, far: 70 });
sol.target.position.set(L / 2, 0, W / 2);
scene.add(hemi, sol, sol.target);
const puntos = [];
for (const [x, z, k] of [[2.6, 5.0, 1], [5.9, 4.3, 1], [9.2, 1.6, 1], [9.2, 5.0, 1], [12.4, 1.6, 1], [12.4, 5.0, 1], [5.6, 2.9, 0.7], [2.6, 2.9, 0.6]]) {
  const p = new THREE.PointLight(0xffffff, 1, 11, 1.6); p.position.set(x, hTecho(x) - 0.25, z); p.userData.k = k; scene.add(p); puntos.push(p);
}
const luzTrag = [];
for (const r of D.translucido) { const p = new THREE.PointLight(0xfff6e6, 1, 9, 1.5); p.position.set((r[0] + r[2]) / 2, hTecho((r[0] + r[2]) / 2) + 0.2, (r[1] + r[3]) / 2); scene.add(p); luzTrag.push(p); }
const luzMarca = new THREE.PointLight(0xff5a4a, 1, 4.5, 1.8); luzMarca.position.set(5.6, 1.6, 3.0); scene.add(luzMarca);
const luzRoja = [[L - 1.2, 0.9, W - 0.6], [9.5, 0.9, W - 0.6], [L - 0.6, 0.9, 2.4], [3.0, 0.9, W - 0.6]].map(([x, y, z]) => { const p = new THREE.PointLight(0xff2a2a, 0, 5.5, 1.7); p.position.set(x, y, z); scene.add(p); return p; });

function modo(noche) {
  NOCHE = noche;
  const u = cielo.material.uniforms;
  if (noche) {
    u.cenit.value.set(0x070b18); u.horizonte.value.set(0x27314f); u.suelo.value.set(0x0b0d12);
    hemi.intensity = 0.07; hemi.color.set(0x8fa3d6); hemi.groundColor.set(0x1b1b20);
    sol.intensity = 0.25; sol.color.set(0x8fa6e0); sol.position.set(L / 2 - 14, 22, W / 2 - 9);
    puntos.forEach((p) => { p.intensity = 8.5 * p.userData.k; p.color.set(0xffe9cf); });
    luzRoja.forEach((p) => { p.intensity = 4.5; });
    luzTrag.forEach((p) => { p.intensity = 0; });
    luzMarca.intensity = 6;
    M_.transl.emissiveIntensity = 0.02; M_.transl.color.set(0x56607a); M_.poli.emissiveIntensity = 0.02; M_.poli.color.set(0x8f98ab);
    M_.luz.emissiveIntensity = 0.3; M_.luz.emissive.set(0xffe2c2); M_.led.emissiveIntensity = 5; M_.ledRojo.emissiveIntensity = 5;
    scene.environmentIntensity = 0.06; renderer.toneMappingExposure = 1.0;
  } else {
    u.cenit.value.set(0x3f86d8); u.horizonte.value.set(0xd3e6f3); u.suelo.value.set(0x7f8f76);
    hemi.intensity = 0.95; hemi.color.set(0xffffff); hemi.groundColor.set(0x55555c);
    sol.intensity = 3.4; sol.color.set(0xfff0d8); sol.position.set(L / 2 + 17, 13.5, W / 2 - 7.5);
    puntos.forEach((p) => { p.intensity = 5.5 * p.userData.k; p.color.set(0xffffff); });
    luzRoja.forEach((p) => { p.intensity = 0; });
    luzTrag.forEach((p) => { p.intensity = 13; });
    luzMarca.intensity = 2.2;
    M_.transl.emissiveIntensity = 1.25; M_.transl.color.set(0xffffff); M_.poli.emissiveIntensity = 0.34; M_.poli.color.set(0xf2f5f5);
    M_.luz.emissiveIntensity = 0.85; M_.luz.emissive.set(0xffffff); M_.led.emissiveIntensity = 2.0; M_.ledRojo.emissiveIntensity = 1.4;
    scene.environmentIntensity = 0.42; renderer.toneMappingExposure = 1.06;
  }
  grupos.entorno.traverse((m) => { if (m.userData.nube) m.visible = !noche; });
  grupos.entorno.traverse((m) => { if (m.isMesh && m.material.isMeshBasicMaterial && m.material.vertexColors) m.material.color.set(noche ? 0x18202e : 0xffffff); });
}
modo(NOCHE);

// ------------------------------------------------------------------ composición (oclusión ambiental) y API
let composer = null;
function crearComposer() {
  if (!CON_AO) return null;
  try {
    const rt = new THREE.WebGLRenderTarget(ANCHO, ALTO, { type: THREE.HalfFloatType, samples: 4 });
    const c = new EffectComposer(renderer, rt);
    c.addPass(new RenderPass(scene, camera));
    const ao = new GTAOPass(scene, camera, ANCHO, ALTO);
    ao.updateGtaoMaterial({ radius: 0.55, distanceExponent: 1.4, thickness: 1.2, scale: 1.15, samples: 16 });
    ao.updatePdMaterial({ lumaPhi: 10, depthPhi: 2, normalPhi: 3, radius: 6, rings: 2, samples: 16 });
    ao.blendIntensity = 0.95;
    c.addPass(ao); c.addPass(new OutputPass());
    return c;
  } catch (e) { console.warn('sin AO', e); return null; }
}
composer = crearComposer();
const controles = VISOR ? new OrbitControls(camera, canvas) : null;
if (controles) { controles.enableDamping = true; controles.maxPolarAngle = Math.PI * 0.495; controles.minDistance = 0.4; controles.maxDistance = 60; }

function pintar() { if (composer) composer.render(); else renderer.render(scene, camera); }
const APP = {
  D, scene, camera, renderer, grupos, hTecho, cielo,
  lados(vis) { grupos.cerramientoAlto.children.forEach((c) => { const l = c.userData.lado; if (l && l in vis) c.visible = vis[l]; }); },
  estudio(si) { const u = cielo.material.uniforms; if (si) { u.cenit.value.set(0xdfe3e6); u.horizonte.value.set(0xf1f0ec); u.suelo.value.set(0xe7e5e0); } },
  vista(cam, obj, fov = 55) {
    camera.fov = fov; camera.position.set(cam[0], cam[1], cam[2]); camera.lookAt(obj[0], obj[1], obj[2]); camera.updateProjectionMatrix();
    if (controles) { controles.target.set(obj[0], obj[1], obj[2]); controles.update(); }
    pintar();
  },
  ver(nombre, visible) { grupos[nombre].visible = visible; pintar(); },
  modo(noche) { modo(noche); pintar(); },
  tamano(w, h) {
    ANCHO = w; ALTO = h; renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix();
    if (composer) composer.setSize(w, h);
    pintar();
  },
  pintar,
  listo: false,
};
window.APP = APP;

export const VISTAS = {
  aerea: { cam: [L / 2 + 6.5, 13.2, W + 9.5], obj: [L / 2 - 0.2, 0, W / 2 + 0.3], fov: 40, techo: false },
  recepcion: { cam: [8.25, 1.62, 4.55], obj: [5.3, 1.25, 2.75], fov: 62, techo: true },
  peso_libre: { cam: [12.3, 1.6, 3.95], obj: [8.8, 1.0, 0.9], fov: 62, techo: true },
  sala: { cam: [7.05, 1.66, 3.72], obj: [13.6, 1.05, 3.3], fov: 68, techo: true },
  tren_inferior: { cam: [10.0, 1.65, 2.1], obj: [13.2, 0.85, 5.3], fov: 64, techo: true },
  servicios: { cam: [2.05, 1.62, 5.35], obj: [3.9, 1.2, 2.3], fov: 66, techo: true },
};
APP.VISTAS = VISTAS;
APP.ir = (n) => { const v = VISTAS[n]; grupos.techo.visible = v.techo; grupos.techoBano.visible = v.techo; grupos.cerramientoAlto.visible = true; APP.vista(v.cam, v.obj, v.fov); };
APP.ir(OPC.vista && VISTAS[OPC.vista] ? OPC.vista : 'aerea');

if (VISOR) {
  const bucle = () => { controles.update(); pintar(); requestAnimationFrame(bucle); };
  bucle();
  const ajustar = () => { const w = canvas.clientWidth, h = canvas.clientHeight; if (w && h && (w !== ANCHO || h !== ALTO)) APP.tamano(w, h); };
  new ResizeObserver(ajustar).observe(canvas);
}
APP.listo = true;
