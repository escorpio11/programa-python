# Estacionamiento techado – Jr. Rodríguez de Mendoza (Amazonas)

Anteproyecto de un estacionamiento vehicular techado, con estructura metálica ligera y
análisis de rentabilidad. Todo se genera con Python a partir de las 4 medidas del terreno
tomadas en Google Maps (frente 30 m, lado colindante 40 m, fondo 30 m, frente a calle lateral 20 m).

## Entregables (`salida/`)

| Archivo | Contenido |
|---|---|
| `Planos_Estacionamiento_Rodriguez_de_Mendoza.pdf` | 7 láminas A3: L-01 perimétrico, A-01 distribución, A-02 techos y cortes, E-01 cimentación, E-02 estructura de techo, E-03 pórtico y placa base, E-04 detalles de zapata y conexiones |
| `Estacionamiento_planta.dxf` | Planta para AutoCAD (metros, capas de arquitectura y estructura) |
| `Modelo_Rentabilidad_Estacionamiento.xlsx` | Supuestos editables (celdas amarillas), presupuesto, escenarios, flujo a 20 años, sensibilidad |
| `Memoria_y_Rentabilidad.pdf` | Memoria descriptiva, tipo de vehículos, estructura, presupuesto y rentabilidad |
| `vistas_previas/*.png` | Imagen de cada lámina |

## Resultados principales

- Terreno ≈ **820 m²** (ángulos reconstruidos: A 130°, B 60°, C 80°, D 90°).
- **28 plazas techadas** (26 de 2.50 × 5.00 m + 2 accesibles de 3.80 × 5.00 m), 5 motos y 2 mototaxis.
- Circulación en L de **sentido único**: ingreso por la calle lateral (P-1), salida a Jr. Rodríguez de Mendoza (P-2); pasillos de 6.50 m.
- Estructura en **voladizo (T desbalanceada)**: 1 columna cada 3 plazas, **13 columnas** en total, ninguna en pasillos;
  ≈ 6.8 t de acero (16.5 kg/m² de techo), gálibo libre 2.80 m.
- Inversión estimada **≈ S/ 330 mil** (piso de afirmado) o ≈ S/ 406 mil (losa de concreto).
- Rentabilidad (escenario base, 18 abonados a S/ 120 + rotación): TIR ≈ 11 % y recuperación ≈ 9 años si lo opera el
  propietario; TIR ≈ 4 % si se contrata un guardián. Se recomienda validar demanda y construir por etapas.

## Cómo regenerar

```bash
pip install matplotlib shapely ezdxf openpyxl reportlab
python3 generar_todo.py
```

Los parámetros están en `geometria.py` (medidas, ancho de plazas y pasillos, portones),
`estructura.py` (cargas, perfiles, niveles) y `rentabilidad.py` (precios, tarifas, escenarios).

## Limitaciones

Es un **anteproyecto**: la geometría viene de Google Maps (±0.5–1 m) y debe confirmarse con levantamiento
topográfico (diagonales A-C ≈ 36.11 m y B-D ≈ 45.51 m). El cálculo estructural es un predimensionamiento
(RNE E.020/E.030/E.090/E.060) que debe revisar y firmar un ingeniero civil colegiado, con estudio de mecánica de
suelos. Precios, tarifas y demanda son estimaciones a validar con cotizaciones y un sondeo local.
