# AZOTEA GYM — gimnasio en la azotea (Huambo, Rodríguez de Mendoza, Amazonas)

Proyecto del gimnasio en la azotea de la casa, sobre la base de:

| Fuente | Qué aporta |
|---|---|
| Plano de distribución de máquinas «AZOTEA GYM» (ago-2026) | Base general 14.62 × 6.65 m, vigas, ubicación de las 13 máquinas |
| A-01 modif. «SS.HH. y zona de servicio — MEDIDAS DE OBRA» (nov-2026) | Baños construidos, tanque elevado TQ-1, lavadero, tragaluces E y SO |
| Techo metálico Casa de Huambo (jul-2024) | Cerchas en ejes 7-5-3-1, alturas 2.80 → 2.40 m, calamina translúcida sobre tragaluces |
| Catálogo 2026 Fitness Extreme | Dimensiones y precios de las máquinas |

## Estado (trabajo en curso)

Hecho:
- `diseno.py`: geometría única del proyecto (existente + propuesta), máquinas con precio y
  dimensiones de catálogo, verificación de pasos libres y alturas, exportación de la escena 3D.
  `python3 diseno.py` imprime las verificaciones (todas conformes).
- `render3d/web/maquinas.js`: modelos 3D paramétricos de las 13 máquinas, porta discos y figuras.
- `render3d/web/gym.js`: escena completa (azotea, baños, tragaluces, tanque, lavadero, recepción,
  lockers, cerramiento, techo metálico, iluminación día/noche, entorno).
- `render3d/render.mjs`: 13 vistas con Chromium headless
  (`cd render3d && npm install && node render.mjs ../salida/vistas_3d 1920 1080`).

Pendiente:
- Afinar materiales y luces de las vistas 3D (pisos y muros más claros, vistas aéreas sin el
  cerramiento del lado cercano) y generar las vistas finales + video de recorrido.
- Láminas A3 en PDF (distribución, cotas, circulación y seguridad, cortes, recepción, eléctricas,
  pisos, cargas sobre losa, verificación de medidas) y exportación DXF.
- Presupuesto en Excel, memoria descriptiva, cronograma.
- Presentación visual para convencer (página interactiva con recorrido 3D + PDF para compartir).

## Decisiones de diseño tomadas

- **Recepción** junto a la llegada de la escalera (mostrador de 1.50 m perpendicular al muro, panel de
  marca retroiluminado y 12 lockers espalda con espalda). El muro del tragaluz E se cierra con
  policarbonato opal hasta 2.40 m: da luz natural a la recepción sin tapar el tragaluz.
- **Sala este** (peso libre, tren superior, tren inferior, crossover): se respeta la ubicación del
  plano de distribución, con las máquinas pesadas sobre los ejes de vigas.
- **Sala oeste**: press plano, hip thrust y dominadas se reubican para liberar el frente de los
  baños construidos, el lavadero y el hall de recepción (pasos ≥ 1.10 m).
- **Lavadero y tanque**: se mantienen; celosía de listones los oculta desde la sala.
- **Zona funcional** de grass sintético al centro de la sala este.

## Advertencia sobre medidas

El baño construido mide 3.70 m interiores (medida de obra) frente a 3.35 m del plano base, y el
plano de techo acota luces mayores que las del plano base (4.73 / 4.87 / 3.52 / 1.26 m). El modelo
respeta la medida de obra del baño y desplaza 0.35 m lo que queda a su derecha (largo 14.97 m).
**Verificar con wincha antes del replanteo**; `diseno.py` es paramétrico y se regenera.
