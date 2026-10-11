"""
Exporta la planta general (arquitectura + estructura) a DXF (AutoCAD R2010),
en metros y en el sistema de coordenadas local del terreno (origen en B).
"""
from __future__ import annotations

import os

import ezdxf
import numpy as np
from ezdxf.enums import TextEntityAlignment

import estructura as est
import geometria as g

CAPAS = {
    "A-LIMITE": (7, "CONTINUOUS"),
    "A-CERCO": (8, "CONTINUOUS"),
    "A-PORTONES": (3, "CONTINUOUS"),
    "A-PLAZAS": (7, "CONTINUOUS"),
    "A-PLAZAS-ACC": (5, "CONTINUOUS"),
    "A-NUMERACION": (2, "CONTINUOUS"),
    "A-CIRCULACION": (4, "CONTINUOUS"),
    "A-MOTOS": (30, "CONTINUOUS"),
    "A-SERVICIOS": (6, "CONTINUOUS"),
    "A-TEXTOS": (7, "CONTINUOUS"),
    "A-COTAS": (1, "CONTINUOUS"),
    "S-TECHOS": (5, "DASHED"),
    "S-COLUMNAS": (1, "CONTINUOUS"),
    "S-ZAPATAS": (8, "DASHED"),
    "S-VIGAS": (6, "CONTINUOUS"),
    "S-CORREAS": (4, "CONTINUOUS"),
    "S-ARRIOSTRES": (1, "CONTINUOUS"),
}


def _pts(poly):
    return [tuple(map(float, c)) for c in poly.exterior.coords]


def _polilinea(msp, poly, capa):
    msp.add_lwpolyline(_pts(poly), close=True, dxfattribs={"layer": capa})


def _texto(msp, p, t, h=0.30, capa="A-TEXTOS", rot=0.0):
    e = msp.add_text(t, height=h, rotation=rot, dxfattribs={"layer": capa})
    e.set_placement(tuple(map(float, p)), align=TextEntityAlignment.MIDDLE_CENTER)


def exportar(ruta):
    doc = ezdxf.new("R2010", setup=True)
    doc.header["$INSUNITS"] = 6       # metros
    for nombre, (color, tipo) in CAPAS.items():
        doc.layers.add(nombre, color=color, linetype=tipo)
    msp = doc.modelspace()

    _polilinea(msp, g.LOTE, "A-LIMITE")
    _polilinea(msp, g.LOTE.buffer(-0.15, join_style=2), "A-CERCO")
    for k, p in g.VERT.items():
        _texto(msp, p + (p - np.array(g.LOTE.centroid.coords[0])) / 12, k, 0.6, "A-TEXTOS")
    for seg, t in ((g.PORTON_INGRESO, "P-1 INGRESO 3.00"), (g.PORTON_SALIDA, "P-2 SALIDA 3.00"),
                   (g.PUERTA_PEATONAL, "PP-1"), (g.PUERTA_PEATONAL_2, "PP-2")):
        a, b = (tuple(map(float, c)) for c in seg.coords)
        msp.add_line(a, b, dxfattribs={"layer": "A-PORTONES", "lineweight": 50})
        m = (np.array(a) + np.array(b)) / 2
        _texto(msp, m, t, 0.35, "A-PORTONES")

    geoms = getattr(g.CIRCULACION, "geoms", [g.CIRCULACION])
    for c in geoms:
        _polilinea(msp, c, "A-CIRCULACION")
    for p in g.PLAZAS:
        _polilinea(msp, p.poly, "A-PLAZAS-ACC" if p.tipo == "accesible" else "A-PLAZAS")
        _texto(msp, np.array(p.poly.centroid.coords[0]), p.codigo, 0.45, "A-NUMERACION")
    for i, m in enumerate(g.MOTOS):
        _polilinea(msp, m, "A-MOTOS")
        _texto(msp, np.array(m.centroid.coords[0]), f"M{i + 1}", 0.20, "A-MOTOS")
    for i, m in enumerate(g.MOTOTAXIS):
        _polilinea(msp, m, "A-MOTOS")
        _texto(msp, np.array(m.centroid.coords[0]), f"MT{i + 1}", 0.25, "A-MOTOS")
    for poly, t in ((g.GARITA, "GARITA"), (g.SSHH, "SS.HH."), (g.DEPOSITO, "DEP.")):
        _polilinea(msp, poly, "A-SERVICIOS")
        _texto(msp, np.array(poly.centroid.coords[0]), t, 0.25, "A-SERVICIOS")

    # estructura
    for cob in g.COBERTURAS:
        _polilinea(msp, cob.poly, "S-TECHOS")
        b = cob.fila.borde
        _texto(msp, b.punto((cob.s0 + cob.s1) / 2, (cob.d_atras + cob.d_frente) / 2), cob.nombre, 0.5, "S-TECHOS")
        for i in range(est.N_CORREAS):
            d = cob.d_atras + cob.mira_hacia * (0.10 + i * est.SEP_CORREAS)
            msp.add_line(tuple(b.punto(cob.s0, d)), tuple(b.punto(cob.s1, d)), dxfattribs={"layer": "S-CORREAS"})
        ss = [s for (_, s, _) in cob.columnas]
        for s in ss:
            msp.add_line(tuple(b.punto(s, cob.d_atras)), tuple(b.punto(s, cob.d_frente)),
                         dxfattribs={"layer": "S-VIGAS", "lineweight": 50})
            zap = b.rect(s - est.ZAP_L / 2, s + est.ZAP_L / 2, cob.d_col - est.ZAP_B / 2, cob.d_col + est.ZAP_B / 2)
            _polilinea(msp, zap, "S-ZAPATAS")
            hc, bc = est.COLUMNA.h / 1000, est.COLUMNA.b / 1000
            col = b.rect(s - bc / 2, s + bc / 2, cob.d_col - hc / 2, cob.d_col + hc / 2)
            _polilinea(msp, col, "S-COLUMNAS")
            hatch = msp.add_hatch(color=1, dxfattribs={"layer": "S-COLUMNAS"})
            hatch.paths.add_polyline_path(_pts(col), is_closed=True)
        if len(ss) >= 2:
            for a, c in {(ss[0], ss[1]), (ss[-2], ss[-1])}:
                msp.add_line(tuple(b.punto(a, cob.d_atras)), tuple(b.punto(c, cob.d_frente)),
                             dxfattribs={"layer": "S-ARRIOSTRES"})
                msp.add_line(tuple(b.punto(a, cob.d_frente)), tuple(b.punto(c, cob.d_atras)),
                             dxfattribs={"layer": "S-ARRIOSTRES"})
    k = 1
    for cob in g.COBERTURAS:
        for (pt_, s, d) in cob.columnas:
            c = np.array(pt_.coords[0])
            _texto(msp, c + cob.fila.borde.n * cob.mira_hacia * 1.9, f"C-{k:02d}", 0.30, "S-COLUMNAS")
            k += 1

    # cotas de linderos
    estilo = "EZDXF"
    for p0, p1, dist in ((g.A, g.B, -2.5), (g.B, g.C, -1.5), (g.C, g.D, -1.5), (g.D, g.A, -2.5)):
        cen = np.array(g.LOTE.centroid.coords[0])
        t = (p1 - p0) / np.linalg.norm(p1 - p0)
        n = np.array([-t[1], t[0]])
        if np.dot(cen - p0, n) > 0:
            n = -n
        dim = msp.add_aligned_dim(p1=tuple(map(float, p0)), p2=tuple(map(float, p1)), distance=float(abs(dist)) *
                                  (1 if float(np.dot(n, [-t[1], t[0]])) > 0 else -1), dimstyle=estilo,
                                  override={"dimtxt": 0.35, "dimasz": 0.25, "dimdec": 2, "dimlfac": 1.0, "dimpost": "<> m"},
                                  dxfattribs={"layer": "A-COTAS"})
        dim.render()
    _texto(msp, (20, -4.5), "ESTACIONAMIENTO TECHADO - JR. RODRIGUEZ DE MENDOZA - ANTEPROYECTO (unidades: m)", 0.5)
    doc.saveas(ruta)
    return ruta


if __name__ == "__main__":
    import sys
    print(exportar(sys.argv[1] if len(sys.argv) > 1 else "salida/Estacionamiento_planta.dxf"))
