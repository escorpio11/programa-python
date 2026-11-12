# -*- coding: utf-8 -*-
"""Regenera todos los entregables del proyecto AZOTEA GYM:  python3 generar.py
(las vistas 3D, el video y el PDF de la presentación se generan con Node; ver README)."""
import diseno
import laminas
import presupuesto
import exportar_dxf
import memoria

if __name__ == "__main__":
    mal = [c for c in diseno.verificar() if not c[3]]
    print("Verificaciones: %d conformes, %d con observación" % (len(diseno.verificar()) - len(mal), len(mal)))
    for c in mal:
        print("   REVISAR:", c[0], c[1], "mín.", c[2])
    print("Escena 3D:", diseno.exportar_escena())
    print("Planos:", laminas.generar())
    print("Presupuesto:", presupuesto.generar())
    print("DXF:", exportar_dxf.generar())
    print("Memoria:", memoria.generar())
    t = presupuesto.totales()
    print("Inversión total S/ {:,} | equilibrio {} socios".format(t["total"], t["equilibrio"]))
