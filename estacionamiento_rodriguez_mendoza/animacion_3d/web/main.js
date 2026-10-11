// Escena principal: luces, cielo, proyecto, entorno, vehículos y guion de cámara.
// Modos (?modo=): 'video' (render cuadro a cuadro), 'still' (vistas de control), 'visor' (interactivo).
import * as THREE from 'three';
import { Sky } from 'three/addons/objects/Sky.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { crearProyecto } from './estructura3d.js';
import { crearEntorno } from './entorno.js';
import { crearVehiculo, COLORES_AUTOS, DIMENSIONES } from './vehiculos.js';
import { crearGuion } from './guion.js';
import { rng } from './texturas.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { GTAOPass } from 'three/addons/postprocessing/GTAOPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';

const qs = new URLSearchParams(location.search);
const MODO = qs.get('modo') || 'visor';
const ANCHO = +qs.get('w') || window.innerWidth;
const ALTO = +qs.get('h') || window.innerHeight;
const CALIDAD = qs.get('calidad') || 'alta';

const datos = await (await fetch('./escena.json')).json();

// ---------------------------------------------------------------- renderer
const canvas = document.getElementById('lienzo');
const AA = (qs.get('aa') ?? '1') === '1';
const renderer = new THREE.WebGLRenderer({ canvas, antialias: AA, preserveDrawingBuffer: MODO !== 'visor' });
renderer.setPixelRatio(MODO === 'visor' ? Math.min(window.devicePixelRatio, 2) : 1);
renderer.setSize(ANCHO, ALTO, false);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 0.86;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = qs.get('pcf') === '1' ? THREE.PCFShadowMap : THREE.PCFSoftShadowMap;

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(40, ANCHO / ALTO, 0.3, 2500);

// ---------------------------------------------------------------- cielo y sol
const sky = new Sky();
sky.scale.setScalar(4000);
const su = sky.material.uniforms;
su.turbidity.value = 4.5;
su.rayleigh.value = 1.6;
su.mieCoefficient.value = 0.004;
su.mieDirectionalG.value = 0.82;
scene.add(sky);

// Norte del proyecto: vector (x, z) en escena.json. Sol de media tarde desde el oeste-noroeste.
const norte = new THREE.Vector3(datos.meta.norte[0], 0, datos.meta.norte[1]).normalize();
const oeste = new THREE.Vector3(norte.z, 0, -norte.x);         // 90° a la izquierda del norte (visto en planta)
const centroLote = (() => {
  const v = datos.lote; let x = 0, z = 0;
  v.forEach((p) => { x += p[0]; z += p[1]; });
  return new THREE.Vector3(x / v.length, 0, z / v.length);
})();

const elevSol = THREE.MathUtils.degToRad(38);
const dirSol = oeste.clone().multiplyScalar(Math.cos(elevSol) * 0.85).add(norte.clone().multiplyScalar(Math.cos(elevSol) * 0.35));
dirSol.y = Math.sin(elevSol);
dirSol.normalize();
su.sunPosition.value.copy(dirSol);

const sol = new THREE.DirectionalLight(0xffeccc, 2.7);
sol.position.copy(centroLote).add(dirSol.clone().multiplyScalar(120));
sol.target.position.copy(centroLote);
sol.castShadow = true;
const TS = +(qs.get('sombra') || (MODO === 'visor' ? 2048 : (CALIDAD === 'alta' ? 4096 : 2048)));
sol.shadow.mapSize.set(TS, TS);
const sc = sol.shadow.camera;
sc.left = -55; sc.right = 55; sc.top = 55; sc.bottom = -55; sc.near = 20; sc.far = 260;
sol.shadow.bias = -0.0004;
sol.shadow.normalBias = 0.03;
sol.shadow.radius = 3;
scene.add(sol, sol.target);
const hemi = new THREE.HemisphereLight(0xcfe3ff, 0x5d5444, 0.42);
scene.add(hemi);

// Mapa de entorno a partir del cielo (reflejos en autos y metal)
{
  const pmrem = new THREE.PMREMGenerator(renderer);
  const skyScene = new THREE.Scene();
  const sky2 = new Sky();
  sky2.scale.setScalar(4000);
  Object.keys(su).forEach((k) => { if (sky2.material.uniforms[k]) sky2.material.uniforms[k].value = su[k].value; });
  skyScene.add(sky2);
  // suelo oscuro en el mapa de entorno: evita que la mitad inferior del cielo ilumine de abajo hacia arriba
  const sueloEnv = new THREE.Mesh(new THREE.CircleGeometry(3000, 32), new THREE.MeshBasicMaterial({ color: 0x8a877d }));
  sueloEnv.rotation.x = -Math.PI / 2; sueloEnv.position.y = -2;
  skyScene.add(sueloEnv);
  scene.environment = pmrem.fromScene(skyScene, 0.02).texture;
  scene.environmentIntensity = 0.38;
}
scene.fog = new THREE.FogExp2(0xc4d3e2, 0.0009);

// ---------------------------------------------------------------- contenido
const proyecto = crearProyecto(datos);
scene.add(proyecto);
const entorno = crearEntorno(scene, datos, { renderer, camera });

// Sombra de contacto suave bajo cada vehículo (oclusión ambiental aproximada)
const texSombra = (() => {
  const c = document.createElement('canvas'); c.width = c.height = 128;
  const x = c.getContext('2d');
  const g = x.createRadialGradient(64, 64, 8, 64, 64, 64);
  g.addColorStop(0, 'rgba(0,0,0,0.30)'); g.addColorStop(0.55, 'rgba(0,0,0,0.18)'); g.addColorStop(1, 'rgba(0,0,0,0)');
  x.fillStyle = g; x.fillRect(0, 0, 128, 128);
  const t = new THREE.CanvasTexture(c); return t;
})();
const matSombra = new THREE.MeshBasicMaterial({ map: texSombra, transparent: true, depthWrite: false, polygonOffset: true,
  polygonOffsetFactor: -6, polygonOffsetUnits: -6 });
function conSombra(v, tipo) {
  const d = DIMENSIONES[tipo] || DIMENSIONES.sedan;
  const s = new THREE.Mesh(new THREE.PlaneGeometry(d.largo * 1.18, d.ancho * 1.35), matSombra);
  s.rotation.x = -Math.PI / 2;
  s.position.y = 0.015;
  s.renderOrder = 1;
  v.add(s);
  return v;
}

// Vehículos estacionados (determinista)
const azar = rng(20261011);
const VACIAS = new Set(['04', '09', '13', '17', '22', '27']);
const mezcla = ['sedan', 'pickup', 'suv', 'sedan', 'hatchback', 'pickup', 'van', 'sedan', 'suv', 'pickup'];
const estacionados = new THREE.Group();
datos.plazas.forEach((p, i) => {
  if (VACIAS.has(p.codigo)) return;
  let tipo = mezcla[i % mezcla.length];
  if (p.tipo === 'accesible') tipo = 'suv';
  const dim = DIMENSIONES[tipo];
  const color = COLORES_AUTOS[Math.floor(azar() * COLORES_AUTOS.length)];
  const v = conSombra(crearVehiculo(tipo, { color, seed: i + 1 }), tipo);
  const [fx, fz] = p.frente;
  const enReversa = azar() < 0.55;
  const dist = 1.10 - 0.95 + (enReversa ? 1.05 : 0.90) + dim.largo / 2 - 0.15;
  v.position.set(p.fondo[0] + fx * dist, 0, p.fondo[1] + fz * dist);
  const hx = enReversa ? fx : -fx, hz = enReversa ? fz : -fz;
  v.rotation.y = Math.atan2(-hz, hx) + (azar() - 0.5) * 0.04;
  v.position.x += -fz * (azar() - 0.5) * 0.12;
  v.position.z += fx * (azar() - 0.5) * 0.12;
  estacionados.add(v);
});
for (const [i, m] of datos.motos.entries()) {
  const color = m.tipo === 'mototaxi' ? (i % 2 ? '#1d4f91' : '#b3261e') : ['#1b1b1b', '#b3261e', '#1d4f91', '#e0e0e0', '#2e6b30'][i % 5];
  const v = conSombra(crearVehiculo(m.tipo, { color, seed: 100 + i }), m.tipo);
  v.position.set(m.centro[0], 0, m.centro[1]);
  v.rotation.y = Math.atan2(-m.dir[1], m.dir[0]);
  estacionados.add(v);
}
scene.add(estacionados);

// Vehículos en movimiento a lo largo del recorrido (P-1 -> P-2)
const curva = new THREE.CatmullRomCurve3(datos.recorrido.map(([x, z]) => new THREE.Vector3(x, 0, z)), false, 'centripetal', 0.5);
const largoCurva = curva.getLength();
const overlay = document.getElementById('overlay');
const guion = crearGuion({ datos, camera, overlay, modo: MODO, THREE, centroLote, curva, largoCurva });
const moviles = guion.programa.map((pr, i) => {
  const v = conSombra(crearVehiculo(pr.tipo, { color: pr.color, seed: 500 + i }), pr.tipo);
  v.visible = false;
  scene.add(v);
  return { v, pr };
});

function moverVehiculos(t) {
  for (const { v, pr } of moviles) {
    const s = guion.sDe(pr, t);
    if (s < 0 || s > largoCurva) { v.visible = false; continue; }
    const u = s / largoCurva;
    const p = curva.getPointAt(u);
    const tg = curva.getTangentAt(u);
    v.visible = true;
    v.position.copy(p);
    v.rotation.y = Math.atan2(-tg.z, tg.x);
    for (const r of v.userData.ruedas || []) r.rotation.z = -s / 0.33;
  }
}

// ---------------------------------------------------------------- render

// Post-proceso opcional: oclusión ambiental (GTAO) + salida con tone mapping
const AO = (qs.get('ao') ?? (MODO === 'video' ? '1' : '0')) === '1';
let composer = null;
if (AO) {
  const rt = new THREE.WebGLRenderTarget(ANCHO, ALTO, { samples: AA ? 4 : 0, type: THREE.HalfFloatType });
  composer = new EffectComposer(renderer, rt);
  composer.setPixelRatio(1);
  composer.setSize(ANCHO, ALTO);
  composer.addPass(new RenderPass(scene, camera));
  const gtao = new GTAOPass(scene, camera, ANCHO, ALTO);
  gtao.output = GTAOPass.OUTPUT.Default;
  gtao.blendIntensity = 0.85;
  gtao.updateGtaoMaterial({ radius: 0.9, distanceExponent: 1.5, thickness: 1.2, scale: 1.0, samples: 16 });
  gtao.updatePdMaterial({ lumaPhi: 10, depthPhi: 2, normalPhi: 3, radius: 6, rings: 2, samples: 16 });
  composer.addPass(gtao);
  composer.addPass(new OutputPass());
}
const dibujar = () => (composer ? composer.render() : renderer.render(scene, camera));

function renderEn(t) {
  moverVehiculos(t);
  entorno.actualizar && entorno.actualizar(t);
  guion.aplicar(t);
  dibujar();
}

function vista(pos, objetivo, fov = 40, t = 20) {
  moverVehiculos(t);
  camera.fov = fov;
  camera.position.set(...pos);
  camera.lookAt(new THREE.Vector3(...objetivo));
  camera.updateProjectionMatrix();
  overlay.style.display = 'none';
  dibujar();
}

window.APP = {
  datos, scene, camera, renderer, renderEn, vista, duracion: guion.duracion, centroLote: centroLote.toArray(),
  info: () => ({ tris: renderer.info.render.triangles, calls: renderer.info.render.calls }),
};

if (MODO === 'visor') {
  const controls = new OrbitControls(camera, canvas);
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;
  controls.target.copy(centroLote);
  controls.maxPolarAngle = Math.PI * 0.495;
  controls.minDistance = 3;
  controls.maxDistance = 240;
  const C = centroLote;
  const acc = Object.fromEntries(datos.accesos.map((a) => [a.codigo, a]));
  const P1 = new THREE.Vector3(acc['P-1'].centro[0], 0, acc['P-1'].centro[1]);
  const in1 = new THREE.Vector3(acc['P-1'].hacia_adentro[0], 0, acc['P-1'].hacia_adentro[1]);
  const colT1 = datos.coberturas.find((c) => c.nombre === 'T-1').columnas.map((p) => new THREE.Vector3(p[0], 0, p[2]));
  const colT2 = datos.coberturas.find((c) => c.nombre === 'T-2').columnas.map((p) => new THREE.Vector3(p[0], 0, p[2]));
  const A = new THREE.Vector3(datos.vertices.A[0], 0, datos.vertices.A[1]);
  const VISTAS = {
    aerea: [C.clone().add(new THREE.Vector3(-52, 44, 46)), C.clone(), 40],
    planta: [C.clone().add(new THREE.Vector3(0.5, 78, 6)), C.clone(), 38],
    esquina: [A.clone().add(new THREE.Vector3(-14, 7.5, -20)), C.clone().setY(1.5), 46],
    ingreso: [P1.clone().sub(in1.clone().multiplyScalar(11)).setY(2.2), P1.clone().add(in1.clone().multiplyScalar(6)).setY(1.2), 52],
    pasillo: [colT1[0].clone().add(new THREE.Vector3(-8.2, 2.1, 1.0)), colT1[2].clone().add(new THREE.Vector3(-3, 2.0, 0)), 56],
    estructura: [colT2[2].clone().add(new THREE.Vector3(3.6, 1.8, -6.8)), colT2[2].clone().add(new THREE.Vector3(-1.6, 3.0, -1.2)), 56],
  };
  const vAereo = VISTAS.aerea;
  camera.position.copy(vAereo[0]); camera.fov = vAereo[2]; camera.updateProjectionMatrix();
  controls.update();
  let anim = null;
  window.APP.irA = (nombre) => {
    const v = VISTAS[nombre]; if (!v) return;
    window.APP.detenerTour && window.APP.detenerTour();
    anim = { t: 0, p0: camera.position.clone(), o0: controls.target.clone(), f0: camera.fov, p1: v[0], o1: v[1], f1: v[2] };
  };
  window.APP.vistas = Object.keys(VISTAS);
  window.APP.techos = (on) => scene.traverse((o) => { if (o.name === 'tr4') o.visible = on; });
  window.APP.autos = (on) => { estacionados.visible = on; moviles.forEach((m) => { m.v.userData.oculto = !on; }); };
  let enTour = false, t0 = 0;
  const reloj = new THREE.Clock();
  window.APP.iniciarTour = () => { enTour = true; t0 = reloj.getElapsedTime(); controls.enabled = false; overlay.style.display = ''; };
  window.APP.detenerTour = () => {
    if (!enTour) return;
    enTour = false; overlay.style.display = 'none'; controls.enabled = true;
    controls.target.copy(C); window.APP.onFinTour && window.APP.onFinTour();
  };
  window.APP.enTour = () => enTour;
  overlay.style.display = 'none';
  const ajustar = () => {
    const w = canvas.clientWidth, h = canvas.clientHeight;
    camera.aspect = w / h; camera.updateProjectionMatrix();
    renderer.setSize(w, h, false);
  };
  window.addEventListener('resize', ajustar);
  ajustar();
  renderer.setAnimationLoop(() => {
    const dt = Math.min(reloj.getDelta(), 0.1);
    const te = reloj.elapsedTime;
    if (enTour) {
      const t = te - t0;
      if (t > guion.duracion) { window.APP.detenerTour(); return; }
      renderEn(t);
      moviles.forEach((m) => { if (m.v.userData.oculto) m.v.visible = false; });
      return;
    }
    if (anim) {
      anim.t = Math.min(1, anim.t + dt / 1.6);
      const k = anim.t * anim.t * (3 - 2 * anim.t);
      camera.position.lerpVectors(anim.p0, anim.p1, k);
      controls.target.lerpVectors(anim.o0, anim.o1, k);
      camera.fov = anim.f0 + (anim.f1 - anim.f0) * k; camera.updateProjectionMatrix();
      if (anim.t >= 1) anim = null;
    }
    moverVehiculos((te % 80) + 4);
    moviles.forEach((m) => { if (m.v.userData.oculto) m.v.visible = false; });
    controls.update();
    renderer.render(scene, camera);
  });
}
window.APP.listo = true;
