// Texturas procedurales (canvas) y materiales compartidos. Sin imágenes externas.
import * as THREE from 'three';

function rng(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6D2B79F5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function lienzo(n = 512) {
  const c = document.createElement('canvas');
  c.width = c.height = n;
  return [c, c.getContext('2d')];
}

function texturaDe(canvas, repeat = 1, srgb = true) {
  const t = new THREE.CanvasTexture(canvas);
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.repeat.set(repeat, repeat);
  t.anisotropy = 8;
  if (srgb) t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

/** Concreto: ruido fino + manchas suaves. tamaño de baldosa de textura = 4 m */
export function texConcreto(base = [178, 176, 170], seed = 3) {
  const [c, x] = lienzo(512);
  const r = rng(seed);
  x.fillStyle = `rgb(${base.join(',')})`;
  x.fillRect(0, 0, 512, 512);
  for (let i = 0; i < 40; i++) {
    const g = x.createRadialGradient(r() * 512, r() * 512, 0, r() * 512, r() * 512, 40 + r() * 120);
    const d = (r() - 0.5) * 10;
    g.addColorStop(0, `rgba(${base[0] + d},${base[1] + d},${base[2] + d},0.12)`);
    g.addColorStop(1, 'rgba(0,0,0,0)');
    x.fillStyle = g;
    x.fillRect(0, 0, 512, 512);
  }
  const img = x.getImageData(0, 0, 512, 512);
  for (let i = 0; i < img.data.length; i += 4) {
    const n = (r() - 0.5) * 14;
    img.data[i] += n; img.data[i + 1] += n; img.data[i + 2] += n;
  }
  x.putImageData(img, 0, 0);
  return texturaDe(c);
}

/** Asfalto */
export function texAsfalto(seed = 7) {
  const [c, x] = lienzo(512);
  const r = rng(seed);
  x.fillStyle = '#4a4b4d';
  x.fillRect(0, 0, 512, 512);
  const img = x.getImageData(0, 0, 512, 512);
  for (let i = 0; i < img.data.length; i += 4) {
    const n = (r() - 0.5) * 40 + (r() < 0.02 ? 35 : 0);
    img.data[i] += n; img.data[i + 1] += n; img.data[i + 2] += n;
  }
  x.putImageData(img, 0, 0);
  for (let i = 0; i < 25; i++) {
    x.strokeStyle = `rgba(30,30,30,${0.15 + r() * 0.2})`;
    x.lineWidth = 1 + r() * 2;
    x.beginPath();
    let px = r() * 512, py = r() * 512;
    x.moveTo(px, py);
    for (let k = 0; k < 6; k++) { px += (r() - 0.5) * 60; py += (r() - 0.5) * 60; x.lineTo(px, py); }
    x.stroke();
  }
  return texturaDe(c);
}

/** Pasto */
export function texPasto(seed = 11) {
  const [c, x] = lienzo(512);
  const r = rng(seed);
  x.fillStyle = '#5d7f3a';
  x.fillRect(0, 0, 512, 512);
  for (let i = 0; i < 9000; i++) {
    const g = 90 + r() * 70;
    x.fillStyle = `rgba(${50 + r() * 50},${g},${30 + r() * 25},0.55)`;
    x.fillRect(r() * 512, r() * 512, 1 + r() * 2, 2 + r() * 5);
  }
  return texturaDe(c);
}

/** Adoquín (zona peatonal) */
export function texAdoquin(seed = 5) {
  const [c, x] = lienzo(512);
  const r = rng(seed);
  x.fillStyle = '#7d736a';
  x.fillRect(0, 0, 512, 512);
  const w = 64, h = 32;
  for (let j = 0; j < 512 / h; j++) {
    for (let i = -1; i < 512 / w + 1; i++) {
      const off = (j % 2) * w / 2;
      const d = (r() - 0.5) * 30;
      x.fillStyle = `rgb(${165 + d},${120 + d},${100 + d})`;
      x.fillRect(i * w + off + 2, j * h + 2, w - 4, h - 4);
    }
  }
  return texturaDe(c);
}

/** Tarrajeo pintado (muros) */
export function texTarrajeo(color = [232, 226, 210], seed = 13) {
  const [c, x] = lienzo(256);
  const r = rng(seed);
  x.fillStyle = `rgb(${color.join(',')})`;
  x.fillRect(0, 0, 256, 256);
  const img = x.getImageData(0, 0, 256, 256);
  for (let i = 0; i < img.data.length; i += 4) {
    const n = (r() - 0.5) * 10;
    img.data[i] += n; img.data[i + 1] += n; img.data[i + 2] += n;
  }
  x.putImageData(img, 0, 0);
  return texturaDe(c);
}

/** Texto sobre fondo transparente u opaco (rótulos, números de plaza) */
export function texTexto(texto, opts = {}) {
  const { ancho = 512, alto = 256, color = '#ffffff', fondo = null, fuente = 'bold 180px Inter, Liberation Sans, Arial',
    borde = null } = opts;
  const c = document.createElement('canvas');
  c.width = ancho; c.height = alto;
  const x = c.getContext('2d');
  if (fondo) { x.fillStyle = fondo; x.fillRect(0, 0, ancho, alto); }
  if (borde) { x.strokeStyle = borde; x.lineWidth = 10; x.strokeRect(5, 5, ancho - 10, alto - 10); }
  x.fillStyle = color;
  x.font = fuente;
  x.textAlign = 'center';
  x.textBaseline = 'middle';
  const lineas = String(texto).split('\n');
  const lh = alto / (lineas.length + 0.2);
  lineas.forEach((l, i) => x.fillText(l, ancho / 2, lh * (i + 0.6)));
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 8;
  return t;
}

/** Símbolo de accesibilidad (silla de ruedas) */
export function texAccesible() {
  const c = document.createElement('canvas');
  c.width = c.height = 256;
  const x = c.getContext('2d');
  x.strokeStyle = '#ffffff';
  x.fillStyle = '#ffffff';
  x.lineWidth = 16;
  x.lineCap = 'round';
  x.beginPath(); x.arc(118, 48, 20, 0, Math.PI * 2); x.fill();
  x.beginPath(); x.moveTo(112, 80); x.lineTo(112, 150); x.lineTo(176, 150); x.lineTo(200, 210); x.stroke();
  x.beginPath(); x.moveTo(112, 110); x.lineTo(165, 110); x.stroke();
  x.beginPath(); x.arc(112, 172, 58, Math.PI * 0.15, Math.PI * 1.25); x.stroke();
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

/** Flecha de circulación (apunta hacia +X de la textura) */
export function texFlecha() {
  const c = document.createElement('canvas');
  c.width = 512; c.height = 256;
  const x = c.getContext('2d');
  x.fillStyle = '#f4f4f0';
  x.beginPath();
  x.moveTo(20, 100); x.lineTo(320, 100); x.lineTo(320, 40); x.lineTo(490, 128);
  x.lineTo(320, 216); x.lineTo(320, 156); x.lineTo(20, 156); x.closePath();
  x.fill();
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

/** Franjas de seguridad amarillo/negro (base de columnas) */
export function texFranjas() {
  const c = document.createElement('canvas');
  c.width = c.height = 128;
  const x = c.getContext('2d');
  x.fillStyle = '#f2c200';
  x.fillRect(0, 0, 128, 128);
  x.fillStyle = '#1b1b1b';
  for (let i = -128; i < 256; i += 64) {
    x.beginPath();
    x.moveTo(i, 128); x.lineTo(i + 32, 128); x.lineTo(i + 160, 0); x.lineTo(i + 128, 0); x.closePath(); x.fill();
  }
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

export { rng };
