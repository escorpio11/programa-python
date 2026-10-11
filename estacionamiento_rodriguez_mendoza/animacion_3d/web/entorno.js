// PROVISIONAL: reemplazado por el módulo definitivo del entorno urbano.
// Interfaz: crearEntorno(scene, datos) -> { grupo: THREE.Group, actualizar(t) }
import * as THREE from 'three';
import { superficie } from './estructura3d.js';

export function crearEntorno(scene, datos) {
  const grupo = new THREE.Group();
  const suelo = new THREE.Mesh(new THREE.PlaneGeometry(600, 600), new THREE.MeshStandardMaterial({ color: 0x6d8a45, roughness: 1 }));
  suelo.rotation.x = -Math.PI / 2;
  suelo.position.y = -0.02;
  suelo.receiveShadow = true;
  grupo.add(suelo);
  for (const c of datos.contexto.calzadas) {
    const m = new THREE.Mesh(superficie(c, -0.01), new THREE.MeshStandardMaterial({ color: 0x555555, roughness: 0.9 }));
    m.receiveShadow = true; grupo.add(m);
  }
  for (const c of datos.contexto.veredas) {
    const m = new THREE.Mesh(superficie(c, 0.0), new THREE.MeshStandardMaterial({ color: 0xaaaaaa, roughness: 0.9 }));
    m.receiveShadow = true; grupo.add(m);
  }
  scene.add(grupo);
  return { grupo, actualizar() {} };
}
