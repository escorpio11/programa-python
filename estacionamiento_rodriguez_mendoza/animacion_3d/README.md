# Recorrido 3D del estacionamiento techado

Animación 3D (video MP4 1920×1080) y visor interactivo del anteproyecto, construidos con
[three.js](https://threejs.org) a partir de la misma geometría de los planos (`../geometria.py`,
`../estructura.py`). Las medidas, columnas, vigas, correas, techos, plazas y portones del modelo
salen de `escena.json`, que se genera desde Python; no hay nada modelado "a ojo" en el proyecto.

## Contenido

| Ruta | Qué es |
|---|---|
| `web/escena.json` | Geometría exportada por `../exportar_escena.py` (x = u, y = altura, z = −v; metros) |
| `web/estructura3d.js` | Modelo del proyecto: piso, señalización, cerco, portones, coberturas metálicas, garita |
| `web/vehiculos.js` | Autos, camionetas, combis, motos y mototaxis (low-poly, a escala) |
| `web/entorno.js` | Calles, veredas, casas vecinas, vegetación, postes y cerros del valle |
| `web/guion.js` | Guion de cámara (8 tomas), rótulos y programación de vehículos en movimiento |
| `web/main.js` | Escena, luz de tarde, cielo, sombras; modos `video`, `still` y `visor` |
| `render_video.mjs` | Render cuadro a cuadro con Chromium headless + codificación H.264 (ffmpeg) |
| `render_vistas.mjs` | Vistas de control (PNG) |
| `visor/visor.html` | Página del visor interactivo (usa three.js desde jsDelivr) |

## Cómo regenerar el video

```bash
cd estacionamiento_rodriguez_mendoza
python3 exportar_escena.py animacion_3d/web/escena.json
cd animacion_3d
npm install                                   # three 0.160.0 y playwright-core
mkdir -p web/lib && cp node_modules/three/build/three.module.js web/lib/ \
  && cp -r node_modules/three/examples/jsm web/lib/addons
node render_video.mjs recorrido_estacionamiento.mp4   # ~84 s a 30 fps
```

Requiere Chromium (variable `CHROME` con la ruta del ejecutable) y `ffmpeg`. El render usa WebGL por
software, por lo que funciona sin tarjeta de video; tarda del orden de 1 s por cuadro.

## Visor interactivo

`node -e "import('./servidor.mjs').then(m => m.servir(8765))"` y abrir
`http://localhost:8765/index.html` (modo visor por defecto): girar, acercar, ver el recorrido guiado.
