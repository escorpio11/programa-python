"""
Exporta la planta general de la pollería (ambas etapas, en capas) y las plantas del
edificio a DXF (AutoCAD R2010), en metros.

- Planta general: coordenadas (u, v) del terreno, origen en el vértice B.
- Plantas del edificio (1.er y 2.º piso): en el sistema local del edificio
  (x = -d, y = -s), desplazadas a la derecha del terreno para no superponerse.
"""
from __future__ import annotations

import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import ezdxf  # noqa: E402
import numpy as np  # noqa: E402
from ezdxf.enums import TextEntityAlignment  # noqa: E402
from shapely import affinity  # noqa: E402
from shapely.geometry import LineString, Point  # noqa: E402

import diseno as dz  # noqa: E402
import edificio as ed  # noqa: E402
import laminas as lm  # noqa: E402

CAPAS = {
    "A-LIMITE": (7, "CONTINUOUS"), "A-CERCO": (8, "CONTINUOUS"), "A-VANOS": (3, "CONTINUOUS"),
    "A-EXISTENTE": (9, "CONTINUOUS"), "A-CALZADA": (8, "CONTINUOUS"), "A-PLAZAS": (7, "CONTINUOUS"),
    "A-CAMINOS": (33, "CONTINUOUS"), "A-JARDIN": (3, "CONTINUOUS"), "A-SETO": (82, "CONTINUOUS"),
    "A-EDIFICIO": (7, "CONTINUOUS"), "A-AMBIENTES": (8, "CONTINUOUS"), "A-LOSA2": (1, "DASHED"),
    "A-SOMBRILLAS-E1": (30, "DASHED"), "A-SOMBRILLAS-E2": (30, "DASHED"), "A-MOBILIARIO": (8, "CONTINUOUS"),
    "A-ARBOLES": (3, "CONTINUOUS"), "A-PISCINA-E2": (5, "CONTINUOUS"), "A-TEXTOS": (7, "CONTINUOUS"),
    "E-COLUMNAS": (1, "CONTINUOUS"), "E-ZAPATAS": (8, "DASHED"),
    "P1-MUROS": (7, "CONTINUOUS"), "P1-AMBIENTES": (8, "CONTINUOUS"), "P1-EQUIPOS": (30, "CONTINUOUS"),
    "P1-MESAS": (8, "CONTINUOUS"), "P2-MUROS": (7, "CONTINUOUS"), "P2-AMBIENTES": (8, "CONTINUOUS"),
    "P2-EQUIPOS": (30, "CONTINUOUS"), "P2-MESAS": (8, "CONTINUOUS"), "P-ESCALERAS": (4, "CONTINUOUS"),
}
DX_P1, DX_P2 = 72.0, 92.0          # desplazamiento de las plantas del edificio en el DXF


def _polys(geom):
    if geom is None or geom.is_empty:
        return []
    return [g_ for g_ in getattr(geom, "geoms", [geom]) if g_.geom_type == "Polygon"]


def _pl(msp, geom, capa, dx=0.0):
    for p in _polys(geom):
        pts = [(float(x) + dx, float(y)) for x, y in p.exterior.coords]
        msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": capa})


def _tx(msp, p, t, h=0.3, capa="A-TEXTOS", rot=0.0, dx=0.0):
    e = msp.add_text(t, height=h, rotation=rot, dxfattribs={"layer": capa})
    e.set_placement((float(p[0]) + dx, float(p[1])), align=TextEntityAlignment.MIDDLE_CENTER)


def exportar(ruta):
    doc = ezdxf.new("R2010", setup=True)
    doc.header["$INSUNITS"] = 6
    for nombre, (color, tipo) in CAPAS.items():
        doc.layers.add(nombre, color=color, linetype=tipo)
    msp = doc.modelspace()

    # --- planta general (u, v)
    _pl(msp, dz.LOTE, "A-LIMITE")
    _pl(msp, dz.INTERIOR, "A-CERCO")
    for cod, p0, p1, tipo, txt in lm.vanos():
        msp.add_line(tuple(map(float, p0)), tuple(map(float, p1)), dxfattribs={"layer": "A-VANOS"})
        t, n = lm._normal_interior(p0, p1)
        _tx(msp, (p0 + p1) / 2 - n * 1.5, f"{cod} {txt}", 0.35, "A-VANOS")
    for poly, txt in ((dz.LENA, "ALMACÉN DE LEÑA (EXISTENTE)"), (dz.GARAJE, "GARAJE (EXISTENTE)")):
        _pl(msp, poly, "A-EXISTENTE")
        _tx(msp, poly.centroid.coords[0], txt, 0.35, "A-EXISTENTE")
    _pl(msp, dz.CALZADA, "A-CALZADA")
    _pl(msp, dz.ZONA_CARGA, "A-CALZADA")
    _pl(msp, dz.VEREDA, "A-CAMINOS")
    _pl(msp, dz.caminos_poly(2), "A-CAMINOS")
    for p in dz.PLAZAS:
        _pl(msp, p["poly"], "A-PLAZAS")
        _tx(msp, p["poly"].centroid.coords[0], p["codigo"], 0.5, "A-PLAZAS")
    _pl(msp, dz.MOTOS, "A-PLAZAS")
    _pl(msp, dz.GLP, "A-EXISTENTE")
    _pl(msp, lm.jardines(1), "A-JARDIN")
    _pl(msp, lm.seto(1), "A-SETO")
    _pl(msp, dz.EDIFICIO, "A-EDIFICIO")
    _pl(msp, dz.LOSA2, "A-LOSA2")
    for a in ed.AMB:
        if a.piso == 1:
            _pl(msp, ed.local_inv(a.poly), "A-AMBIENTES")
    for s_, d_ in dz.COLUMNAS:
        c = dz.SD(s_, d_)
        _pl(msp, affinity.rotate(Point(c).buffer(0.102, cap_style=3), dz.ANG_SD, origin=tuple(c)), "E-COLUMNAS")
    for (s_, d_), tipo in lm.TIPO_COL.items():
        L_ = lm.es.ZAPATAS[tipo]["lado"]
        c = dz.SD(s_, d_)
        _pl(msp, affinity.rotate(Point(c).buffer(L_ / 2, cap_style=3), dz.ANG_SD, origin=tuple(c)), "E-ZAPATAS")
    for a in dz.SOMBRILLAS + dz.SOMBRILLAS_E1_SUR:
        _pl(msp, a.lona, "A-SOMBRILLAS-E1")
        _tx(msp, a.centro, a.codigo, 0.4, "A-SOMBRILLAS-E1")
        for tipo, pz in lm.mesa_sombrilla(a):
            _pl(msp, pz, "A-MOBILIARIO")
    for a in dz.SOMBRILLAS_E2_RELAJO:
        _pl(msp, a.lona, "A-SOMBRILLAS-E2")
    for arb in dz.ARBOLES:
        msp.add_circle(tuple(map(float, arb["p"])), arb["copa"] / 2, dxfattribs={"layer": "A-ARBOLES"})
    for pol in (dz.PISCINA, dz.PATERA, dz.ANDEN, dz.VESTIDORES, dz.VEST_DAMAS, dz.VEST_VARONES, dz.CUARTO_MAQ,
                dz.PASO_LIMPIO, dz.DUCHA_EXT, dz.PEDILUVIO, dz.RELAJO, *dz.CAMILLAS, *dz.HAMACAS):
        _pl(msp, pol, "A-PISCINA-E2")
    msp.add_lwpolyline([tuple(map(float, p)) for p in lm.ex.cerco_piscina()], dxfattribs={"layer": "A-PISCINA-E2"})
    _tx(msp, (20.0, -4.0), "PLANTA GENERAL (capas *-E1: 1.ª etapa, *-E2: 2.ª etapa) - coordenadas en m, origen en B", 0.5)

    # --- plantas del edificio (coordenadas locales desplazadas)
    for piso, dx in ((1, DX_P1), (2, DX_P2)):
        cap = f"P{piso}"
        for a in ed.AMB:
            if a.piso == piso:
                _pl(msp, a.poly, f"{cap}-AMBIENTES", dx + 25.0)
                c = a.poly.centroid
                _tx(msp, (c.x, c.y), a.nombre, 0.18, f"{cap}-AMBIENTES", dx=dx + 25.0)
        for a_, b_, tipo in lm.segmentos_muro(piso):
            if tipo in ("muro", "muro_ventana_alta", "muro_ventana", "muro_acustico", "tabique"):
                esp = 0.25 if tipo == "muro_acustico" else (0.10 if tipo == "tabique" else 0.15)
                _pl(msp, LineString([a_, b_]).buffer(esp / 2, cap_style=2).difference(lm.huecos_puertas(piso)),
                    f"{cap}-MUROS", dx + 25.0)
            else:
                msp.add_line((float(a_[0]) + dx + 25.0, float(a_[1])), (float(b_[0]) + dx + 25.0, float(b_[1])),
                             dxfattribs={"layer": f"{cap}-MUROS"})
        for e in ed.EQ:
            if e.piso == piso:
                _pl(msp, e.poly, f"{cap}-EQUIPOS", dx + 25.0)
        for m in (ed.MESAS_1 if piso == 1 else ed.MESAS_2):
            _pl(msp, m, f"{cap}-MESAS", dx + 25.0)
        if piso == 2:
            _pl(msp, ed.LOSA2_L, "P2-MUROS", dx + 25.0)
        tr1, desc, tr2 = ed.escalera_U()
        t1, desc2, t2, lleg = ed.escalera_exterior()
        for pol in tr1 + [desc] + tr2 + t1 + [desc2] + t2 + [lleg]:
            _pl(msp, pol, "P-ESCALERAS", dx + 25.0)
        _tx(msp, (-18.0 + dx + 25.0, -3.0), f"PLANTA DEL {'1.er' if piso == 1 else '2.º'} PISO (sistema local del edificio)", 0.4)
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    doc.saveas(ruta)
    return ruta


if __name__ == "__main__":
    print(exportar(os.path.join(AQUI, "salida", "Polleria_Campestre_planta.dxf")))
