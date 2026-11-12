"""
Genera todos los entregables del anteproyecto en la carpeta `salida/`:

    Planos_Estacionamiento_Rodriguez_de_Mendoza.pdf   (7 láminas A3)
    Estacionamiento_planta.dxf                         (AutoCAD, metros)
    Modelo_Rentabilidad_Estacionamiento.xlsx           (fórmulas editables)
    Memoria_y_Rentabilidad.pdf                         (memoria + análisis)
    Alternativas_Uso_Terreno.pdf                       (qué hacer con el terreno: 12 alternativas)
    Modelo_Alternativas_Uso_Terreno.xlsx               (fórmulas editables de las alternativas)
    vistas_previas/*.png                               (imagen de cada lámina)

Uso:  python3 generar_todo.py
"""
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import alternativas
import estructura
import exportar_dxf
import geometria
import informe
import informe_alternativas
import planos
import rentabilidad
import dibujo


def main():
    salida = os.path.join(AQUI, "salida")
    vistas = os.path.join(salida, "vistas_previas")
    graf = os.path.join(salida, "graficos")
    os.makedirs(vistas, exist_ok=True)

    errores = geometria.verificar()
    if errores:
        raise SystemExit("Distribución inválida: " + "; ".join(errores))
    for nombre, ok in (("viga", estructura.VIGA["ok"]), ("columna", estructura.COLUMNA_SEL["ok"]),
                       ("placa", estructura.PLACA["ok"]), ("zapata", estructura.ZAPATA["ok"])):
        if not ok:
            raise SystemExit(f"La verificación de {nombre} no cumple")

    _guardar = dibujo.Hoja.guardar
    dibujo.Hoja.guardar = lambda self, pdf=None, png=None, dpi=150: _guardar(self, pdf, png, dpi)
    print(planos.generar(salida, vistas))
    print(exportar_dxf.exportar(os.path.join(salida, "Estacionamiento_planta.dxf")))
    print(rentabilidad.exportar_xlsx(os.path.join(salida, "Modelo_Rentabilidad_Estacionamiento.xlsx")))
    print(informe.generar(os.path.join(salida, "Memoria_y_Rentabilidad.pdf"), vistas, graf))
    alternativas.exportar_xlsx(os.path.join(salida, "Modelo_Alternativas_Uso_Terreno.xlsx"))
    print(informe_alternativas.generar(os.path.join(salida, "Alternativas_Uso_Terreno.pdf"), graf))

    r = geometria.resumen()
    print(f"\nPlazas techadas: {r['plazas_total']} ({r['plazas_accesibles']} accesibles) | motos {r['motos']} | "
          f"mototaxis {r['mototaxis']} | columnas {r['columnas']} | área techada {r['area_techada']:.0f} m²")
    print(f"Acero: {estructura.ACERO_TOTAL_KG:,.0f} kg | Inversión: S/ {rentabilidad.capex()[-1]:,.0f}")


if __name__ == "__main__":
    main()
