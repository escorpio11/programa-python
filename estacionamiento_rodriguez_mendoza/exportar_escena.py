"""
Exporta la escena 3D del estacionamiento (JSON) a partir de la geometría y la
estructura del anteproyecto, para la animación y el visor interactivo.

Convención de ejes (three.js): x = u, y = altura, z = -v  (u, v: sistema local
del terreno, origen en el vértice B). Todo en metros.
"""
from __future__ import annotations

import json
import math
import os

import numpy as np
from shapely.geometry import LineString, Polygon, mapping
from shapely.ops import unary_union

import estructura as est
import geometria as g

R4 = lambda x: round(float(x), 4)


def xz(p):
    p = np.asarray(p, dtype=float)
    return [R4(p[0]), R4(-p[1])]


def xyz(p, y):
    p = np.asarray(p, dtype=float)
    return [R4(p[0]), R4(y), R4(-p[1])]


def poly_xz(poly):
    out = []
    geoms = getattr(poly, "geoms", [poly])
    for gg in geoms:
        if gg.is_empty or gg.geom_type != "Polygon":
            continue
        out.append({"ext": [xz(c) for c in list(gg.exterior.coords)[:-1]],
                    "huecos": [[xz(c) for c in list(r.coords)[:-1]] for r in gg.interiors]})
    return out


def _normal_ext(p0, p1):
    t = (p1 - p0) / np.linalg.norm(p1 - p0)
    n = np.array([-t[1], t[0]])
    c = np.array(g.LOTE.centroid.coords[0])
    if np.dot(c - p0, n) > 0:
        n = -n
    return t, n


def banda_ext(p0, p1, d0, d1, ext0=0.0, ext1=0.0):
    t, n = _normal_ext(p0, p1)
    a, b = p0 - t * ext0, p1 + t * ext1
    return Polygon([a + n * d0, b + n * d0, b + n * d1, a + n * d1])


# --------------------------------------------------------------------------
def miembros_cobertura(cob):
    """Barras de la cobertura como segmentos 3D con sección (ancho, alto)."""
    b = cob.fila.borde
    L = est.ANCHO_COB
    xc = est.BRAZO_POSTERIOR
    ch = est.CORDON.h / 1000
    dg = est.DIAGONAL.h / 1000

    def P(s, x, y):
        return xyz(b.punto(s, cob.d_atras + cob.mira_hacia * x), y)

    m = []
    ss = [s for (_, s, _) in cob.columnas]
    n = 10
    for s in ss:
        xs = [L * i / n for i in range(n + 1)]
        sup = [est.peralte_viga(x)[1] - ch / 2 for x in xs]
        inf = [est.peralte_viga(x)[2] + ch / 2 for x in xs]
        for i in range(n):
            m.append(dict(t="cordon", a=P(s, xs[i], sup[i]), b=P(s, xs[i + 1], sup[i + 1]), w=ch, h=ch))
            m.append(dict(t="cordon", a=P(s, xs[i], inf[i]), b=P(s, xs[i + 1], inf[i + 1]), w=ch, h=ch))
            if i % 2 == 0:
                m.append(dict(t="diagonal", a=P(s, xs[i], inf[i]), b=P(s, xs[i + 1], sup[i + 1]), w=dg, h=dg))
            else:
                m.append(dict(t="diagonal", a=P(s, xs[i], sup[i]), b=P(s, xs[i + 1], inf[i + 1]), w=dg, h=dg))
            m.append(dict(t="diagonal", a=P(s, xs[i + 1], inf[i + 1]), b=P(s, xs[i + 1], sup[i + 1]), w=dg, h=dg))
        m.append(dict(t="diagonal", a=P(s, 0, inf[0]), b=P(s, 0, sup[0]), w=dg, h=dg))
        # columna
        y_top = est.peralte_viga(xc)[1]
        m.append(dict(t="columna", a=P(s, xc, est.NIV_SUP_DADO + 0.025), b=P(s, xc, y_top),
                      w=est.COLUMNA.b / 1000, h=est.COLUMNA.h / 1000,
                      lado=[R4(b.n[0] * cob.mira_hacia), 0, R4(-b.n[1] * cob.mira_hacia)]))
        # cartelas (bajo el cordón inferior, a ambos lados de la columna)
        yi = est.peralte_viga(xc)[2]
        for sg in (-1, 1):
            m.append(dict(t="cartela", a=P(s, xc + sg * 0.15, yi - 0.30), b=P(s, xc + sg * 0.45, yi), w=0.01, h=0.12))
    # correas
    for i in range(est.N_CORREAS):
        x = 0.10 + i * est.SEP_CORREAS
        y = est.niv_sup_cubierta(x) - est.PERALTE_CORREA / 2
        m.append(dict(t="correa", a=P(cob.s0, x, y), b=P(cob.s1, x, y), w=0.06, h=est.PERALTE_CORREA))
    # arriostres en X (paños extremos), bajo las correas
    if len(ss) >= 2:
        for (a, c) in {(ss[0], ss[1]), (ss[-2], ss[-1])}:
            for (x0, x1) in ((0.2, L - 0.2), (L - 0.2, 0.2)):
                y0 = est.niv_sup_cubierta(x0) - est.PERALTE_CORREA - 0.02
                y1 = est.niv_sup_cubierta(x1) - est.PERALTE_CORREA - 0.02
                m.append(dict(t="tensor", a=P(a, x0, y0), b=P(c, x1, y1), w=0.013, h=0.013))
    # canaleta posterior y bajadas
    yg = est.niv_sup_cubierta(0)
    m.append(dict(t="canaleta", a=P(cob.s0, -0.12, yg - 0.11), b=P(cob.s1, -0.12, yg - 0.11), w=0.25, h=0.18))
    for s in ss:
        m.append(dict(t="bajada", a=P(s + 0.35, -0.10, yg - 0.20), b=P(s + 0.35, -0.10, 0.05), w=0.11, h=0.11))
    # fascia frontal
    yf = est.niv_sup_cubierta(L)
    m.append(dict(t="fascia", a=P(cob.s0, L + 0.01, yf - 0.08), b=P(cob.s1, L + 0.01, yf - 0.08), w=0.012, h=0.26))
    # luminarias LED bajo correas (cada 2 plazas aprox.)
    x_lum = 3.3
    y_lum = est.niv_sup_cubierta(x_lum) - est.PERALTE_CORREA - 0.05
    nl = max(1, int(round((cob.s1 - cob.s0) / 5.0)))
    for k in range(nl):
        s = cob.s0 + (k + 0.5) * (cob.s1 - cob.s0) / nl
        m.append(dict(t="luminaria", a=P(s - 0.6, x_lum, y_lum), b=P(s + 0.6, x_lum, y_lum), w=0.25, h=0.05))
    return m


def cobertura(cob):
    b = cob.fila.borde
    L = est.ANCHO_COB

    def P(s, x, y):
        return xyz(b.punto(s, cob.d_atras + cob.mira_hacia * x), y)

    y0, y1 = est.niv_sup_cubierta(0), est.niv_sup_cubierta(L)
    techo = dict(
        # esquinas: (s0, atrás), (s1, atrás), (s1, frente), (s0, frente)
        esquinas=[P(cob.s0, 0, y0), P(cob.s1, 0, y1 * 0 + y0), P(cob.s1, L, y1), P(cob.s0, L, y1)],
        dir_s=[R4(b.t[0]), 0, R4(-b.t[1])],
    )
    dados = []
    for (pt, s, d) in cob.columnas:
        dados.append(dict(centro=xyz(b.punto(s, d), est.NIV_SUP_DADO / 2), lx=est.DADO_L, lz=est.DADO_B,
                          dir_s=[R4(b.t[0]), 0, R4(-b.t[1])]))
    return dict(nombre=cob.nombre, fila=cob.fila.nombre, techo=techo, miembros=miembros_cobertura(cob), dados=dados,
                columnas=[xyz(b.punto(s, d), 0) for (_, s, d) in cob.columnas])


def plazas():
    out = []
    for p in g.PLAZAS:
        b = p.borde
        frente_pos = p.fila in ("A", "B")
        fondo_d = p.d0 if frente_pos else p.d1
        frente_d = p.d1 if frente_pos else p.d0
        sgn = 1 if frente_d > fondo_d else -1
        dirf = b.n * sgn
        sm = (p.s0 + p.s1) / 2
        tope_d = fondo_d + sgn * 1.10
        out.append(dict(
            codigo=p.codigo, fila=p.fila, tipo=p.tipo,
            esquinas=[xz(c) for c in list(p.poly.exterior.coords)[:-1]],
            centro=xz(b.punto(sm, (p.d0 + p.d1) / 2)),
            frente=[R4(dirf[0]), R4(-dirf[1])],           # vector unitario fondo -> pasillo
            ancho=R4(p.s1 - p.s0),
            fondo=xz(b.punto(sm, fondo_d)), frente_pt=xz(b.punto(sm, frente_d)),
            tope=xz(b.punto(sm, tope_d)),
            num=xz(b.punto(sm, frente_d - sgn * 0.75)),
        ))
    return out


def cerco():
    h = 2.40
    anillo = g.LOTE.difference(g.LOTE.buffer(-0.15, join_style=2))
    vanos = unary_union([seg.buffer(0.001, cap_style=2).buffer(0.40, cap_style=2, join_style=2) for seg in
                         (g.PORTON_INGRESO, g.PORTON_SALIDA, g.PUERTA_PEATONAL, g.PUERTA_PEATONAL_2)])
    vanos_x = []
    for seg in (g.PORTON_INGRESO, g.PORTON_SALIDA, g.PUERTA_PEATONAL, g.PUERTA_PEATONAL_2):
        a, c = (np.array(q) for q in seg.coords)
        t = (c - a) / np.linalg.norm(c - a)
        vanos_x.append(Polygon([a, c, c + np.array([-t[1], t[0]]) * 3, a + np.array([-t[1], t[0]]) * 3]).union(
            Polygon([a, c, c - np.array([-t[1], t[0]]) * 3, a - np.array([-t[1], t[0]]) * 3])))
    muros = anillo.difference(unary_union(vanos_x))
    # columnetas de confinamiento cada ~3.5 m en los frentes y en vanos
    columnetas = []
    for p0, p1 in ((g.A, g.B), (g.D, g.A), (g.B, g.C), (g.C, g.D)):
        L = np.linalg.norm(p1 - p0)
        t = (p1 - p0) / L
        nseg = max(1, int(round(L / 3.5)))
        for k in range(nseg + 1):
            pt = p0 + t * L * k / nseg
            c = Point_(pt)
            if unary_union(vanos_x).buffer(0.2).contains(c):
                continue
            columnetas.append(xz(pt))
    return dict(altura=h, espesor=0.15, muros=poly_xz(muros), columnetas=columnetas)


def Point_(p):
    from shapely.geometry import Point
    return Point(float(p[0]), float(p[1]))


def accesos():
    out = []
    datos = ((g.PORTON_INGRESO, "P-1", "INGRESO", "porton"), (g.PORTON_SALIDA, "P-2", "SALIDA", "porton"),
             (g.PUERTA_PEATONAL, "PP-1", "PEATONAL", "puerta"), (g.PUERTA_PEATONAL_2, "PP-2", "PEATONAL", "puerta"))
    c = np.array(g.LOTE.centroid.coords[0])
    for seg, cod, txt, tipo in datos:
        a, b = (np.array(q) for q in seg.coords)
        t = (b - a) / np.linalg.norm(b - a)
        n = np.array([-t[1], t[0]])
        if np.dot(c - a, n) < 0:
            n = -n
        # la hoja corrediza se desliza hacia el lado con muro libre
        desliza = -1 if cod == "P-1" else 1
        out.append(dict(codigo=cod, texto=txt, tipo=tipo, a=xz(a), b=xz(b), centro=xz((a + b) / 2),
                        hacia_adentro=[R4(n[0]), R4(-n[1])], dir=[R4(t[0]), R4(-t[1])], desliza=desliza,
                        ancho=R4(np.linalg.norm(b - a))))
    return out


def edificaciones():
    def caja(poly, h, nombre):
        return dict(nombre=nombre, poly=poly_xz(poly), altura=h)
    return [caja(g.GARITA, 2.50, "Garita de control"), caja(g.SSHH, 2.60, "SS.HH. accesible"),
            caja(g.DEPOSITO, 2.60, "Depósito")]


def motos():
    out = []
    for i, m in enumerate(g.MOTOS):
        cs = np.array(m.exterior.coords)[:-1]
        c = cs.mean(axis=0)
        e0, e1 = cs[1] - cs[0], cs[2] - cs[1]
        larg = e0 if np.linalg.norm(e0) > np.linalg.norm(e1) else e1
        out.append(dict(tipo="moto", centro=xz(c), dir=[R4(larg[0] / np.linalg.norm(larg)), R4(-larg[1] / np.linalg.norm(larg))]))
    for i, m in enumerate(g.MOTOTAXIS):
        cs = np.array(m.exterior.coords)[:-1]
        c = cs.mean(axis=0)
        e0, e1 = cs[1] - cs[0], cs[2] - cs[1]
        larg = e0 if np.linalg.norm(e0) > np.linalg.norm(e1) else e1
        out.append(dict(tipo="mototaxi", centro=xz(c), dir=[R4(larg[0] / np.linalg.norm(larg)), R4(-larg[1] / np.linalg.norm(larg))]))
    return out


def recorrido():
    """Trayectoria de un auto: Jr. Rodríguez de Mendoza -> calle lateral -> P-1 -> pasillos en L -> P-2 -> jirón."""
    from planos import _interseccion
    dA = (g.D_PASILLO[0] + g.D_PASILLO[1]) / 2
    p1a, p1b = (np.array(q) for q in g.PORTON_INGRESO.coords)
    p2a, p2b = (np.array(q) for q in g.PORTON_SALIDA.coords)
    m1, m2 = (p1a + p1b) / 2, (p2a + p2b) / 2
    tAB, nAB = _normal_ext(g.A, g.B)        # tAB: A -> B ; nAB: hacia la calle
    tDA, nDA = _normal_ext(g.D, g.A)        # tDA: D -> A
    tBA, tAD = -tAB, -tDA
    c_ab, c_da = 1.2 + 1.75, 1.2 + 1.5      # ejes de carril (lado del lote)
    # cruce de ejes de carril en la esquina A
    X = _interseccion(g.A + nAB * c_ab, tBA, g.A + nDA * c_da, tAD)
    pts = [g.B + nAB * c_ab - tBA * 8, g.B + nAB * c_ab + tBA * 10, X - tBA * 7, X - tBA * 2.6,
           X + (tAD - tBA) * 0.9, X + tAD * 2.8, X + tAD * 6.5]
    pts += [m1 + nDA * c_da - tAD * 4.0, m1 + nDA * 1.6 - tAD * 1.2, m1 - nDA * 0.4, m1 - nDA * 2.6]
    esq = _interseccion(g.DC.punto(0, dA), g.DC.t, g.BC.punto(0, dA), g.BC.t)
    s_esq = float(np.dot(esq - g.DC.p0, g.DC.t))
    for s in np.arange(5.0, s_esq - 4.5, 3.5):
        pts.append(g.DC.punto(float(s), dA))
    pts += [esq - g.DC.t * 4.0, esq - g.DC.t * 1.3 - g.BC.t * 1.3, esq - g.BC.t * 4.0]
    u_esq = float(np.dot(esq - g.BC.p0, g.BC.t))
    for u in np.arange(u_esq - 7.5, 10.5, -3.5):
        pts.append(g.BC.punto(float(u), dA - 0.4))
    pts += [m2 - nAB * 2.6 + tAB * 0.3, m2 - nAB * 0.3, m2 + nAB * 1.8, m2 + nAB * c_ab - tAB * 3.5,
            m2 + nAB * c_ab - tAB * 12, m2 + nAB * c_ab - tAB * 24, X - tBA * 2.0 + tBA * 14]
    return [xz(p) for p in pts]


def contexto():
    A, B, C, D = g.A, g.B, g.C, g.D
    V, CAL_AB, CAL_DA = 1.20, 7.0, 6.0
    # calzadas
    cal_ab = banda_ext(A, B, V, V + CAL_AB, ext0=45, ext1=45)
    cal_da = banda_ext(D, A, V, V + CAL_DA, ext0=50, ext1=V + CAL_AB + 2)
    calzadas = unary_union([cal_ab, cal_da])
    # veredas
    ver_lote = unary_union([banda_ext(A, B, 0, V, ext0=V, ext1=45), banda_ext(D, A, 0, V, ext0=50, ext1=V)])
    ver_op_ab = banda_ext(A, B, V + CAL_AB, V + CAL_AB + V, ext0=45, ext1=45)
    ver_op_da = banda_ext(D, A, V + CAL_DA, V + CAL_DA + V, ext0=50, ext1=V + CAL_AB)
    veredas = unary_union([ver_lote, ver_op_ab, ver_op_da]).difference(calzadas)
    # manzanas vecinas
    m_op_ab = banda_ext(A, B, V + CAL_AB + V, 45, ext0=45, ext1=45)
    m_op_da = banda_ext(D, A, V + CAL_DA + V, 40, ext0=50, ext1=0).difference(
        banda_ext(A, B, 0, V + CAL_AB + V, ext0=60, ext1=60))
    vec_bc = banda_ext(B, C, 0, 30, ext0=0, ext1=30)
    vec_cd = banda_ext(C, D, 0, 30, ext0=30, ext1=0).union(banda_ext(C, D, 0, 30, ext0=0, ext1=55))
    vecinos = unary_union([vec_bc, vec_cd]).difference(unary_union([calzadas, veredas, g.LOTE.buffer(0.01)]))
    # patio verde detrás del fondo junto a D (se ve en la imagen satelital)
    patio = banda_ext(C, D, 0, 14, ext0=-14, ext1=0).intersection(vecinos)
    return dict(
        calzadas=poly_xz(calzadas), veredas=poly_xz(veredas),
        manzana_frente_ab=poly_xz(m_op_ab.difference(calzadas)),
        manzana_frente_da=poly_xz(m_op_da.difference(calzadas)),
        vecinos=poly_xz(vecinos.difference(patio)), patio_verde_fondo=poly_xz(patio),
        nombres_calles=[
            dict(nombre="Jr. Rodríguez de Mendoza", centro=xz((A + B) / 2 + _normal_ext(A, B)[1] * (V + CAL_AB / 2)),
                 dir=[R4(_normal_ext(A, B)[0][0]), R4(-_normal_ext(A, B)[0][1])]),
            dict(nombre="Calle lateral", centro=xz((D + A) / 2 + _normal_ext(D, A)[1] * (V + CAL_DA / 2)),
                 dir=[R4(_normal_ext(D, A)[0][0]), R4(-_normal_ext(D, A)[0][1])]),
        ],
        ancho_vereda=V, ancho_calzada_ab=CAL_AB, ancho_calzada_da=CAL_DA,
    )


def flechas():
    dA = (g.D_PASILLO[0] + g.D_PASILLO[1]) / 2
    out = []
    for s in (4.0, 13.0):
        out.append(dict(pos=xz(g.DC.punto(s, dA)), dir=[R4(g.DC.t[0]), R4(-g.DC.t[1])]))
    for u in (22.5, 15.0):
        out.append(dict(pos=xz(g.BC.punto(u, dA)), dir=[R4(-g.BC.t[0]), R4(g.BC.t[1])]))
    return out


def exportar(ruta):
    r = g.resumen()
    escena = dict(
        meta=dict(proyecto="Estacionamiento vehicular techado", ubicacion="Jr. Rodríguez de Mendoza, Mendoza (Amazonas)",
                  convencion="x = u, y = altura, z = -v (m); origen en el vértice B",
                  norte=[R4(g.NORTE[0]), R4(-g.NORTE[1])], resumen={k: (R4(v) if isinstance(v, float) else v)
                                                                   for k, v in r.items() if k not in ("filas", "angulos")}),
        lote=[xz(p) for p in (g.A, g.B, g.C, g.D)], vertices={k: xz(v) for k, v in g.VERT.items()},
        piso_util=poly_xz(g.UTIL), circulacion=poly_xz(g.CIRCULACION), zona_interior=poly_xz(g.ZONA_INTERIOR),
        paso_motos=poly_xz(g.PASO_MOTO),
        plazas=plazas(), coberturas=[cobertura(c) for c in g.COBERTURAS], cerco=cerco(), accesos=accesos(),
        edificaciones=edificaciones(), motos=motos(), recorrido=recorrido(), flechas=flechas(), contexto=contexto(),
        niveles=dict(fondo_cubierta=est.NIV_FONDO_COB, frente_cubierta=R4(est.niv_sup_cubierta(est.ANCHO_COB)),
                     galibo=est.NIV_INF_VIGA_COL, pendiente=est.PENDIENTE),
    )
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(escena, f, ensure_ascii=False, separators=(",", ":"))
    return ruta, escena


if __name__ == "__main__":
    import sys
    ruta, e = exportar(sys.argv[1] if len(sys.argv) > 1 else "animacion_3d/web/escena.json")
    print(ruta, os.path.getsize(ruta) // 1024, "KB")
    print("plazas", len(e["plazas"]), "coberturas", len(e["coberturas"]),
          "miembros", sum(len(c["miembros"]) for c in e["coberturas"]), "muros", len(e["cerco"]["muros"]),
          "recorrido", len(e["recorrido"]))
