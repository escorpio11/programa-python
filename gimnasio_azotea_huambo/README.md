# AZOTEA GYM — gimnasio en la azotea (Huambo, Rodríguez de Mendoza, Amazonas)

Proyecto del gimnasio en la azotea techada de la casa: 13 máquinas de fuerza, recepción con
12 lockers, zona funcional y los dos baños con ducha ya construidos. Se conservan el lavadero, el
tanque elevado y los dos tragaluces (no se cubren).

## Entregables (`salida/`)

| Archivo | Contenido |
|---|---|
| `Presentacion_Azotea_Gym.pdf` | Presentación de 17 diapositivas para mostrar y convencer (vistas 3D, distribución, inversión, recuperación, plazo) |
| `Recorrido_Azotea_Gym.mp4` | Video de recorrido interior de 17 s (1280 × 720) |
| `vistas_3d/*.jpg` | 14 vistas 3D: aéreas, recepción, peso libre, sala, máquinas, lockers, noche y planta |
| `Planos_Azotea_Gym.pdf` | 9 láminas A3 (abajo); `vistas_previas/*.png` trae cada lámina como imagen |
| `Azotea_Gym_planta.dxf` | Planta por capas, en metros, para AutoCAD |
| `Presupuesto_Azotea_Gym.xlsx` | Presupuesto por partidas con fórmulas, resumen, recuperación de la inversión y cronograma |
| `Memoria_Descriptiva_Azotea_Gym.pdf` | Memoria descriptiva (criterios, acabados, instalaciones, cargas, seguridad, presupuesto) |
| `presentacion/` | Fuente de la presentación (diapositivas HTML, hoja de estilos e imágenes) |

| Lámina | Título |
|---|---|
| A-01 | Planta de distribución propuesta y relación de máquinas |
| A-02 | Cotas, circulación, evacuación y verificación de pasos libres |
| A-03 | Comparativo: plano base vs. propuesta |
| A-04 | Recepción, lockers y vestíbulo de servicios |
| A-05 | Cortes y alturas (máquinas frente al techo) |
| A-06 | Pisos, cerramiento y acabados |
| IE-01 | Iluminación, tomacorrientes y ventilación |
| E-01 | Cargas sobre la losa (coordinación con el ingeniero estructural) |
| V-01 | Verificación de medidas en obra |

## El proyecto en cifras

- Azotea techada de 98.0 m²; sala útil de 76.5 m²; máquinas 29.3 m² (38 %); aforo simultáneo de 16 personas.
- 13 máquinas del Catálogo 2026 Fitness Extreme: S/ 56,100. Accesorios de peso libre: S/ 10,460.
- Inversión referencial total con IGV: **S/ 121,294** (etapa de apertura S/ 115,033; mejoras S/ 6,260).
- Punto de equilibrio con los supuestos de partida: 32 socios (mensualidad supuesta de S/ 70).

## Decisiones de diseño

- **Recepción** junto a la llegada de la escalera: mostrador de 1.50 m, panel de marca
  retroiluminado y 12 lockers espalda con espalda. El muro del tragaluz E se cierra con
  policarbonato opal hasta 2.40 m: da luz natural sin tapar el tragaluz.
- **Sala este** (peso libre, tren superior, tren inferior, crossover): conserva la ubicación del
  plano de distribución, con las máquinas pesadas sobre las vigas de los ejes.
- **Sala oeste**: press plano, hip thrust y dominadas se reubican para liberar el frente de los
  baños construidos, el lavadero y el hall de recepción (pasos de 1.10 m o más).
- **Lavadero y tanque**: se mantienen; una celosía de listones los oculta desde la sala.
- **Zona funcional** de grass sintético al centro de la sala este.

## Antes de ejecutar

1. **Medir con wincha** (lámina V-01). El baño construido mide 3.70 m interiores y el plano base
   3.35 m; el plano de techo acota luces mayores (4.73 / 4.87 / 3.52 / 1.26 m). El modelo respeta
   la medida de obra del baño y desplaza 0.35 m lo que queda a su derecha (largo 14.97 m).
2. **Evaluación estructural** de losa y vigas por ingeniero civil colegiado: la Norma E.020 pide
   400 kgf/m² para gimnasios.
3. **Altura bajo la cercha del eje 2**: el crossover mide 2.30 m; confirmar 2.35 m o más.
4. Confirmar si ya existe cerramiento sobre el parapeto (se descuenta del presupuesto) y cotizar el
   flete a Huambo. Los precios que no son de catálogo son referenciales.

## Código

| Módulo | Qué hace |
|---|---|
| `diseno.py` | Geometría única (existente + propuesta), máquinas, verificación de pasos y alturas, escena 3D |
| `laminas.py` | Las 9 láminas A3 y los metrados |
| `presupuesto.py` | Partidas, totales, recuperación y cronograma → Excel |
| `memoria.py` | Memoria descriptiva → PDF |
| `exportar_dxf.py` | Planta → DXF |
| `generar.py` | Regenera planos, presupuesto, DXF y memoria: `python3 generar.py` |
| `render3d/web/` | Modelo three.js (`gym.js`, `maquinas.js`, `escena.json`) |
| `render3d/render.mjs` | Vistas 3D: `cd render3d && npm install && node render.mjs ../salida/vistas_3d 1920 1080` |
| `render3d/render_video.mjs` | Video de recorrido: `node render_video.mjs` |
| `render3d/presentacion_pdf.mjs` | PDF de la presentación: `node presentacion_pdf.mjs` |

Requiere Python 3 con `matplotlib`, `openpyxl`, `reportlab`, `ezdxf`, `pillow`, y Node con `playwright`.
