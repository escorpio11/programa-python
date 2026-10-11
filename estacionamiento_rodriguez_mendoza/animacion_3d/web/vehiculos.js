// PROVISIONAL: reemplazado por el módulo definitivo de vehículos.
// Interfaz: crearVehiculo(tipo, {color, seed}) -> THREE.Group, frente hacia +X,
// centrado en la huella, suelo en y = 0. Metros.
import * as THREE from 'three';

export const DIMENSIONES = {
  sedan: { largo: 4.50, ancho: 1.75, alto: 1.45 },
  hatchback: { largo: 4.00, ancho: 1.70, alto: 1.50 },
  suv: { largo: 4.70, ancho: 1.85, alto: 1.75 },
  pickup: { largo: 5.30, ancho: 1.85, alto: 1.82 },
  van: { largo: 5.30, ancho: 1.90, alto: 2.30 },
  moto: { largo: 2.00, ancho: 0.75, alto: 1.10 },
  mototaxi: { largo: 2.80, ancho: 1.35, alto: 1.75 },
};

export const COLORES_AUTOS = ['#f2f2f0', '#c9ccd0', '#2b2d30', '#8e1b1b', '#1d3c6e', '#6f7378', '#e9e4d8', '#2f5d3a'];

export function crearVehiculo(tipo, { color = '#cccccc' } = {}) {
  const d = DIMENSIONES[tipo] || DIMENSIONES.sedan;
  const g = new THREE.Group();
  const m = new THREE.Mesh(new THREE.BoxGeometry(d.largo, d.alto * 0.6, d.ancho),
    new THREE.MeshStandardMaterial({ color, roughness: 0.3, metalness: 0.5 }));
  m.position.y = d.alto * 0.3 + 0.2;
  m.castShadow = true;
  g.add(m);
  const c = new THREE.Mesh(new THREE.BoxGeometry(d.largo * 0.5, d.alto * 0.35, d.ancho * 0.9),
    new THREE.MeshStandardMaterial({ color: 0x223344, roughness: 0.1 }));
  c.position.y = d.alto * 0.8;
  c.castShadow = true;
  g.add(c);
  g.userData.ruedas = [];
  return g;
}
