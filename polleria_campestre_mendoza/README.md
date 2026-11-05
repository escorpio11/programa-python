# Pollería campestre — Jr. Rodríguez de Mendoza, Mendoza (Amazonas)

Anteproyecto de una pollería campestre en el lote de 820 m² de la esquina del
Jr. Rodríguez de Mendoza con la calle lateral, conservando el **almacén de leña**
y el **garaje del propietario** existentes.

## Entregables (`salida/`)

| Archivo | Contenido |
|---|---|
| `Planos_Polleria_Campestre_Mendoza.pdf` | 10 láminas A3 (abajo) |
| `Memoria_Descriptiva_Polleria_Campestre.pdf` | Memoria descriptiva de 10 páginas: concepto, circulaciones, edificio, sombrillas, piscina, estructura, instalaciones, normativa, presupuesto y próximos pasos |
| `Presupuesto_Polleria_Campestre.xlsx` | Presupuesto referencial por etapas, con fórmulas, metrados y supuestos |
| `Polleria_Campestre_planta.dxf` | Planta general por capas (1.ª y 2.ª etapa) y plantas del edificio, en metros, para AutoCAD |
| `vistas_previas/*.png` | Imagen de cada lámina |

| Lámina | Título |
|---|---|
| A-01 | Planimetría general — 1.ª etapa (restaurante y jardines) |
| A-02 | Planimetría general — 2.ª etapa (piscina, vestidores y relajo) |
| A-03 | Circulaciones vehicular, peatonal y de servicio; rutas de evacuación |
| A-04 | Sombrillas removibles: modo restaurante / modo evento y anclaje |
| A-05 | Planta del 1.er piso (cocina, hornos polleros, parrilla, despacho) |
| A-06 | Planta del 2.º piso (bar, terraza y escenario) |
| A-07 | Cortes X-X, Y-Y y elevaciones |
| A-08 | Piscina, patera, vestidores y zona de relajo |
| E-01 | Cimentación |
| E-02 | Estructura metálica del entrepiso, arriostres y pórtico |

## El proyecto en cifras

- **Edificio central de acero, 2 pisos**: 115.5 m² cerrados abajo + 161.2 m² de losa
  arriba (volados de 2.00 m que techan los porches) → 276.7 m² techados.
- **1.er piso**: cocina de 27.5 m² con 2 hornos polleros a leña, parrilla, freidoras y
  campana de 5 m; despacho y caja; SS.HH. accesible, damas y varones; ascensor
  panorámico exterior de 2 paradas.
- **2.º piso**: bar de 27.5 m² con depósito, SS.HH. (accesible, damas, varones),
  terraza exterior de 62 m² y **escenario de 4.00 × 6.00 m** diseñado para 750 kgf/m².
- **Sombrillas**: 10 sombrillas profesionales de 3.00 × 3.00 m en camisas empotradas
  con tapa al ras: se retiran en minutos para eventos.
- **Capacidad**: 113 asientos en modo restaurante (58 en jardines, 24 en el 1.er piso,
  31 en el 2.º); en modo evento 12 mesas redondas de 8 + pista de baile, o ~300
  personas de pie solo en el césped.
- **Vehículos**: calzada de 6.00 m de doble sentido desde la calle lateral hasta el
  garaje; 5 plazas (1 accesible), 2 de motos, zona de carga y caseta de GLP.
- **2.ª etapa**: piscina de 6.00 × 3.50 m (1.20–1.50 m), patera de 2.40 × 2.40 m,
  andén de 1.50 m, vestidores con paso limpio, ducha, pediluvio, cerco de vidrio y
  zona de relajo con camillas y hamacas (D.S. 007-2003-SA).
- **Inversión referencial con IGV**: 1.ª etapa ≈ S/ 1 038 000; 2.ª etapa ≈ S/ 182 000.

## Código

| Módulo | Qué hace |
|---|---|
| `diseno.py` | Geometría de todo el lote: existentes, calzada, plazas, edificio, jardines, sombrillas, caminos, piscina; `verificar()` comprueba choques |
| `edificio.py` | Ambientes, equipos, puertas, tabiques, escaleras, mesas y techos del edificio |
| `estructura_pol.py` | Predimensionamiento LRFD (E.020, E.030, E.090), zapatas y metrado de acero |
| `laminas.py` | Dibujo de las 10 láminas (usa `../estacionamiento_rodriguez_mendoza/dibujo.py`) |
| `presupuesto.py` | Metrados y presupuesto por etapas → xlsx |
| `memoria.py` | Memoria descriptiva → PDF |
| `exportar_3d.py` | Escena JSON para el modelo three.js (`render3d/web/`) |
| `exportar_dxf.py` | Planta general y plantas del edificio → DXF |
| `generar.py` | Regenera todo: `python3 generar.py` |

## Advertencias

Es un **anteproyecto**: las medidas del lote vienen de imagen satelital, la
capacidad portante del suelo es supuesta (1.0 kg/cm²) y los precios son
referenciales. Antes de construir: levantamiento topográfico, parámetros
urbanísticos, estudio de mecánica de suelos, proyecto de especialidades firmado
y licencia de edificación (modalidad C), ITSE y autorización sanitaria de la
piscina.
