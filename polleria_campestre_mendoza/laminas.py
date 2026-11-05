"""
Láminas del anteproyecto de la pollería campestre (PDF A3 apaisado).

    A-01  Planimetría general - 1.ª etapa (restaurante y jardines)
    A-02  Planimetría general - 2.ª etapa (piscina, vestidores y relajo)
    A-03  Circulaciones vehicular y peatonal, evacuación y aforo
    A-04  Sombrillas removibles: modo restaurante / modo evento y anclaje
    A-05  Planta del 1.er piso (cocina, hornos, parrilla y despacho)
    A-06  Planta del 2.º piso (bar, terraza y escenario)
    A-07  Cortes y elevaciones
    A-08  Piscina, vestidores y zona de relajo (2.ª etapa)
    E-01  Cimentación y columnas
    E-02  Estructura metálica del entrepiso y del techo

Reutiliza el marco de dibujo del anteproyecto de estacionamiento (`dibujo.py`,
`planos.dibujar_entorno`) y la geometría de `diseno.py` y `edificio.py`.
"""
from __future__ import annotations

import math
import os
import sys

import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Arc, Circle, Polygon as MplPolygon, Rectangle
from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(1, os.path.join(AQUI, "..", "estacionamiento_rodriguez_mendoza"))

import diseno as dz  # noqa: E402
import edificio as ed  # noqa: E402
import estructura_pol as es  # noqa: E402
import dibujo as dib  # noqa: E402
import planos as pl  # noqa: E402
from dibujo import (AZUL, GRIS, GRIS_CLARO, LW, ROJO, VERDE, Hoja, Vista, corte_marca, pt)  # noqa: E402

dib.PROYECTO = "POLLERÍA CAMPESTRE"
dib.SUBPROYECTO = "ANTEPROYECTO - EDIFICIO DE ESTRUCTURA METÁLICA"
dib.FECHA = "NOVIEMBRE 2026"

g = dz.g
TOTAL_LAMINAS = 10
ESC_GENERAL = 150
ORIGEN_GENERAL = (-3.6, -2.2)          # punto del terreno (m) que cae en (X0, Y0) de la hoja
X0, Y0 = 11.5, 34.0

# Colores de relleno
F_JARDIN = "#e6f1dc"
F_SETO = "#c3dcae"
F_CALZADA = "#e9e7e2"
F_PAVIMENTO = "#f3ead6"
F_EDIF = "#fbf4ea"
F_EXIST = "#dcd6cc"
F_AGUA = "#cdeaf8"
F_ANDEN = "#ede7da"
F_SERV = "#efe7f4"
F_ACC = "#d6e6f5"
F_MOTO = "#fbecc8"
F_COCINA = "#fde9d6"
F_SSHH = "#e4eef8"
F_ESCENARIO = "#f6e3a8"
F_LONA = "#f7efe0"
MARRON = "#8a6d3b"

# Ángulo (en la hoja) del eje d hacia el oeste -> textos del edificio alineados con sus fachadas
_N = np.array(g.DC.n)
_T = np.array(g.DC.t)
ANG_EDIF = math.degrees(math.atan2(-_N[1], -_N[0]))      # dirección de -n (hacia el este) ≈ 10°


def uv(geom_local):
    """Geometría en coordenadas locales del edificio -> (u, v)."""
    return ed.local_inv(geom_local)


def uvp(p_local):
    q = ed.local_inv(Point(p_local))
    return np.array([q.x, q.y])


def SD(s, d):
    return np.asarray(dz.SD(s, d), float)


# ==========================================================================
# Elementos comunes de las plantas generales
# ==========================================================================
def ocupado_etapa(etapa):
    base = [dz.LENA, dz.GARAJE, dz.CALZADA, *[p["poly"] for p in dz.PLAZAS], dz.MOTOS, dz.GLP, dz.VEREDA,
            dz.EDIFICIO, dz.PORCHE, dz.ESCALERA_EXT]
    if etapa >= 2:
        base.append(dz.ZONA_PISCINA)
    return unary_union(base).buffer(0)


def jardines(etapa):
    return dz.INTERIOR.difference(ocupado_etapa(etapa))


def vanos():
    """Vanos en los cercos de los frentes: (código, p0, p1, tipo, rótulo)."""
    pA = dz.punto_AB
    return [
        ("V-1", SD(0.0, dz.PORTON_V[0]), SD(0.0, dz.PORTON_V[1]), "porton2", "INGRESO Y SALIDA VEHICULAR"),
        ("P-2", SD(0.0, dz.PORTON_P2[0]), SD(0.0, dz.PORTON_P2[1]), "puerta", "INGRESO DE SERVICIO"),
        ("P-4", SD(0.0, 0.6), SD(0.0, 2.2), "puerta_ext", "GLP Y RESIDUOS"),
        ("P-1", pA(dz.P1_DESDE_A[0]), pA(dz.P1_DESDE_A[1]), "porton2", "INGRESO PRINCIPAL"),
        ("P-3", pA(dz.P3_DESDE_A[0]), pA(dz.P3_DESDE_A[1]), "emergencia", "SALIDA DE EMERGENCIA"),
    ]


def _normal_interior(p0, p1):
    t = (p1 - p0) / np.linalg.norm(p1 - p0)
    n = np.array([-t[1], t[0]])
    c = np.array(dz.LOTE.centroid.coords[0])
    if np.dot(c - p0, n) < 0:
        n = -n
    return t, n


def seto(etapa):
    franja = unary_union([LineString([dz.A, dz.B]).buffer(dz.MURO + dz.SETO, cap_style=2),
                          LineString([dz.D, dz.A]).buffer(dz.MURO + dz.SETO, cap_style=2)]).intersection(dz.INTERIOR)
    quitar = [dz.CALZADA, dz.VEREDA, dz.GLP, dz.MOTOS, dz.LENA, dz.caminos_poly(etapa), *[p["poly"] for p in dz.PLAZAS]]
    for cod, p0, p1, tipo, _ in vanos():
        quitar.append(LineString([p0, p1]).buffer(0.9, cap_style=2))
    if etapa >= 2:
        quitar.append(dz.ZONA_PISCINA)
    r = franja.difference(unary_union(quitar).buffer(0.15))
    return unary_union([p for p in getattr(r, "geoms", [r]) if p.area > 0.4])


def dibujar_cercos(v: Vista):
    anillo = dz.LOTE.difference(dz.INTERIOR)
    v.poly(anillo, fc="#8f8f8f", ec="none", z=4)
    v.poly(dz.LOTE, fc="none", ec="k", lw="grueso", z=5)
    v.poly(dz.INTERIOR, fc="none", ec="k", lw="fino", z=5)
    for cod, p0, p1, tipo, _ in vanos():
        hueco = LineString([p0, p1]).buffer(0.4, cap_style=2).intersection(anillo.buffer(0.02))
        v.poly(hueco, fc="white", ec="none", z=4.5)
        t, n = _normal_interior(p0, p1)
        w = np.linalg.norm(p1 - p0)
        q0, q1 = p0 + n * dz.MURO, p1 + n * dz.MURO
        if tipo == "porton2":                         # dos hojas batientes hacia el interior
            for a, b, sgn in ((q0, q0 + t * w / 2, 1), (q1, q1 - t * w / 2, -1)):
                hoja = a + n * (w / 2)
                v.linea([a, hoja], lw="medio", z=6)
                _arco(v, a, w / 2, b - a, hoja - a)
        elif tipo == "puerta":
            hoja = q0 + n * w
            v.linea([q0, hoja], lw="medio", z=6)
            _arco(v, q0, w, q1 - q0, hoja - q0)
        elif tipo in ("puerta_ext", "emergencia"):     # abre hacia la calle
            hoja = p0 - n * w * 0.9
            v.linea([p0, hoja], lw="medio", z=6)
            _arco(v, p0, w * 0.9, (p1 - p0) * 0.9, hoja - p0)


def _arco(v: Vista, centro, radio, va, vb, color="k"):
    """Arco de barrido de puerta entre los vectores va y vb (m)."""
    a1 = math.degrees(math.atan2(va[1], va[0]))
    a2 = math.degrees(math.atan2(vb[1], vb[0]))
    d = (a2 - a1) % 360
    if d > 180:
        a1, a2 = a2, a1
    c = v.T(centro)
    r = radio * v.k
    v.ax.add_patch(Arc(c, 2 * r, 2 * r, theta1=a1, theta2=a1 + min(d, 360 - d), lw=LW["fino"], color=color,
                       zorder=6, ls=(0, (3, 1.5))))


def rotular_vanos(v: Vista, sep=2.3, h=1.3):
    for cod, p0, p1, tipo, txt in vanos():
        t, n = _normal_interior(p0, p1)
        col = ROJO if tipo == "emergencia" else "k"
        v.texto_a_lo_largo(p0 - n * sep, p1 - n * sep, cod, h=1.8, color=col, weight="bold")
        v.texto_a_lo_largo(p0 - n * (sep + 1.1), p1 - n * (sep + 1.1), txt, h=h, color=col)


def mesa_sombrilla(a: dz.Sombrilla):
    """Mesa y sillas bajo una sombrilla, en (u, v)."""
    c = np.asarray(a.centro, float)
    piezas = []
    if a.mesa == "6":
        piezas.append(("mesa", box(-0.9, -0.45, 0.9, 0.45)))
        for x in (-0.6, 0.0, 0.6):
            for y in (-0.8, 0.8):
                piezas.append(("silla", box(x - 0.21, y - 0.21, x + 0.21, y + 0.21)))
    elif a.mesa == "4":
        piezas.append(("mesa", box(-0.45, -0.45, 0.45, 0.45)))
        for x, y in ((0, -0.8), (0, 0.8), (-0.8, 0), (0.8, 0)):
            piezas.append(("silla", box(x - 0.21, y - 0.21, x + 0.21, y + 0.21)))
    out = []
    for tipo, p in piezas:
        p = affinity.rotate(p, a.ang + (90 if a.mesa == "6" else 0), origin=(0, 0))
        out.append((tipo, affinity.translate(p, c[0], c[1])))
    return out


def asientos(a: dz.Sombrilla):
    return {"6": 6, "4": 4}.get(a.mesa, 0)


def dibujar_sombrilla(v: Vista, a: dz.Sombrilla, rotulo=True, muebles=True, solo_anclaje=False, h=1.6):
    c = np.asarray(a.centro, float)
    if solo_anclaje:
        v.circulo(c, 0.9, fc="white", ec=MARRON, lw="medio")
        v.circulo(c, 0.35, fc=MARRON, ec=MARRON, lw="fino")
        if rotulo:
            v.texto(c + np.array([0, -1.0]), a.codigo, h=1.2, color=MARRON)
        return
    v.poly(a.lona, fc=F_LONA, ec=MARRON, lw="fino", ls=(0, (4, 1.5)), z=6, alpha=0.95)
    lona = np.asarray(a.lona.exterior.coords)[:4]
    for p in lona:                                  # varillas de la lona
        v.linea([c, p], lw=0.08 * dib.MM, color=MARRON, z=6.1)
    if muebles:
        for tipo, p in mesa_sombrilla(a):
            v.poly(p, fc="white", ec="k", lw="fino", z=6.2)
    v.circulo(c, 0.55, fc=MARRON, ec="k", lw="fino", z=6.3)
    if rotulo:
        d = np.array([np.cos(np.radians(a.ang + 45)), np.sin(np.radians(a.ang + 45))])
        v.texto(c + d * 1.65 * 0.0 + np.array([0.0, 1.25]), a.codigo, h=h, weight="bold", color=MARRON, z=7,
                bbox=dict(fc="white", ec="none", pad=0.3, alpha=0.85))


def dibujar_arbol(v: Vista, arb, z=7):
    p = np.asarray(arb["p"], float)
    r = arb["copa"] / 2
    if arb["tipo"] == "palmera":
        for k in range(8):
            ang = k * math.pi / 4 + 0.2
            v.linea([p, p + r * np.array([math.cos(ang), math.sin(ang)])], lw="fino", color=VERDE, z=z)
        v.poly(Point(p).buffer(r), fc="none", ec=VERDE, lw="fino", ls=(0, (2, 2)), z=z)
    else:
        circ = Point(p).buffer(r, resolution=32)
        borde = []
        nlob = 9 if arb["tipo"] == "frondoso" else 6
        for k in range(nlob):
            ang = 2 * math.pi * k / nlob
            borde.append(Point(p + 0.78 * r * np.array([math.cos(ang), math.sin(ang)])).buffer(0.36 * r))
        copa = unary_union([circ.buffer(-0.25 * r), *borde])
        v.poly(copa, fc="#cfe5bd", ec=VERDE, lw="fino", z=z, alpha=0.9)
    v.circulo(p, 0.45, fc=VERDE, ec=VERDE, lw="fino", z=z + 0.1)


def dibujar_plazas(v: Vista):
    for p in dz.PLAZAS:
        acc = p["tipo"] == "accesible"
        v.poly(p["poly"], fc=F_ACC if acc else "white", ec="k", lw="fino", z=3)
        s0, s1 = p["s0"], p["s1"]
        d_mid = dz.D_CALZ[0] - dz.LARGO_PLAZA / 2
        if acc:                                       # franja de transferencia de 1.20 m achurada
            v.poly(dz.rect_sd(s0, s0 + 1.2, dz.D_CALZ[0] - dz.LARGO_PLAZA, dz.D_CALZ[0]), fc="none", ec="k",
                   lw="fino", hatch="////", hatch_color=AZUL, z=3.1)
            v.texto(SD((s0 + 1.2 + s1) / 2, d_mid + 0.6), "♿" if False else "ACC.", h=1.6, weight="bold",
                    color=AZUL, ang=ANG_EDIF + 90)
            s_tope0 = s0 + 1.6
        else:
            s_tope0 = s0 + 0.4
        v.poly(dz.rect_sd(s_tope0, s1 - 0.4, 0.85, 1.0), fc="#666666", ec="none", z=3.2)    # tope de llantas
        v.texto(SD((s_tope0 + s1) / 2 if acc else (s0 + s1) / 2, d_mid - 0.4), p["codigo"], h=1.7, weight="bold",
                ang=ANG_EDIF + 90)
    # motos (2) y caseta de GLP
    v.poly(dz.MOTOS, fc=F_MOTO, ec="k", lw="fino", z=3)
    s0, s1, d0, d1 = 0.35, 2.45, 2.55, 5.05
    v.linea([SD((s0 + s1) / 2, d0), SD((s0 + s1) / 2, d1)], lw="fino", z=3.1)
    v.texto(SD(s0 + 0.52, (d0 + d1) / 2), "M1", h=1.2, ang=ANG_EDIF + 90)
    v.texto(SD(s1 - 0.52, (d0 + d1) / 2), "M2", h=1.2, ang=ANG_EDIF + 90)


def dibujar_existentes(v: Vista, h=1.5):
    for poly, txt in ((dz.LENA, "ALMACÉN DE LEÑA\n(EXISTENTE)"), (dz.GARAJE, "GARAJE DEL PROPIETARIO\n(EXISTENTE)")):
        v.poly(poly, fc=F_EXIST, ec="k", lw="grueso", z=3, hatch="xx", hatch_color="#b9b2a6")
        c = np.array(poly.centroid.coords[0])
        ang = ANG_EDIF + 90 if poly is dz.LENA else 0
        v.texto(c, txt, h=h, weight="bold", ang=ang, bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.9),
                linespacing=1.05)


def dibujar_escalera(v: Vista, tramos, flecha_desde=None, flecha_hasta=None):
    for pol in tramos:
        v.poly(uv(pol), fc="white", ec="k", lw="fino", z=4)
    if flecha_desde is not None:
        v.flecha_simple(flecha_desde, flecha_hasta, lw="fino", cab=1.4, z=7)


def dibujar_edificio_general(v: Vista, rotular=True, h=1.15):
    """Planta simplificada del 1.er piso del edificio sobre la planta general."""
    v.poly(dz.PORCHE, fc=F_PAVIMENTO, ec="none", z=2)
    v.poly(dz.EDIFICIO, fc=F_EDIF, ec="none", z=3)
    colores = {"cocina": F_COCINA, "sshh": F_SSHH, "servicio": F_SERV}
    for a in ed.AMB:
        if a.piso != 1:
            continue
        v.poly(uv(a.poly), fc=colores.get(a.uso, F_EDIF), ec="k", lw="fino", z=3.2)
    for e in ed.EQ:
        if e.piso == 1 and e.tipo in ("equipo",):
            v.poly(uv(e.poly), fc="#d9a77a", ec="k", lw="fino", z=3.4)
    tr1, desc, tr2 = ed.escalera_U()
    dibujar_escalera(v, tr1 + [desc] + tr2)
    t1, desc2, t2, lleg = ed.escalera_exterior()
    dibujar_escalera(v, t1 + [desc2] + t2 + [lleg])
    asc = uv(ed.RL(*ed.ASCENSOR))
    v.poly(asc, fc="white", ec="k", lw="fino", z=4)
    c = np.asarray(asc.exterior.coords)[:4]
    v.linea([c[0], c[2]], lw="fino", z=4.1)
    v.linea([c[1], c[3]], lw="fino", z=4.1)
    v.poly(dz.EDIFICIO, fc="none", ec="k", lw="mgrueso", z=5)
    v.poly(dz.LOSA2, fc="none", ec=ROJO, lw="medio", ls=(0, (6, 2, 1, 2)), z=5.5)
    for s_, d_ in dz.COLUMNAS:
        p = SD(s_, d_)
        v.poly(Point(p).buffer(0.16, cap_style=3).envelope if False else
               affinity.rotate(box(p[0] - 0.13, p[1] - 0.13, p[0] + 0.13, p[1] + 0.13), ANG_EDIF, origin=tuple(p)),
               fc="k", ec="k", lw="fino", z=6)
    if rotular:
        etiquetas = [
            ("COCINA\n(HORNOS Y PARRILLA)", 12.5, 15.6),
            ("DESPACHO\nY MESAS", 13.7, 21.0),
            ("HALL", 8.9, 19.0),
            ("SS.HH.", 17.3, 20.4),
            ("LAVADO", 16.7, 13.4),
            ("SERV.", 8.75, 14.7),

        ]
        for txt, s_, d_ in etiquetas:
            v.texto(SD(s_, d_), txt, h=h, ang=ANG_EDIF, linespacing=1.0, z=7,
                    weight="bold" if "COCINA" in txt or "PORCHE" in txt else "normal")
        v.texto(SD(6.5, 17.2), "PORCHE NORTE", h=h, ang=ANG_EDIF, z=7)
        v.texto(SD(12.2, 23.9), "PORCHE OESTE", h=h, ang=ANG_EDIF + 90, z=7)


def dibujar_superficies(v: Vista, etapa):
    v.poly(jardines(etapa), fc=F_JARDIN, ec="none", z=1)
    v.poly(seto(etapa), fc=F_SETO, ec=VERDE, lw="fino", z=1.5, hatch="oo", hatch_color="#8fbf73")
    v.poly(dz.CALZADA, fc=F_CALZADA, ec="k", lw="fino", z=2)
    v.poly(dz.ZONA_CARGA, fc="none", ec="k", lw="fino", hatch="\\\\\\\\", hatch_color=GRIS, z=2.2)
    v.poly(dz.VEREDA, fc=F_PAVIMENTO, ec="k", lw="fino", z=2)
    v.poly(dz.caminos_poly(etapa), fc=F_PAVIMENTO, ec="#9c8a63", lw="fino", z=2)
    v.poly(dz.GLP, fc=F_SERV, ec="k", lw="grueso", z=3)
    v.texto(np.array(dz.GLP.centroid.coords[0]), "GLP\nRES.", h=1.1, ang=ANG_EDIF + 90, linespacing=1.0)


def flechas_vehiculares(v: Vista):
    d_in, d_out = 6.7, 9.7
    v.flecha(SD(4.2, d_in), SD(8.6, d_in), ancho_mm=3.0, fc="white")
    v.flecha(SD(8.6, d_out), SD(4.2, d_out), ancho_mm=3.0, fc="white")
    v.flecha(SD(14.0, d_in), SD(22.0, d_in), ancho_mm=3.0, fc="white")
    v.flecha(SD(22.0, d_out), SD(14.0, d_out), ancho_mm=3.0, fc="white")
    v.texto(SD(10.5, 8.2), "CALZADA DE DOBLE SENTIDO  6.00 m", h=1.5, ang=ANG_EDIF + 90, weight="bold")
    v.texto(SD(24.5, 8.2), "ACCESO AL GARAJE", h=1.3, ang=ANG_EDIF + 90)
    v.texto(SD(9.3, 10.25), "CARGA", h=1.2, ang=ANG_EDIF + 90)


def cotas_generales(v: Vista):
    A, B, C, D = dz.A, dz.B, dz.C, dz.D
    v.cota(A, B, offset_mm=24, lado=-1, texto="30.00", h=2.2)
    v.cota(B, C, offset_mm=14, lado=-1, texto="40.00", h=2.2)
    v.cota(C, D, offset_mm=10, lado=-1, texto="30.00", h=2.2)
    v.cota(D, A, offset_mm=44, lado=-1, texto="20.00", h=2.2)
    # franja vehicular (a lo largo de la calle lateral), sobre la vereda pública
    v.cota(SD(0, 0), SD(0, dz.D_CALZ[0]), offset_mm=4.5, lado=-1, h=1.4)
    v.cota(SD(0, dz.D_CALZ[0]), SD(0, dz.D_CALZ[1]), offset_mm=4.5, lado=-1, h=1.4)
    v.cota(SD(0, dz.D_CALZ[1]), SD(0, dz.D_VEREDA[1]), offset_mm=4.5, lado=-1, h=1.4)


def marca_norte(v, xy=(296, 262)):
    v.norte(xy, g.NORTE, largo=13)


def leyenda(h: Hoja, x, y, items, paso=3.9):
    h.texto(x, y + 1, "LEYENDA", h=2.0, weight="bold", va="bottom")
    for i, (tipo, col, txt) in enumerate(items):
        yy = y - 3.0 - i * paso
        if tipo == "rect":
            h.ax.add_patch(Rectangle((x, yy - 1.3), 7, 2.6, fc=col, ec="k", lw=LW["fino"]))
        elif tipo == "hatch":
            h.ax.add_patch(Rectangle((x, yy - 1.3), 7, 2.6, fc=col[0], ec="k", lw=LW["fino"], hatch=col[1]))
        elif tipo == "dash":
            h.ax.plot([x, x + 7], [yy, yy], color=col, lw=LW["medio"], ls=(0, (6, 2, 1, 2)))
        elif tipo == "col":
            h.ax.add_patch(Rectangle((x + 2.5, yy - 1.0), 2.0, 2.0, fc="k"))
        elif tipo == "somb":
            h.ax.add_patch(Rectangle((x + 0.8, yy - 1.6), 5.4, 3.2, fc=F_LONA, ec=MARRON, lw=LW["fino"], ls="--"))
            h.ax.add_patch(Circle((x + 3.5, yy), 0.7, fc=MARRON))
        elif tipo == "arbol":
            h.ax.add_patch(Circle((x + 3.5, yy), 1.5, fc="#cfe5bd", ec=VERDE, lw=LW["fino"]))
        elif tipo == "linea":
            h.ax.plot([x, x + 7], [yy, yy], color=col, lw=LW["grueso"])
        h.texto(x + 9, yy, txt, h=1.5)
    return y - 3.0 - len(items) * paso


# ==========================================================================
# Cuadros (áreas, mesas y aforo)
# ==========================================================================
def asientos_jardin(etapa):
    lista = dz.SOMBRILLAS + (dz.SOMBRILLAS_E1_SUR if etapa == 1 else [])
    return sum(asientos(a) for a in lista), len(lista)


def asientos_edificio():
    p1 = 4 * len(ed.MESAS_1)
    p2 = 4 * len(ed.MESAS_2) + len(ed.TABURETES)
    return p1, p2


def cuadro_areas(etapa):
    j = jardines(etapa).area
    filas = [
        ["Área del terreno", dz.LOTE.area],
        ["Almacén de leña y garaje (existentes)", dz.LENA.area + dz.GARAJE.area],
        ["Calzada, estacionamientos, motos y GLP", dz.CALZADA.area + sum(p["poly"].area for p in dz.PLAZAS)
         + dz.MOTOS.area + dz.GLP.area],
        ["Edificio: 1.er piso cerrado", dz.EDIFICIO.area],
        ["Porches techados (bajo el 2.º piso)", dz.PORCHE.area],
        ["Veredas, caminos y escalera exterior", dz.VEREDA.area + dz.ESCALERA_EXT.area
         + dz.caminos_poly(etapa).difference(dz.PORCHE).area],
    ]
    if etapa >= 2:
        filas.append(["Piscina, andenes, vestidores y relajo", dz.ZONA_PISCINA.area])
    filas.append(["Jardines y setos", j - dz.caminos_poly(etapa).difference(dz.PORCHE).area])
    filas.append(["2.º piso: bar, SS.HH., terraza y escenario (techado parcial)", dz.LOSA2.area])
    area_techada = dz.EDIFICIO.area + dz.LOSA2.area
    return filas, area_techada


# ==========================================================================
# A-01  Planimetría general - 1.ª etapa
# ==========================================================================
def lamina_planimetria(pdf, png_dir, etapa=1):
    codigo = "A-01" if etapa == 1 else "A-02"
    n = 1 if etapa == 1 else 2
    h = Hoja(codigo, "PLANIMETRÍA GENERAL", "ARQUITECTURA", "1/150", n, TOTAL_LAMINAS,
             subtitulo="1.ª ETAPA: RESTAURANTE Y JARDINES" if etapa == 1 else "2.ª ETAPA: PISCINA, VESTIDORES Y RELAJO")
    v = h.vista(X0, Y0, ESC_GENERAL, ORIGEN_GENERAL)
    pl.dibujar_entorno(v)
    dibujar_superficies(v, etapa)
    dibujar_plazas(v)
    dibujar_existentes(v)
    dibujar_edificio_general(v)
    if etapa >= 2:
        dibujar_piscina_general(v)
    somb = dz.SOMBRILLAS + (dz.SOMBRILLAS_E1_SUR if etapa == 1 else dz.SOMBRILLAS_E2_RELAJO)
    for a in somb:
        dibujar_sombrilla(v, a)
    for arb in dz.ARBOLES:
        if arb.get("etapa", 1) <= etapa:
            dibujar_arbol(v, arb)
    dibujar_cercos(v)
    rotular_vanos(v)
    flechas_vehiculares(v)
    cotas_generales(v)
    # rótulos de zonas
    caja = dict(fc="white", ec="none", pad=0.5, alpha=0.8)
    v.texto(SD(4.2, 16.4) + np.array([0.0, 0.0]), "JARDÍN NORTE", h=1.7, weight="bold", color=VERDE, bbox=caja)
    v.texto(SD(13.2, 30.3), "JARDÍN OESTE", h=1.7, weight="bold", color=VERDE, ang=ANG_EDIF + 60, bbox=caja)
    if etapa == 1:
        v.texto((19.0, 4.55), "JARDÍN SUR (FUTURA ZONA DE PISCINA - 2.ª ETAPA)", h=1.6, weight="bold", color=VERDE,
                bbox=caja)
    v.texto(SD(12.0, 25.2) + np.array([0.0, 0.0]), "", h=1.0)
    v.texto(SD(5.0, 19.0) + _N * 0.0, "", h=1.0)
    v.texto(SD(5.0, 11.8), "VEREDA 1.20", h=1.1, ang=ANG_EDIF + 90)
    marca_norte(v)
    v.escala_grafica((215, 20), metros=10, paso=2)
    h.titulo_vista(80, 23, "PLANIMETRÍA GENERAL - " + ("1.ª ETAPA" if etapa == 1 else "2.ª ETAPA"), "ESC. 1/150")

    # ---- franja derecha
    x = h.x_franja + 2.5
    filas, techada = cuadro_areas(etapa)
    yb = h.tabla(x, 281, ["CUADRO DE ÁREAS", "m²"], [[a, f"{b:,.1f}"] for a, b in filas], [72, 14], h_fila=4.0,
                 h_txt=1.5, alinear=["l", "r"])
    h.texto(x, yb - 2.6, f"Área techada total (1.er + 2.º piso): {techada:,.1f} m²", h=1.5, weight="bold")
    sj, nm = asientos_jardin(etapa)
    p1, p2 = asientos_edificio()
    filas_m = [["Jardines: sombrillas (mesas de 6 y 4)", f"{nm}", f"{sj}"],
               ["1.er piso: salón y porches (mesas de 4)", f"{len(ed.MESAS_1)}", f"{p1}"],
               ["2.º piso: terraza (mesas de 4) y barras", f"{len(ed.MESAS_2)}", f"{p2}"],
               ["TOTAL MODO RESTAURANTE", "", f"{sj + p1 + p2}"]]
    if etapa >= 2:
        filas_m.insert(1, ["Zona de relajo: camillas y hamacas", f"{len(dz.CAMILLAS) + len(dz.HAMACAS)}", "-"])
    yb = h.tabla(x, yb - 9, ["CAPACIDAD (MODO RESTAURANTE)", "MESAS", "ASIENTOS"], filas_m, [56, 14, 16],
                 h_fila=4.0, h_txt=1.5, alinear=["l", "r", "r"], negrita_ultima=True)
    items = [("rect", F_JARDIN, "Jardín (césped)"),
             ("hatch", (F_SETO, "oo"), "Seto vivo tras el cerco de los frentes"),
             ("rect", F_PAVIMENTO, "Caminos, vereda y porches (piedra o laja)"),
             ("rect", F_CALZADA, "Calzada y estacionamientos (adoquín de concreto)"),
             ("hatch", (F_EXIST, "xx"), "Estructuras existentes que se conservan"),
             ("somb", None, "Sombrilla profesional 3.00 × 3.00 m (removible)"),
             ("arbol", None, "Árbol / palmera"),
             ("dash", ROJO, "Proyección del 2.º piso (volados de 2.00 m)"),
             ("col", "k", f"Columna metálica {es.COLUMNA['seccion'].nombre}")]
    if etapa >= 2:
        items.insert(4, ("rect", F_AGUA, "Piscina y patera (2.ª etapa)"))
    yb = leyenda(h, x, yb - 8, items, paso=3.6)
    if etapa == 1:
        notas = [
            "1. Cotas en metros. Las estructuras de leña y garaje existentes se conservan; el garaje se usa por la misma calzada.",
            "2. Las sombrillas S1 a S10 se anclan en camisas metálicas empotradas al ras del césped: se retiran en minutos para eventos (ver A-04).",
            "3. La franja sur (S6 a S10) se reserva para la piscina de la 2.ª etapa (ver A-02).",
            "4. Estacionamiento descubierto: 5 plazas (1 accesible 3.80 × 5.00 m) + 2 motos. Para eventos se coordina estacionamiento en la vía (ver A-03).",
        ]
    else:
        notas = [
            "1. La piscina se separa del jardín con cerco de vidrio templado de 1.20 m; se entra solo por los vestidores, ducha y pediluvio (D.S. 007-2003-SA).",
            "2. En la 2.ª etapa la sombrilla S6 pasa a la zona de relajo; S7 a S10 se guardan para eventos o se reubican.",
            "3. Requiere autorización sanitaria de la DIRESA Amazonas, salvavidas en horario de uso y señalización de profundidades.",
        ]
    yb = h.notas(yb - 2, "NOTAS", notas, h=1.4, ancho_chars=64)
    if yb - h.y_cajetin_top > 30:
        filas_v = [["V-1", "Portón de 2 hojas batientes (madera y acero)", "6.00"],
                   ["P-1", "Portada principal de 2 hojas con techo de teja", "3.00"],
                   ["P-2", "Puerta de servicio y evacuación del 2.º piso", "1.80"],
                   ["P-3", "Salida de emergencia, barra antipánico", "1.20"],
                   ["P-4", "Puerta de la caseta de GLP y residuos", "1.60"]]
        h.tabla(x, yb - 1, ["VANO", "DESCRIPCIÓN", "ANCHO"], filas_v, [12, 60, 14], h_fila=3.8, h_txt=1.4,
                alinear=["c", "l", "r"])
    h.guardar(pdf, os.path.join(png_dir, f"{codigo}.png") if png_dir else None)


def dibujar_piscina_general(v: Vista, rotular=True, h=1.25):
    v.poly(dz.ZONA_PISCINA, fc="#eef6ee", ec="none", z=1.6)
    v.poly(dz.ANDEN, fc=F_ANDEN, ec="k", lw="fino", z=2.5)
    v.poly(dz.RELAJO, fc="#f8f3dc", ec="#9c8a63", lw="fino", ls=(0, (3, 2)), z=2.4)
    v.poly(dz.PISCINA, fc=F_AGUA, ec="k", lw="grueso", z=3)
    v.poly(dz.PATERA, fc="#e2f4fc", ec="k", lw="grueso", z=3)
    v.poly(dz.PEDILUVIO, fc=F_AGUA, ec="k", lw="medio", z=3)
    v.poly(dz.DUCHA_EXT, fc="#e2f4fc", ec="k", lw="medio", z=3.1)
    for pol, fc in ((dz.VEST_DAMAS, F_SSHH), (dz.VEST_VARONES, F_SSHH), (dz.CUARTO_MAQ, F_SERV),
                    (dz.PASO_LIMPIO, F_PAVIMENTO)):
        v.poly(pol, fc=fc, ec="k", lw="medio", z=3)
    v.poly(dz.VESTIDORES, fc="none", ec="k", lw="mgrueso", z=3.2)
    for c in dz.CAMILLAS:
        v.poly(c, fc="white", ec="k", lw="fino", z=6.5)
    for hm in dz.HAMACAS:
        v.poly(hm, fc="#fff3cf", ec="k", lw="fino", z=6.5)
    # cerco de vidrio
    sw = dz.SD(dz.S1, dz.D1 + dz.VOLADO_O)
    x1, y1 = dz.VESTIDORES.bounds[2], dz.VESTIDORES.bounds[3]
    cerco = [(x1, y1), (dz.U_CERCO_PISCINA, y1), (dz.U_CERCO_PISCINA, dz.V_CERCO_PISCINA),
             (sw[0], dz.V_CERCO_PISCINA), (sw[0], sw[1])]
    v.linea(cerco, lw="grueso", color=AZUL, z=5)
    if rotular:
        v.texto(np.array(dz.PISCINA.centroid.coords[0]), f"PISCINA\n6.00 × 3.50\nprof. {dz.PROF_MIN:.2f}-{dz.PROF_MAX:.2f}",
                h=h, weight="bold", linespacing=1.0)
        v.texto(np.array(dz.PATERA.centroid.coords[0]), f"PATERA\n2.40 × 2.40\nprof. 0.30-0.40", h=1.0,
                linespacing=1.0)
        for pol, txt in ((dz.VEST_DAMAS, "VEST.\nDAMAS"), (dz.VEST_VARONES, "VEST.\nVARONES"), (dz.CUARTO_MAQ, "MÁQ."),
                         (dz.PASO_LIMPIO, "PASO")):
            v.texto(np.array(pol.centroid.coords[0]), txt, h=1.0, linespacing=1.0)
        v.texto(np.array(dz.PEDILUVIO.centroid.coords[0]) + np.array([0.6, -0.95]), "PEDILUVIO", h=0.95)
        v.texto(np.array(dz.DUCHA_EXT.centroid.coords[0]) + np.array([0.0, 0.95]), "DUCHA", h=0.95)
        v.texto((25.5, 4.55), "ZONA DE\nRELAJO", h=1.15, weight="bold", linespacing=1.0)
        v.texto((19.7, 6.15), "ANDÉN 1.50 m", h=1.0)
        v.texto((12.0, 6.15), "CERCO DE VIDRIO h = 1.20 m", h=1.0, color=AZUL, ha="left")


def generar(salida_dir, png_dir=None, solo=None):
    os.makedirs(salida_dir, exist_ok=True)
    if png_dir:
        os.makedirs(png_dir, exist_ok=True)
    ruta = os.path.join(salida_dir, "Planos_Polleria_Campestre_Mendoza.pdf")
    laminas = [
        ("A-01", lambda p: lamina_planimetria(p, png_dir, 1)),
        ("A-02", lambda p: lamina_planimetria(p, png_dir, 2)),
    ]
    with PdfPages(ruta) as pdf:
        for cod, fn in laminas:
            if solo and cod not in solo:
                continue
            fn(pdf)
        d = pdf.infodict()
        d["Title"] = "Pollería campestre - Rodríguez de Mendoza (anteproyecto)"
        d["Subject"] = "Planos de arquitectura y estructuras"
    return ruta


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(AQUI, "salida")
    png = sys.argv[2] if len(sys.argv) > 2 else os.path.join(out, "png")
    solo = sys.argv[3].split(",") if len(sys.argv) > 3 else None
    print(generar(out, png, solo))
