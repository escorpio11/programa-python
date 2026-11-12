// Banco del revisor: misma iluminacion que main.js (sol 2.7, hemi 0.42, exposicion 0.86, entorno con suelo).
import * as THREE from 'three';
import { Sky } from 'three/addons/objects/Sky.js';
import { crearVehiculo, DIMENSIONES, COLORES_AUTOS } from '../vehiculos.js';
import { texConcreto } from '../texturas.js';

const qs = new URLSearchParams(location.search);
const ANCHO = +qs.get('w') || window.innerWidth;
const ALTO = +qs.get('h') || window.innerHeight;
const canvas = document.getElementById('lienzo');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(1);
renderer.setSize(ANCHO, ALTO, false);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 0.86;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(40, ANCHO / ALTO, 0.1, 3000);
const sky = new Sky();
sky.scale.setScalar(4000);
const su = sky.material.uniforms;
su.turbidity.value = 4.5; su.rayleigh.value = 1.6; su.mieCoefficient.value = 0.004; su.mieDirectionalG.value = 0.82;
scene.add(sky);
const norte = new THREE.Vector3(0.8181, 0, -0.5751).normalize();
const oeste = new THREE.Vector3(norte.z, 0, -norte.x);
const elevSol = THREE.MathUtils.degToRad(38);
const dirSol = oeste.clone().multiplyScalar(Math.cos(elevSol) * 0.85).add(norte.clone().multiplyScalar(Math.cos(elevSol) * 0.35));
dirSol.y = Math.sin(elevSol); dirSol.normalize();
su.sunPosition.value.copy(dirSol);
const sol = new THREE.DirectionalLight(0xffeccc, 2.7);
sol.position.copy(dirSol.clone().multiplyScalar(60));
sol.castShadow = true;
sol.shadow.mapSize.set(4096, 4096);
const sc = sol.shadow.camera;
sc.left = -18; sc.right = 18; sc.top = 18; sc.bottom = -18; sc.near = 5; sc.far = 140;
sol.shadow.bias = -0.0004; sol.shadow.normalBias = 0.03; sol.shadow.radius = 3;
scene.add(sol, sol.target);
scene.add(new THREE.HemisphereLight(0xcfe3ff, 0x5d5444, 0.42));
{
  const pmrem = new THREE.PMREMGenerator(renderer);
  const skyScene = new THREE.Scene();
  const sky2 = new Sky(); sky2.scale.setScalar(4000);
  Object.keys(su).forEach((k) => { if (sky2.material.uniforms[k]) sky2.material.uniforms[k].value = su[k].value; });
  skyScene.add(sky2);
  const sueloEnv = new THREE.Mesh(new THREE.CircleGeometry(3000, 32), new THREE.MeshBasicMaterial({ color: 0x8a877d }));
  sueloEnv.rotation.x = -Math.PI / 2; sueloEnv.position.y = -2; skyScene.add(sueloEnv);
  scene.environment = pmrem.fromScene(skyScene, 0.02).texture;
}
scene.fog = new THREE.FogExp2(0xc4d3e2, 0.0009);
const tex = texConcreto([128, 128, 125], 3); tex.repeat.set(12, 12);
const piso = new THREE.Mesh(new THREE.PlaneGeometry(80, 80), new THREE.MeshStandardMaterial({ map: tex, roughness: 0.92 }));
piso.rotation.x = -Math.PI / 2; piso.receiveShadow = true; scene.add(piso);

// techo opcional (simula la cobertura: sombra completa sobre los autos)
const techo = new THREE.Mesh(new THREE.BoxGeometry(8, 0.1, 30), new THREE.MeshStandardMaterial({ color: 0x3a5fae }));
techo.position.set(0, 4.2, 0); techo.castShadow = true; techo.visible = false; scene.add(techo);

// sombra de main.js (conSombra) para ver la acumulacion
const texSombra = (() => {
  const c = document.createElement('canvas'); c.width = c.height = 128;
  const x = c.getContext('2d');
  const g = x.createRadialGradient(64, 64, 8, 64, 64, 64);
  g.addColorStop(0, 'rgba(0,0,0,0.55)'); g.addColorStop(0.55, 'rgba(0,0,0,0.32)'); g.addColorStop(1, 'rgba(0,0,0,0)');
  x.fillStyle = g; x.fillRect(0, 0, 128, 128);
  return new THREE.CanvasTexture(c);
})();
const matSombraMain = new THREE.MeshBasicMaterial({ map: texSombra, transparent: true, depthWrite: false, polygonOffset: true,
  polygonOffsetFactor: -6, polygonOffsetUnits: -6 });
function conSombra(v, tipo) {
  const d = DIMENSIONES[tipo];
  const s = new THREE.Mesh(new THREE.PlaneGeometry(d.largo * 1.18, d.ancho * 1.35), matSombraMain);
  s.rotation.x = -Math.PI / 2; s.position.y = 0.015; s.renderOrder = 1; s.name = 'sombraMain';
  v.add(s); return v;
}

let grupo = new THREE.Group(); scene.add(grupo);
const TIPOS = ['sedan', 'hatchback', 'suv', 'pickup', 'van', 'moto', 'mototaxi'];
function escena(nombre, opts = {}) {
  scene.remove(grupo); grupo = new THREE.Group(); scene.add(grupo);
  const info = [];
  const add = (t, color, seed, x, z, ry = 0) => {
    const v = crearVehiculo(t, { color, seed });
    if (opts.sombraMain) conSombra(v, t);
    v.position.set(x, 0, z); v.rotation.y = ry; grupo.add(v); info.push({ v, t });
  };
  if (nombre === 'fila') {
    // como main.js: plazas de 2.50 m, mitad en reversa, colores del catalogo, + techo
    const tipos = ['sedan', 'pickup', 'suv', 'sedan', 'hatchback', 'pickup', 'van', 'sedan', 'suv', 'pickup'];
    tipos.forEach((t, i) => {
      const rev = [1, 0, 1, 1, 0, 1, 0, 0, 1, 0][i];
      const L = DIMENSIONES[t].largo;
      const x = 0.15 + (rev ? 1.05 : 0.90) + L / 2 - 0.15;
      add(t, COLORES_AUTOS[(i * 7 + 3) % 10], i + 1, -x, (i - 4.5) * 2.5, rev ? Math.PI : 0);
    });
  } else if (nombre === 'heroes') {
    add('pickup', '#f2f2f0', 500, 0, -3.2); add('sedan', '#8e1b1b', 501, 0, 0); add('suv', '#2b2d30', 502, 0, 3.2);
  } else if (nombre === 'solo') {
    add(opts.tipo, opts.color, opts.seed ?? 1, 0, 0);
  } else if (nombre === 'colores') {
    // los 10 colores de catalogo en sedan, en dos filas
    COLORES_AUTOS.forEach((c, i) => add('sedan', c, 1, (i % 5 - 2) * 5.2, (Math.floor(i / 5) - 0.5) * 3.0));
  } else if (nombre === 'motos') {
    const cols = ['#1b1b1b', '#b3261e', '#1d4f91', '#e0e0e0', '#2e6b30'];
    cols.forEach((c, i) => add('moto', c, 100 + i, 0, (i - 2) * 0.95));
    add('mototaxi', '#b3261e', 105, 0, 4.0); add('mototaxi', '#1d4f91', 106, 0, -4.2);
  } else {
    TIPOS.forEach((t, i) => {
      const color = t === 'moto' ? '#b3261e' : t === 'mototaxi' ? '#1d4f91' : COLORES_AUTOS[[7, 6, 3, 4, 0][i] ?? 0];
      add(t, color, i + 1, 0, (i - 3) * 3.0);
    });
  }
  grupo.updateMatrixWorld(true);
  window.APP.vehiculos = info;
}

window.APP = {
  scene, camera, renderer, escena, techo,
  vista(pos, obj, fov = 40) {
    camera.fov = fov; camera.aspect = ANCHO / ALTO;
    camera.position.set(...pos); camera.lookAt(new THREE.Vector3(...obj)); camera.updateProjectionMatrix();
    renderer.render(scene, camera);
  },
  alambre(on) {
    for (const { v } of window.APP.vehiculos) v.traverse((o) => {
      if (!o.isMesh || o.name.startsWith('sombra')) return;
      (Array.isArray(o.material) ? o.material : [o.material]).forEach((m) => { m.wireframe = on; });
    });
  },
  plano(on) {
    for (const { v } of window.APP.vehiculos) v.traverse((o) => {
      if (!o.isMesh || o.name.startsWith('sombra')) return;
      (Array.isArray(o.material) ? o.material : [o.material]).forEach((m) => { m.flatShading = on; m.needsUpdate = true; });
    });
  },
  girar(a) { for (const { v } of window.APP.vehiculos) for (const r of v.userData.ruedas || []) r.rotation.z = a; },
  medir() {
    const out = [];
    for (const { v, t } of window.APP.vehiculos) {
      v.updateMatrixWorld(true);
      const cuerpo = v.children.find((o) => o.isMesh && o.name !== 'sombraContacto' && o.name !== 'sombraMain') ||
        v.children[0].children?.find((o) => o.isMesh);
      const inv = new THREE.Matrix4().copy(v.matrixWorld).invert();
      // caja del cuerpo en coords locales del vehiculo
      const bb = new THREE.Box3();
      const loc = (o) => { const b = new THREE.Box3().setFromObject(o, true); return b.applyMatrix4(inv); };
      v.traverse((o) => { if (o.isMesh && !o.name.startsWith('sombra')) bb.union(loc(o)); });
      const ruedas = (v.userData.ruedas || []).map((w) => {
        const b = loc(w);
        return { minY: +b.min.y.toFixed(4), zMin: +b.min.z.toFixed(3), zMax: +b.max.z.toFixed(3), x: +((b.min.x + b.max.x) / 2).toFixed(3), parent: w.parent === v ? 'grupo' : 'sub' };
      });
      // por material: centroides en X para comprobar orientacion (faro adelante, stop atras)
      const cen = {};
      v.traverse((o) => {
        if (!o.isMesh || !o.geometry.groups.length) return;
        const pos = o.geometry.attributes.position;
        const mats = Array.isArray(o.material) ? o.material : [o.material];
        for (const g of o.geometry.groups) {
          const n = mats[g.materialIndex].name.split('_')[0];
          let sx = 0, c = 0, minx = 1e9, maxx = -1e9;
          for (let i = g.start; i < g.start + g.count; i++) { const x = pos.getX(i); sx += x; c++; minx = Math.min(minx, x); maxx = Math.max(maxx, x); }
          cen[n] = [+(sx / c).toFixed(2), +minx.toFixed(2), +maxx.toFixed(2)];
        }
      });
      // rueda: radio y ancho maximo de la carroceria a la altura del eje
      out.push({ tipo: t, caja: [bb.min.toArray().map((a) => +a.toFixed(3)), bb.max.toArray().map((a) => +a.toFixed(3))], ruedas, cen });
    }
    return out;
  },
};
escena(qs.get('escena') || 'todos', { sombraMain: qs.get('sombraMain') === '1' });
renderer.render(scene, camera);
window.APP.listo = true;
