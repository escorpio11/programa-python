// Modelo 3D del proyecto a partir de escena.json: piso, señalización, cerco,
// portones, coberturas metálicas (columnas, vigas reticuladas, correas, TR-4),
// garita y servicios. Coordenadas: x = u, y = altura, z = -v (m).
import * as THREE from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { texConcreto, texAdoquin, texPasto, texTarrajeo, texTexto, texAccesible, texFlecha, texFranjas } from './texturas.js';

const V3 = (a) => new THREE.Vector3(a[0], a[1], a[2]);

// ---------------------------------------------------------------- materiales
export function materialesProyecto() {
  const concreto = texConcreto([170, 168, 163], 3);
  concreto.repeat.set(0.25, 0.25);
  const concretoPasillo = texConcreto([156, 155, 152], 9);
  concretoPasillo.repeat.set(0.25, 0.25);
  const ador = texAdoquin(); ador.repeat.set(0.5, 0.5);
  const pasto = texPasto(); pasto.repeat.set(0.3, 0.3);
  const tarr = texTarrajeo([214, 202, 176]); tarr.repeat.set(0.5, 0.5);
  return {
    piso: new THREE.MeshStandardMaterial({ map: concreto, roughness: 0.92, metalness: 0 }),
    pasillo: new THREE.MeshStandardMaterial({ map: concretoPasillo, roughness: 0.9, metalness: 0 }),
    adoquin: new THREE.MeshStandardMaterial({ map: ador, roughness: 0.95 }),
    pasto: new THREE.MeshStandardMaterial({ map: pasto, roughness: 1 }),
    muro: new THREE.MeshStandardMaterial({ map: tarr, roughness: 0.95 }),
    zocalo: new THREE.MeshStandardMaterial({ color: 0x5b6f86, roughness: 0.8 }),
    remate: new THREE.MeshStandardMaterial({ color: 0x9aa3ab, roughness: 0.7 }),
    acero: new THREE.MeshStandardMaterial({ color: 0xc9cdd2, roughness: 0.5, metalness: 0.3 }),
    columna: new THREE.MeshStandardMaterial({ color: 0xd4d7db, roughness: 0.5, metalness: 0.25 }),
    franjas: new THREE.MeshStandardMaterial({ map: texFranjas(), roughness: 0.6 }),
    correa: new THREE.MeshStandardMaterial({ color: 0xa3aab1, roughness: 0.4, metalness: 0.6 }),
    tensor: new THREE.MeshStandardMaterial({ color: 0x8f969c, roughness: 0.4, metalness: 0.8 }),
    techoSup: new THREE.MeshStandardMaterial({ color: 0x2c5282, roughness: 0.38, metalness: 0.45, side: THREE.FrontSide }),
    techoInf: new THREE.MeshStandardMaterial({ color: 0xb7bcc2, roughness: 0.75, metalness: 0.1, side: THREE.BackSide }),
    fascia: new THREE.MeshStandardMaterial({ color: 0xf2f3f5, roughness: 0.5, metalness: 0.3 }),
    canaleta: new THREE.MeshStandardMaterial({ color: 0xc6ccd2, roughness: 0.35, metalness: 0.75 }),
    pvc: new THREE.MeshStandardMaterial({ color: 0xe8e8e6, roughness: 0.6 }),
    luminaria: new THREE.MeshStandardMaterial({ color: 0xfafafa, emissive: 0xfff3dd, emissiveIntensity: 0.0, roughness: 0.4 }),
    dado: new THREE.MeshStandardMaterial({ map: concreto, color: 0xd4d2cc, roughness: 0.9 }),
    lineaBlanca: new THREE.MeshStandardMaterial({ color: 0xf3f3ee, roughness: 0.7, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 }),
    lineaAmarilla: new THREE.MeshStandardMaterial({ color: 0xf0c419, roughness: 0.7, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 }),
    azulAcc: new THREE.MeshStandardMaterial({ color: 0x1f5fa8, roughness: 0.75, polygonOffset: true, polygonOffsetFactor: -1, polygonOffsetUnits: -1 }),
    tope: new THREE.MeshStandardMaterial({ color: 0xf0c419, roughness: 0.75 }),
    porton: new THREE.MeshStandardMaterial({ color: 0x2b2f33, roughness: 0.45, metalness: 0.6 }),
    vidrio: new THREE.MeshPhysicalMaterial({ color: 0x9fb4c4, roughness: 0.05, metalness: 0.1, transmission: 0, transparent: true, opacity: 0.55 }),
    marco: new THREE.MeshStandardMaterial({ color: 0x3a3f44, roughness: 0.5, metalness: 0.5 }),
    losa: new THREE.MeshStandardMaterial({ color: 0xdcdad4, roughness: 0.85 }),
    puerta: new THREE.MeshStandardMaterial({ color: 0x6b4f3a, roughness: 0.7 }),
    bolardo: new THREE.MeshStandardMaterial({ color: 0xf0c419, roughness: 0.6 }),
    sardinel: new THREE.MeshStandardMaterial({ color: 0xbdbab3, roughness: 0.9 }),
  };
}

// ---------------------------------------------------------------- utilidades
function shapeDe(poly) {
  // poly: {ext:[[x,z]...], huecos:[[...]]}; shape en (x, -z) para extruir hacia +y tras rotar
  const s = new THREE.Shape(poly.ext.map(([x, z]) => new THREE.Vector2(x, -z)));
  for (const h of poly.huecos || []) s.holes.push(new THREE.Path(h.map(([x, z]) => new THREE.Vector2(x, -z))));
  return s;
}

/** Losa/volumen vertical a partir de polígono en planta, entre y0 e y1 */
export function prisma(poly, y0, y1, uvEscala = 1) {
  const geo = new THREE.ExtrudeGeometry(shapeDe(poly), { depth: y1 - y0, bevelEnabled: false });
  geo.rotateX(-Math.PI / 2);          // shape (x, -z) -> plano XZ, extrusión hacia +y
  geo.translate(0, y0, 0);
  planarUV(geo, uvEscala);
  return geo;
}

/** Superficie plana horizontal (y) a partir de polígono */
export function superficie(poly, y) {
  const geo = new THREE.ShapeGeometry(shapeDe(poly));
  geo.rotateX(-Math.PI / 2);
  geo.translate(0, y, 0);
  planarUV(geo, 1);
  return geo;
}

function planarUV(geo, k) {
  const p = geo.attributes.position;
  const uv = new Float32Array(p.count * 2);
  const n = geo.attributes.normal;
  for (let i = 0; i < p.count; i++) {
    const nx = Math.abs(n ? n.getX(i) : 0), ny = Math.abs(n ? n.getY(i) : 1);
    if (ny > 0.7) { uv[2 * i] = p.getX(i) * k; uv[2 * i + 1] = p.getZ(i) * k; }
    else if (nx > 0.7) { uv[2 * i] = p.getZ(i) * k; uv[2 * i + 1] = p.getY(i) * k; }
    else { uv[2 * i] = p.getX(i) * k; uv[2 * i + 1] = p.getY(i) * k; }
  }
  geo.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
}

/** Caja orientada a lo largo del segmento a-b; w = ancho horizontal, h = alto */
export function barra(a, b, w, h, lado) {
  const A = V3(a), B = V3(b);
  const L = A.distanceTo(B);
  const geo = new THREE.BoxGeometry(L, h, w);
  const dir = B.clone().sub(A).normalize();
  let up = new THREE.Vector3(0, 1, 0);
  if (Math.abs(dir.dot(up)) > 0.98) up = lado ? V3(lado).normalize() : new THREE.Vector3(1, 0, 0);
  const zz = new THREE.Vector3().crossVectors(dir, up).normalize();
  const yy = new THREE.Vector3().crossVectors(zz, dir).normalize();
  const m = new THREE.Matrix4().makeBasis(dir, yy, zz);
  m.setPosition(A.clone().add(B).multiplyScalar(0.5));
  geo.applyMatrix4(m);
  return geo;
}

function malla(geos, mat, sombra = true) {
  if (!geos.length) return null;
  const geo = geos.length === 1 ? geos[0] : mergeGeometries(geos, false);
  const me = new THREE.Mesh(geo, mat);
  me.castShadow = sombra;
  me.receiveShadow = true;
  return me;
}

/** Calcomanía horizontal (plano) en el piso */
function calco(tex, cx, cz, ancho, alto, angulo, y = 0.012, mat = null) {
  const m = mat || new THREE.MeshStandardMaterial({ map: tex, transparent: true, roughness: 0.75, depthWrite: false,
    polygonOffset: true, polygonOffsetFactor: -4, polygonOffsetUnits: -4 });
  const me = new THREE.Mesh(new THREE.PlaneGeometry(ancho, alto), m);
  me.rotation.x = -Math.PI / 2;
  me.rotation.z = angulo;
  me.position.set(cx, y, cz);
  me.receiveShadow = true;
  return me;
}

/** Plancha TR-4 (nervios trapezoidales a lo largo de la pendiente) */
function planchaTR4(esq, dirS, matSup, matInf) {
  const P00 = V3(esq[0]), P10 = V3(esq[1]), P11 = V3(esq[2]), P01 = V3(esq[3]);
  const L = P00.distanceTo(P10);
  const paso = 0.25, hN = 0.035;
  const perfil = [];
  for (let s = 0; s <= L + 1e-6; s += paso) {
    perfil.push([s, 0], [s + 0.06, 0.0], [s + 0.09, hN], [s + 0.16, hN], [s + 0.19, 0]);
  }
  const pos = [], idx = [];
  const fila0 = [], fila1 = [];
  for (const [s, h] of perfil) {
    const f = Math.min(s / L, 1);
    const a = P00.clone().lerp(P10, f);
    const b = P01.clone().lerp(P11, f);
    fila0.push(a.x, a.y + h, a.z);
    fila1.push(b.x, b.y + h, b.z);
  }
  const n = perfil.length;
  pos.push(...fila0, ...fila1);
  for (let i = 0; i < n - 1; i++) {
    const a = i, b = i + 1, c = n + i, d = n + i + 1;
    idx.push(a, c, b, b, c, d);
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  geo.setIndex(idx);
  geo.computeVertexNormals();
  // orientar normales hacia arriba
  const nrm = geo.attributes.normal;
  let sum = 0; for (let i = 0; i < nrm.count; i++) sum += nrm.getY(i);
  if (sum < 0) { idx.reverse(); geo.setIndex(idx); geo.computeVertexNormals(); }
  const sup = new THREE.Mesh(geo, matSup);
  sup.castShadow = true; sup.receiveShadow = true;
  const inf = new THREE.Mesh(geo, matInf);
  inf.position.y = -0.003;
  inf.receiveShadow = true;
  const g = new THREE.Group();
  g.add(sup, inf);
  return g;
}

// ---------------------------------------------------------------- proyecto
export function crearProyecto(d, mat = materialesProyecto()) {
  const raiz = new THREE.Group();
  raiz.name = 'proyecto';

  // ---- pisos
  const lote = { ext: d.lote, huecos: [] };
  const piso = new THREE.Mesh(superficie(lote, 0.0), mat.piso);
  piso.receiveShadow = true; piso.name = 'piso';
  raiz.add(piso);
  for (const c of d.circulacion) {
    const me = new THREE.Mesh(superficie(c, 0.002), mat.pasillo);
    me.receiveShadow = true; raiz.add(me);
  }
  for (const z of d.zona_interior) {
    const me = new THREE.Mesh(superficie(z, 0.004), mat.adoquin);
    me.receiveShadow = true; raiz.add(me);
  }

  // ---- señalización de plazas
  const lineas = [], azules = [], topes = [];
  const texAcc = texAccesible();
  for (const p of d.plazas) {
    const [fx, fz] = p.frente;
    const sx = -fz, sz = fx;              // dirección a lo largo de la fila
    const ang = Math.atan2(-fz, fx);      // rotación para orientar +x local a 'frente'
    const fondo = new THREE.Vector3(p.fondo[0], 0, p.fondo[1]);
    const prof = Math.hypot(p.frente_pt[0] - p.fondo[0], p.frente_pt[1] - p.fondo[1]);
    // líneas laterales (en ambos bordes de cada plaza) + línea de fondo
    for (const lado of [-1, 1]) {
      const c = fondo.clone().add(new THREE.Vector3(sx * lado * p.ancho / 2, 0, sz * lado * p.ancho / 2));
      const a = [c.x, 0.006, c.z];
      const b = [c.x + fx * prof, 0.006, c.z + fz * prof];
      const g = barra(a, b, 0.10, 0.004);
      lineas.push(g);
    }
    if (p.tipo === 'accesible') {
      const cx = (p.fondo[0] + p.frente_pt[0]) / 2, cz = (p.fondo[1] + p.frente_pt[1]) / 2;
      const g = new THREE.PlaneGeometry(prof - 0.1, p.ancho - 0.1);
      g.rotateX(-Math.PI / 2); g.rotateY(ang); g.translate(cx, 0.004, cz);
      azules.push(g);
      raiz.add(calco(texAcc, cx + fx * 0.6 - sx * 0.55, cz + fz * 0.6 - sz * 0.55, 1.5, 1.5, ang - Math.PI / 2, 0.012));
      // franjas de transferencia (1.20 m) lado derecho
      for (let k = 0; k < 6; k++) {
        const off = p.ancho / 2 - 0.6;
        const t0 = 0.6 + k * 0.75;
        const a = [p.fondo[0] + sx * (off - 0.5) + fx * t0, 0.007, p.fondo[1] + sz * (off - 0.5) + fz * t0];
        const b = [p.fondo[0] + sx * (off + 0.5) + fx * (t0 + 0.45), 0.007, p.fondo[1] + sz * (off + 0.5) + fz * (t0 + 0.45)];
        lineas.push(barra(a, b, 0.12, 0.003));
      }
    }
    // número de plaza
    const tn = texTexto(p.codigo, { ancho: 256, alto: 160, fuente: 'bold 130px Inter, Liberation Sans, Arial', color: '#f5f5f0' });
    raiz.add(calco(tn, p.num[0], p.num[1], 0.9, 0.56, ang + Math.PI / 2, 0.012));
    // tope de llantas
    const t = barra([p.tope[0] - sx * 0.8, 0.06, p.tope[1] - sz * 0.8], [p.tope[0] + sx * 0.8, 0.06, p.tope[1] + sz * 0.8], 0.15, 0.10);
    topes.push(t);
  }
  raiz.add(malla(lineas, mat.lineaBlanca, false));
  if (azules.length) raiz.add(malla(azules, mat.azulAcc, false));
  raiz.add(malla(topes, mat.tope, true));

  // flechas de circulación
  const tf = texFlecha();
  for (const f of d.flechas) {
    raiz.add(calco(tf, f.pos[0], f.pos[1], 3.2, 1.6, Math.atan2(-f.dir[1], f.dir[0]), 0.012));
  }

  // ---- cerco perimetral
  const H = d.cerco.altura;
  const muroGeo = [], zocaloGeo = [], remateGeo = [], colGeo = [];
  for (const m of d.cerco.muros) {
    muroGeo.push(prisma(m, 0.30, H, 1));
    zocaloGeo.push(prisma(m, 0.0, 0.30, 1));
  }
  // remate (sombrero) sobre el muro: polígono algo más ancho
  for (const m of d.cerco.muros) remateGeo.push(prisma(m, H, H + 0.06, 1));
  for (const c of d.cerco.columnetas) {
    const g = new THREE.BoxGeometry(0.28, H + 0.12, 0.28);
    g.translate(c[0], (H + 0.12) / 2, c[1]);
    colGeo.push(g);
  }
  raiz.add(malla(muroGeo, mat.muro));
  raiz.add(malla(zocaloGeo, mat.zocalo));
  raiz.add(malla(remateGeo, mat.remate));
  raiz.add(malla(colGeo, mat.muro));

  // ---- portones y puertas
  for (const a of d.accesos) {
    const A = new THREE.Vector3(a.a[0], 0, a.a[1]), B = new THREE.Vector3(a.b[0], 0, a.b[1]);
    const dir = new THREE.Vector3(a.dir[0], 0, a.dir[1]);
    const adentro = new THREE.Vector3(a.hacia_adentro[0], 0, a.hacia_adentro[1]);
    const ang = Math.atan2(-dir.z, dir.x);
    // pilares de vano
    for (const P of [A, B]) {
      const g = new THREE.BoxGeometry(0.35, H + 0.25, 0.35);
      const me = new THREE.Mesh(g, mat.muro);
      me.position.set(P.x - dir.x * (P === A ? 0.18 : -0.18), (H + 0.25) / 2, P.z - dir.z * (P === A ? 0.18 : -0.18));
      me.castShadow = me.receiveShadow = true;
      raiz.add(me);
    }
    if (a.tipo === 'porton') {
      // hoja corrediza abierta: desplazada a lo largo del muro, por dentro
      const hoja = new THREE.Group();
      const Lh = a.ancho + 0.2, Hh = 2.25;
      const marcoG = [];
      marcoG.push(barra([0, 0.08, 0], [Lh, 0.08, 0], 0.06, 0.08), barra([0, Hh, 0], [Lh, Hh, 0], 0.06, 0.08),
        barra([0, 0.08, 0], [0, Hh, 0], 0.06, 0.08, [0, 0, 1]), barra([Lh, 0.08, 0], [Lh, Hh, 0], 0.06, 0.08, [0, 0, 1]));
      for (let x = 0.12; x < Lh - 0.05; x += 0.12) marcoG.push(barra([x, 0.1, 0], [x, Hh, 0], 0.025, 0.025, [0, 0, 1]));
      hoja.add(malla(marcoG, mat.porton));
      const s = a.desliza;
      const inicio = s > 0 ? B.clone() : A.clone();
      const base = inicio.clone().add(adentro.clone().multiplyScalar(0.12));
      hoja.position.copy(base);
      hoja.rotation.y = ang + (s > 0 ? 0 : Math.PI);
      raiz.add(hoja);
      // riel
      const r = barra([A.x - dir.x * 3.4 * (s < 0 ? 1 : 0), 0.01, A.z - dir.z * 3.4 * (s < 0 ? 1 : 0)],
        [B.x + dir.x * 3.4 * (s > 0 ? 1 : 0), 0.01, B.z + dir.z * 3.4 * (s > 0 ? 1 : 0)], 0.06, 0.02);
      raiz.add(malla([r], mat.marco, false));
      // letrero sobre el portón
      const color = a.texto === 'INGRESO' ? '#1f8a4c' : '#c0392b';
      const tl = texTexto(a.texto === 'INGRESO' ? '➜ INGRESO' : 'SALIDA ➜', { ancho: 1024, alto: 220, fondo: color,
        fuente: 'bold 150px Inter, Liberation Sans, DejaVu Sans, Arial' });
      for (const sg of [1, -1]) {
        const cartel = new THREE.Mesh(new THREE.PlaneGeometry(3.0, 0.62), new THREE.MeshStandardMaterial({ map: tl, roughness: 0.5,
          emissive: 0xffffff, emissiveMap: tl, emissiveIntensity: 0.12 }));
        const c = A.clone().add(B).multiplyScalar(0.5);
        cartel.position.set(c.x - adentro.x * 0.05 * sg, H + 0.62, c.z - adentro.z * 0.05 * sg);
        cartel.rotation.y = Math.atan2(-adentro.x * sg, -adentro.z * sg) + 0;
        cartel.lookAt(cartel.position.x - adentro.x * sg, cartel.position.y, cartel.position.z - adentro.z * sg);
        raiz.add(cartel);
      }
      const viga = barra([A.x, H + 0.25, A.z], [B.x, H + 0.25, B.z], 0.20, 0.10);
      const vigaSup = barra([A.x, H + 0.98, A.z], [B.x, H + 0.98, B.z], 0.12, 0.06);
      raiz.add(malla([viga, vigaSup], mat.marco));
      for (const P of [A, B]) raiz.add(malla([barra([P.x, H + 0.2, P.z], [P.x, H + 1.0, P.z], 0.06, 0.06, [dir.x, 0, dir.z])], mat.marco));
    } else {
      const g = barra([A.x + dir.x * 0.02, 1.05, A.z + dir.z * 0.02], [B.x - dir.x * 0.02, 1.05, B.z - dir.z * 0.02], 0.05, 2.1);
      raiz.add(malla([g], mat.porton));
      const dintel = barra([A.x, 2.25, A.z], [B.x, 2.25, B.z], 0.18, 0.3);
      raiz.add(malla([dintel], mat.muro));
    }
  }

  // ---- letrero de esquina (frente a la intersección)
  {
    const A = d.vertices.A, B = d.vertices.B, D = d.vertices.D;
    const tAB = new THREE.Vector3(B[0] - A[0], 0, B[1] - A[1]).normalize();
    const tAD = new THREE.Vector3(D[0] - A[0], 0, D[1] - A[1]).normalize();
    const bis = tAB.clone().add(tAD).normalize();           // hacia el interior
    const pos = new THREE.Vector3(A[0], 0, A[1]).add(bis.clone().multiplyScalar(1.4));
    const panel = new THREE.Group();
    const tx = texTexto('P  ESTACIONAMIENTO\nTECHADO · 24 H', { ancho: 1400, alto: 420, fondo: '#163a63',
      fuente: 'bold 120px Inter, Liberation Sans, Arial' });
    const cara = new THREE.Mesh(new THREE.PlaneGeometry(4.2, 1.26), new THREE.MeshStandardMaterial({ map: tx, roughness: 0.45,
      emissive: 0xffffff, emissiveMap: tx, emissiveIntensity: 0.15 }));
    cara.position.y = 4.6;
    panel.add(cara);
    const dorso = new THREE.Mesh(new THREE.BoxGeometry(4.3, 1.36, 0.10), mat.marco);
    dorso.position.set(0, 4.6, -0.07);
    panel.add(dorso);
    for (const sx of [-1.6, 1.6]) {
      const poste = new THREE.Mesh(new THREE.BoxGeometry(0.12, 4.0, 0.12), mat.marco);
      poste.position.set(sx, 2.0, -0.07);
      poste.castShadow = true;
      panel.add(poste);
    }
    panel.position.copy(pos);
    const mira = bis.clone().negate();
    panel.rotation.y = Math.atan2(mira.x, mira.z);
    raiz.add(panel);
  }

  // ---- edificaciones (garita, SS.HH., depósito)
  for (const e of d.edificaciones) {
    for (const p of e.poly) {
      const cuerpo = new THREE.Mesh(prisma(p, 0, e.altura, 1), mat.muro);
      cuerpo.castShadow = cuerpo.receiveShadow = true;
      raiz.add(cuerpo);
      // losa con alero
      const cx = p.ext.reduce((s, q) => s + q[0], 0) / p.ext.length, cz = p.ext.reduce((s, q) => s + q[1], 0) / p.ext.length;
      const ext = { ext: p.ext.map(([x, z]) => [cx + (x - cx) * 1.18, cz + (z - cz) * 1.18]), huecos: [] };
      const losa = new THREE.Mesh(prisma(ext, e.altura, e.altura + 0.15, 1), mat.losa);
      losa.castShadow = losa.receiveShadow = true;
      raiz.add(losa);
      // ventanas / puerta: franja de vidrio en cada cara (garita) o puerta (servicios)
      const n = p.ext.length;
      for (let i = 0; i < n; i++) {
        const a = p.ext[i], b = p.ext[(i + 1) % n];
        const L = Math.hypot(b[0] - a[0], b[1] - a[1]);
        const ux = (b[0] - a[0]) / L, uz = (b[1] - a[1]) / L;
        let nx = uz, nz = -ux;
        if ((a[0] + nx * 0.5 - cx) ** 2 + (a[1] + nz * 0.5 - cz) ** 2 < (a[0] - cx) ** 2 + (a[1] - cz) ** 2) { nx = -nx; nz = -nz; }
        const mx = (a[0] + b[0]) / 2 + nx * 0.012, mz = (a[1] + b[1]) / 2 + nz * 0.012;
        if (e.nombre.startsWith('Garita')) {
          const v = new THREE.Mesh(new THREE.PlaneGeometry(L * 0.7, 0.9), mat.vidrio);
          v.position.set(mx, 1.55, mz);
          v.lookAt(mx + nx, 1.55, mz + nz);
          raiz.add(v);
          const mr = barra([mx - ux * L * 0.36, 1.08, mz - uz * L * 0.36], [mx + ux * L * 0.36, 1.08, mz + uz * L * 0.36], 0.08, 0.05);
          raiz.add(malla([mr], mat.marco));
        } else if (i === 0) {
          const pu = new THREE.Mesh(new THREE.PlaneGeometry(0.9, 2.05), mat.puerta);
          pu.position.set(mx, 1.03, mz);
          pu.lookAt(mx + nx, 1.03, mz + nz);
          raiz.add(pu);
        }
      }
    }
  }
  // bolardos del paso de motos
  for (const pm of d.paso_motos) {
    const e = pm.ext;
    // bolardos en el lado hacia el pasillo (primer borde)
    for (const f of [0.3, 0.7]) {
      const x = e[0][0] + (e[3][0] - e[0][0]) * f, z = e[0][1] + (e[3][1] - e[0][1]) * f;
      const b = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.09, 0.9, 12), mat.bolardo);
      b.position.set(x, 0.45, z); b.castShadow = true; raiz.add(b);
    }
  }

  // ---- coberturas metálicas
  const lum = [];
  for (const cob of d.coberturas) {
    const g = new THREE.Group();
    g.name = 'cobertura-' + cob.nombre;
    const porTipo = {};
    for (const m of cob.miembros) (porTipo[m.t] = porTipo[m.t] || []).push(m);
    const geo = (lst) => lst.map((m) => barra(m.a, m.b, m.w, m.h, m.lado));
    const add = (lst, material, sombra = true) => { const me = lst && lst.length ? malla(geo(lst), material, sombra) : null; if (me) g.add(me); };
    add(porTipo.cordon, mat.acero);
    add(porTipo.diagonal, mat.acero);
    add(porTipo.cartela, mat.acero);
    add(porTipo.correa, mat.correa);
    add(porTipo.tensor, mat.tensor, false);
    add(porTipo.canaleta, mat.canaleta);
    add(porTipo.bajada, mat.pvc);
    add(porTipo.fascia, mat.fascia);
    // columnas: cuerpo blanco + franja de seguridad (0 a 1.0 m)
    for (const c of porTipo.columna || []) {
      const a = c.a.slice(), b = c.b.slice();
      const corte = [a[0], 1.1, a[2]];
      g.add(malla([barra(corte, b, c.w, c.h, c.lado)], mat.columna));
      const fr = malla([barra(a, corte, c.w + 0.004, c.h + 0.004, c.lado)], mat.franjas);
      g.add(fr);
      // placa base
      const pb = barra([a[0], 0.10, a[2]], [a[0], 0.125, a[2]], 0.35, 0.5, c.lado);
      g.add(malla([pb], mat.marco));
    }
    for (const l of porTipo.luminaria || []) lum.push(barra(l.a, l.b, l.w, l.h));
    // dados de concreto
    for (const dd of cob.dados) {
      const bx = new THREE.BoxGeometry(dd.lx, 0.10, dd.lz);
      const ang = Math.atan2(-dd.dir_s[2], dd.dir_s[0]);
      bx.rotateY(ang);
      bx.translate(dd.centro[0], 0.05, dd.centro[2]);
      g.add(malla([bx], mat.dado));
    }
    // plancha TR-4
    const tr4 = planchaTR4(cob.techo.esquinas, cob.techo.dir_s, mat.techoSup, mat.techoInf);
    tr4.name = 'tr4';
    g.add(tr4);
    raiz.add(g);
  }
  if (lum.length) {
    const me = malla(lum, mat.luminaria, false);
    me.name = 'luminarias';
    raiz.add(me);
  }
  raiz.userData.materiales = mat;
  return raiz;
}
