"""
Regenera todos los entregables de la pollería campestre:

    python3 generar.py

1. verifica la geometría (diseno.verificar),
2. exporta la escena 3D (render3d/web/escena_polleria.json),
3. dibuja las 10 láminas (PDF + vistas previas PNG),
4. exporta la planta general y las plantas del edificio a DXF,
5. calcula el presupuesto (xlsx con fórmulas),
6. compone la memoria descriptiva (PDF).
"""
from __future__ import annotations

import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import diseno  # noqa: E402
import exportar_3d  # noqa: E402
import exportar_dxf  # noqa: E402
import laminas  # noqa: E402
import memoria  # noqa: E402
import presupuesto  # noqa: E402


def main():
    problemas = diseno.verificar()
    print("verificación geométrica:", problemas or "sin problemas")
    if problemas:
        sys.exit(1)
    salida = os.path.join(AQUI, "salida")
    previas = os.path.join(salida, "vistas_previas")
    print(exportar_3d.exportar(os.path.join(AQUI, "render3d", "web", "escena_polleria.json")))
    print(laminas.generar(salida, previas))
    print(exportar_dxf.exportar(os.path.join(salida, "Polleria_Campestre_planta.dxf")))
    print(presupuesto.exportar_xlsx(os.path.join(salida, "Presupuesto_Polleria_Campestre.xlsx")))
    print(memoria.generar(os.path.join(salida, "Memoria_Descriptiva_Polleria_Campestre.pdf"), previas,
                          os.path.join(salida, "_tmp_memoria")))


if __name__ == "__main__":
    main()
