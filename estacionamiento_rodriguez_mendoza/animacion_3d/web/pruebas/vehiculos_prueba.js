// Banco de prueba de vehiculos.js con la misma iluminación que main.js.
//   ?escena=todos  -> los 7 tipos alineados (frente hacia +X)
//   ?escena=fila   -> 6 autos estacionados lado a lado a 2.50 m entre ejes de plaza
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
renderer.toneMappingExposure = 0.92;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(40, ANCHO / ALTO, 0.1, 3000);

// cielo y sol: mismos parámetros que main.js
const sky = new Sky();
sky.scale.setScalar(4000);
const su = sky.material.uniforms;
su.turbidity.value = 4.5; su.rayleigh.value = 1.6; su.mieCoefficient.value = 0.004; su.mieDirectionalG.value = 0.82;
scene.add(sky);
const norte = new THREE.Vector3(0.8181, 0, -0.5751).normalize();
const oeste = new THREE.Vector3(norte.z, 0, -norte.x);
const elevSol = THREE.MathUtils.degToRad(38);
const dirSol = oeste.clone().multiplyScalar(Math.cos(elevSol) * 0.85).add(norte.clone().multiplyScalar(Math.cos(elevSol) * 0.35));
dirSol.y = Math.sin(elevSol);
dirSol.normalize();
su.sunPosition.value.copy(dirSol);
const centro = new THREE.Vector3(0, 0, 0);
const sol = new THREE.DirectionalLight(0xfff1dc, 3.1);
sol.position.copy(centro).add(dirSol.clone().multiplyScalar(60));
sol.target.position.copy(centro);
sol.castShadow = true;
sol.shadow.mapSize.set(4096, 4096);
const sc = sol.shadow.camera;
sc.left = -18; sc.right = 18; sc.top = 18; sc.bottom = -18; sc.near = 5; sc.far = 140;
sol.shadow.bias = -0.0004;
sol.shadow.normalBias = 0.03;
sol.shadow.radius = 3;
scene.add(sol, sol.target);
scene.add(new THREE.HemisphereLight(0xcfe3ff, 0x6b5b45, 0.85));
{
  const pmrem = new THREE.PMREMGenerator(renderer);
  const skyScene = new THREE.Scene();
  const sky2 = new Sky();
  sky2.scale.setScalar(4000);
  Object.keys(su).forEach((k) => { if (sky2.material.uniforms[k]) sky2.material.uniforms[k].value = su[k].value; });
  skyScene.add(sky2);
  scene.environment = pmrem.fromScene(skyScene, 0.02).texture;
}
scene.fog = new THREE.FogExp2(0xc9d8e6, 0.0011);

// piso de concreto gris
const tex = texConcreto([128, 128, 125], 3);
tex.repeat.set(12, 12);
const piso = new THREE.Mesh(new THREE.PlaneGeometry(80, 80), new THREE.MeshStandardMaterial({ map: tex, roughness: 0.92 }));
piso.rotation.x = -Math.PI / 2;
piso.receiveShadow = true;
scene.add(piso);

const matLinea = new THREE.MeshStandardMaterial({ color: 0xf3f3ee, roughness: 0.7, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 });
let grupo = new THREE.Group();
scene.add(grupo);

const TIPOS = ['sedan', 'hatchback', 'suv', 'pickup', 'van', 'moto', 'mototaxi'];

function linea(x, z, lx, lz) {
  const m = new THREE.Mesh(new THREE.PlaneGeometry(lx, lz), matLinea);
  m.rotation.x = -Math.PI / 2;
  m.position.set(x, 0.002, z);
  m.receiveShadow = true;
  grupo.add(m);
}

function escena(nombre) {
  scene.remove(grupo);
  grupo = new THREE.Group();
  scene.add(grupo);
  const info = [];
  if (nombre === 'fila') {
    // 6 plazas de 2.50 m (ejes de plaza en z = i*2.5), autos en reversa / de frente
    const tipos = ['sedan', 'suv', 'pickup', 'hatchback', 'van', 'sedan'];
    const cols = ['#c6c9cc', '#f2f2ef', '#141516', '#7a141a', '#f2f2ef', '#1f3a6b'];
    for (let i = 0; i <= 6; i++) linea(0, (i - 3) * 2.5, 5.0, 0.12);
    linea(-2.5, 0, 0.12, 15.0);
    tipos.forEach((t, i) => {
      const v = crearVehiculo(t, { color: cols[i], seed: i + 3 });
      const z = (i - 2.5) * 2.5;
      const L = DIMENSIONES[t].largo;
      v.position.set(-2.5 + 0.35 + L / 2, 0, z);
      grupo.add(v);
      info.push({ v, t });
    });
  } else if (nombre === 'variantes') {
    // semillas 1..4 de pickup, suv, sedan y van (llantas, barra antivuelco, rieles, franja)
    ['pickup', 'suv', 'sedan', 'van'].forEach((t, j) => {
      for (let k = 0; k < 4; k++) {
        const v = crearVehiculo(t, { color: COLORES_AUTOS[(k * 3 + j) % COLORES_AUTOS.length], seed: k + 1 });
        v.position.set((k - 1.5) * 6.2, 0, (j - 1.5) * 3.2);
        grupo.add(v);
        info.push({ v, t });
      }
    });
  } else if (nombre === 'perfil') {
    // todos los tipos en fila a lo largo de X (vista lateral desde -Z)
    let x = -16;
    TIPOS.forEach((t, i) => {
      const L = DIMENSIONES[t].largo;
      const color = t === 'moto' ? '#b3261e' : t === 'mototaxi' ? '#1d4f91' : COLORES_AUTOS[[1, 6, 2, 4, 0][i]];
      const v = crearVehiculo(t, { color, seed: i + 1 });
      v.position.set(x + L / 2, 0, 0);
      x += L + 0.9;
      grupo.add(v);
      info.push({ v, t });
    });
  } else {
    TIPOS.forEach((t, i) => {
      const color = t === 'moto' ? '#b3261e' : t === 'mototaxi' ? '#1d4f91' : COLORES_AUTOS[[1, 0, 2, 4, 0, 0, 0][i] ?? i];
      const v = crearVehiculo(t, { color, seed: i + 1 });
      v.position.set(0, 0, (i - 3) * 3.0);
      grupo.add(v);
      info.push({ v, t });
    });
  }
  grupo.updateMatrixWorld(true);
  window.APP.vehiculos = info;
}

function triangulos(obj) {
  let n = 0;
  obj.traverse((o) => {
    if (o.isMesh) {
      const g = o.geometry;
      n += (g.index ? g.index.count : g.attributes.position.count) / 3;
    }
  });
  return n;
}

window.APP = {
  scene, camera, renderer, escena,
  vista(pos, obj, fov = 40) {
    camera.fov = fov;
    camera.aspect = ANCHO / ALTO;
    camera.position.set(...pos);
    camera.lookAt(new THREE.Vector3(...obj));
    camera.updateProjectionMatrix();
    renderer.render(scene, camera);
  },
  info() {
    const r = [];
    for (const { v, t } of window.APP.vehiculos) {
      const b = new THREE.Box3();
      v.updateMatrixWorld(true);
      v.traverse((o) => { if (o.isMesh && o.name !== 'sombraContacto') b.union(new THREE.Box3().setFromObject(o, true)); });
      const s = b.getSize(new THREE.Vector3());
      const c = b.getCenter(new THREE.Vector3()).sub(v.position);
      const mats = new Set();
      v.traverse((o) => { if (o.isMesh) (Array.isArray(o.material) ? o.material : [o.material]).forEach((m) => mats.add(m.name)); });
      // apoyo de ruedas: y mínima de cada rueda en coordenadas de mundo
      const apoyo = (v.userData.ruedas || []).map((w) => +new THREE.Box3().setFromObject(w, true).min.y.toFixed(4));
      const porMat = {};
      v.traverse((o) => {
        if (!o.isMesh) return;
        const mats = Array.isArray(o.material) ? o.material : [o.material];
        const gs = o.geometry.groups.length ? o.geometry.groups : [{ start: 0, count: o.geometry.attributes.position.count, materialIndex: 0 }];
        for (const g of gs) { const n = mats[g.materialIndex].name.split('_')[0]; porMat[n] = (porMat[n] || 0) + g.count / 3; }
      });
      r.push({ tipo: t, tris: triangulos(v), porMat, largo: +s.x.toFixed(3), ancho: +s.z.toFixed(3), alto: +s.y.toFixed(3),
        ref: DIMENSIONES[t], minY: +b.min.y.toFixed(3), centroX: +c.x.toFixed(3), centroZ: +c.z.toFixed(3),
        ruedas: (v.userData.ruedas || []).length, apoyo, materiales: mats.size, drawGroups: v.children[0]?.geometry?.groups?.length });
    }
    return r;
  },
};
escena(qs.get('escena') || 'todos');
renderer.render(scene, camera);
window.APP.listo = true;
