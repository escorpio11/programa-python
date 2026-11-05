"""
Láminas del anteproyecto (PDF A3) del estacionamiento techado.

    L-01  Plano perimétrico y de ubicación
    A-01  Distribución general, circulación y señalización
    A-02  Planta de techos y cortes
    E-01  Cimentación y columnas
    E-02  Estructura de techo (vigas, correas, arriostres)
    E-03  Pórtico típico, conexiones y especificaciones
    E-04  Detalles de cimentación
"""
from __future__ import annotations

import math
import os

import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Polygon as MplPolygon, Rectangle, Arc
from shapely.geometry import Polygon, LineString, Point
from shapely.ops import unary_union

import geometria as g
import estructura as est
from dibujo import (Hoja, Vista, corte_marca, LW, GRIS, GRIS_CLARO, AZUL, ROJO, VERDE, F_CIRC, F_ACC, F_MOTO,
                    F_SERV, F_VERDE, F_TECHO, pt)

TOTAL_LAMINAS = 7
ESC_PLANTA = 150
ORIGEN_PLANTA = (-3.6, -2.2)          # punto del terreno (m) que cae en (X0, Y0) de la hoja
X0, Y0 = 11.5, 34.0
S_CORTE_A = 6.1      # a lo largo de C-D (atraviesa filas A y D)
U_CORTE_B = 16.6     # a lo largo de B-C (atraviesa filas B y C)


# ==========================================================================
# Elementos comunes de planta
# ==========================================================================
def _offset_linea(p0, p1, d):
    t = (p1 - p0) / np.linalg.norm(p1 - p0)
    n = np.array([-t[1], t[0]])
    c = np.array(g.LOTE.centroid.coords[0])
    if np.dot(c - p0, n) > 0:      # n apunta hacia fuera
        n = -n
    return p0 + n * d, p1 + n * d, t, n


def _interseccion(p, r, q, s):
    m = np.array([r, -s]).T
    k = np.linalg.solve(m, q - p)
    return p + k[0] * r


def dibujar_entorno(v: Vista, rotular=True, ancho_vereda=1.20, ancho_via=3.2):
    """Veredas y vías (referenciales) en los frentes AB y DA, colindantes en BC y CD."""
    A, B, C, D = g.A, g.B, g.C, g.D
    # frente AB
    a1, b1, tAB, nAB = _offset_linea(A, B, ancho_vereda)
    a2, b2, _, _ = _offset_linea(A, B, ancho_vereda + ancho_via)
    # frente DA
    d1, e1, tDA, nDA = _offset_linea(D, A, ancho_vereda)
    d2, e2, _, _ = _offset_linea(D, A, ancho_vereda + ancho_via)
    # esquina (intersección de bordes de vereda)
    esq1 = _interseccion(a1, tAB, e1, tDA)
    esq2 = _interseccion(a2, tAB, e2, tDA)
    ext = 2.0
    # bordes de vereda / sardinel
    v.linea([b1 + tAB * ext, esq1], lw="fino", color=GRIS)
    v.linea([esq1, d1 - tDA * ext], lw="fino", color=GRIS)
    # borde exterior (eje referencial de vía)
    v.linea([b2 + tAB * ext, esq2], lw="fino", color=GRIS, ls=(0, (6, 3)))
    v.linea([esq2, d2 - tDA * ext], lw="fino", color=GRIS, ls=(0, (6, 3)))
    # prolongación del límite de vereda más allá del lote
    v.linea([B, B + tAB * ext], lw="fino", color=GRIS)
    v.linea([D, D - tDA * ext], lw="fino", color=GRIS)
    if rotular:
        mAB = (a2 + b2) / 2 + nAB * 1.2 - tAB * 2.0
        v.texto_a_lo_largo(a2 - tAB * 8 + nAB * 1.0, b2 + tAB * 8 + nAB * 1.0, "JR. RODRÍGUEZ DE MENDOZA",
                           h=2.6, weight="bold")
        v.texto_a_lo_largo(a1, b1, "VEREDA", h=1.4, color=GRIS, offset_mm=0)
        v.texto_a_lo_largo(d2 + nDA * 1.0, e2 + nDA * 1.0, "CALLE LATERAL (S/N)", h=2.6, weight="bold")
        v.texto_a_lo_largo(d1, e1, "VEREDA", h=1.4, color=GRIS)
        # colindantes
        for p0, p1, t in ((B, C, "PROPIEDAD DE TERCEROS - EDIFICACIONES EXISTENTES"),
                          (C, D, "PROPIEDAD DE TERCEROS")):
            q0, q1, tt, nn = _offset_linea(p0, p1, 1.3 if p0 is B else 0.95)
            v.texto_a_lo_largo(q0, q1, t, h=1.6, color=GRIS)
    # achurado colindantes
    for p0, p1 in ((B, C), (C, D)):
        q0, q1, tt, nn = _offset_linea(p0, p1, 0.6)
        franja = Polygon([p0, p1, q1, q0])
        v.poly(franja, fc="none", ec="none", hatch="////", hatch_color=GRIS_CLARO, lw="fino", z=1)


def dibujar_lote(v: Vista, grosor_cerco=0.15, cerco=True, lw="grueso"):
    v.poly(g.LOTE, fc="none", ec="k", lw=lw, z=4)
    if cerco:
        interior = g.LOTE.buffer(-grosor_cerco, join_style=2)
        v.poly(interior, fc="none", ec="k", lw="fino", z=4)
        anillo = g.LOTE.difference(interior)
        v.poly(anillo, fc="#9e9e9e", ec="none", z=3)
        # vanos
        for seg in (g.PORTON_INGRESO, g.PORTON_SALIDA, g.PUERTA_PEATONAL, g.PUERTA_PEATONAL_2):
            vano = seg.buffer(0.30, cap_style=2).intersection(anillo.buffer(0.01))
            v.poly(vano, fc="white", ec="none", z=3.5)


def dibujar_portones(v: Vista, rotular=True):
    for seg, nombre, txt in ((g.PORTON_INGRESO, "P-1", "INGRESO"), (g.PORTON_SALIDA, "P-2", "SALIDA")):
        p0, p1 = (np.array(c) for c in seg.coords)
        t = (p1 - p0) / np.linalg.norm(p1 - p0)
        n = np.array([-t[1], t[0]])
        c = np.array(g.LOTE.centroid.coords[0])
        if np.dot(c - p0, n) < 0:
            n = -n
        # hoja corrediza (dibujada en posición abierta, desplazada hacia el interior)
        q0, q1 = p0 + n * 0.30, p1 + n * 0.30
        v.linea([q0, q1], lw="mgrueso", color="k", z=6)
        v.linea([q1, q1 + t * 0.6], lw="fino", color="k", z=6)
        v.flecha_simple(q0 + t * 0.8 + n * 0.25, q1 - t * 0.6 + n * 0.25, lw="fino", cab=1.2)
        if rotular:
            v.texto_a_lo_largo(p0 - n * 2.0, p1 - n * 2.0, f"{nombre}  {txt}", h=2.0, weight="bold", color=VERDE if nombre == "P-1" else ROJO)
            v.texto_a_lo_largo(p0 - n * 2.75, p1 - n * 2.75, "portón corredizo, ancho libre 3.00 m", h=1.25)
    for seg, nombre in ((g.PUERTA_PEATONAL, "PP-1"), (g.PUERTA_PEATONAL_2, "PP-2")):
        p0, p1 = (np.array(c) for c in seg.coords)
        t = (p1 - p0) / np.linalg.norm(p1 - p0)
        n = np.array([-t[1], t[0]])
        c = np.array(g.LOTE.centroid.coords[0])
        if np.dot(c - p0, n) < 0:
            n = -n
        L = np.linalg.norm(p1 - p0)
        hoja_end = p0 + n * L
        v.linea([p0, hoja_end], lw="medio", z=6)
        # arco de apertura
        ang0 = math.degrees(math.atan2(t[1], t[0]))
        ang1 = math.degrees(math.atan2(n[1], n[0]))
        q = v.T(p0)
        r = L * v.k
        a0, a1 = sorted([ang0, ang1])
        if a1 - a0 > 180:
            a0, a1 = a1, a0 + 360
        v.ax.add_patch(Arc(q, 2 * r, 2 * r, theta1=a0, theta2=a1, lw=LW["fino"], color="k", zorder=6))
        if rotular:
            m = (p0 + p1) / 2 - n * 1.3
            v.texto(m, nombre, h=1.5, weight="bold")


def dibujar_plazas(v: Vista, numerar=True, topes=True, tenue=False):
    col = GRIS_CLARO if tenue else "k"
    for p in g.PLAZAS:
        fc = "none" if tenue else (F_ACC if p.tipo == "accesible" else "white")
        v.poly(p.poly, fc=fc, ec=col, lw="fino" if tenue else "medio", z=2)
        b = p.borde
        fondo_d = p.d0 if p.fila in ("A", "B") else p.d1
        frente_d = p.d1 if p.fila in ("A", "B") else p.d0
        sgn = 1 if frente_d > fondo_d else -1
        if topes and not tenue:
            dd = fondo_d + sgn * 1.10
            w = p.s1 - p.s0
            v.poly(b.rect(p.s0 + w / 2 - 0.80, p.s0 + w / 2 + 0.80, min(dd, dd + sgn * 0.15),
                          max(dd, dd + sgn * 0.15)), fc="#555555", ec="none", z=3)
        if numerar:
            centro = b.punto((p.s0 + p.s1) / 2, (fondo_d + frente_d) / 2 + sgn * 0.6)
            v.texto(centro, p.codigo, h=2.2 if not tenue else 1.6, weight="bold", color=col)
            if p.tipo == "accesible" and not tenue:
                v.texto(b.punto((p.s0 + p.s1) / 2, (fondo_d + frente_d) / 2 - sgn * 0.9), "♿", h=3.4,
                        color=AZUL, fontfamily="DejaVu Sans")
                # franja de transferencia rayada (1.20 m) en el lado derecho
                zona = b.rect(p.s1 - 1.20, p.s1, min(fondo_d, frente_d), max(fondo_d, frente_d))
                v.poly(zona, fc="none", ec="none", hatch="\\\\\\\\", hatch_color=AZUL, z=2.5)


def dibujar_coberturas(v: Vista, rotular=True, color=AZUL, ls=(0, (5, 2)), lw="medio", relleno=None):
    for cob in g.COBERTURAS:
        v.poly(cob.poly, fc=relleno or "none", ec=color, lw=lw, ls=ls, z=4 if relleno is None else 1.5,
               alpha=1.0)
        if rotular:
            b = cob.fila.borde
            frente = cob.fila.d1 if cob.mira_hacia > 0 else cob.fila.d0
            d_txt = (frente + cob.d_frente) / 2
            for s in (cob.s0 + 1.25, cob.s1 - 1.25):
                v.texto(b.punto(s, d_txt), cob.nombre, h=1.6, color=color, weight="bold", ang=_ang_borde(v, b))


def _ang_borde(v, b):
    q0, q1 = v.T(b.p0), v.T(b.p1)
    d = q1 - q0
    ang = math.degrees(math.atan2(d[1], d[0]))
    if ang > 90:
        ang -= 180
    elif ang <= -90:
        ang += 180
    return ang


def dibujar_columnas(v: Vista, rotular=False, tam=None, z=8):
    sec = est.COLUMNA
    for i, (cob, n, pt_) in enumerate(g.COLUMNAS):
        cobj = next(c for c in g.COBERTURAS if c.nombre == cob)
        b = cobj.fila.borde
        c = np.array(pt_.coords[0])
        h, bb = sec.h / 1000, sec.b / 1000
        t, nn = b.t, b.n
        pts = [c + t * bb / 2 + nn * h / 2, c - t * bb / 2 + nn * h / 2, c - t * bb / 2 - nn * h / 2,
               c + t * bb / 2 - nn * h / 2]
        v.poly(Polygon(pts), fc="k", ec="k", lw="fino", z=z)


def etiquetas_columnas():
    """Código de cada columna: C-01 ... en el orden de las coberturas."""
    etiquetas = []
    k = 1
    for cob in g.COBERTURAS:
        for (pt_, s, d) in cob.columnas:
            etiquetas.append((f"C-{k:02d}", cob, np.array(pt_.coords[0])))
            k += 1
    return etiquetas


def vista_planta(hoja, escala=ESC_PLANTA, x0=X0, y0=Y0, origen=ORIGEN_PLANTA):
    return hoja.vista(x0, y0, escala, origen)


def _norte(v, xy=(296, 262)):
    v.norte(xy, g.NORTE, largo=13)


# ==========================================================================
# L-01  Perimétrico y ubicación
# ==========================================================================
def lamina_L01(pdf, png_dir):
    h = Hoja("L-01", "PLANO PERIMÉTRICO", "ARQUITECTURA", "INDICADA", 1, TOTAL_LAMINAS,
             subtitulo="Y DE UBICACIÓN")
    v = vista_planta(h)
    dibujar_entorno(v)
    dibujar_lote(v, cerco=False, lw="mgrueso")
    A, B, C, D = g.A, g.B, g.C, g.D
    # diagonales de control
    v.linea([A, C], lw="fino", color=GRIS, ls=(0, (4, 3)))
    v.linea([B, D], lw="fino", color=GRIS, ls=(0, (4, 3)))
    v.texto_a_lo_largo(A + (C - A) * 0.55, A + (C - A) * 0.95,
                       f"diagonal A-C = {np.linalg.norm(A - C):.2f} m (verificar en campo)", h=1.5, color=GRIS,
                       offset_mm=1.6)
    v.texto_a_lo_largo(B + (D - B) * 0.05, B + (D - B) * 0.42,
                       f"diagonal B-D = {np.linalg.norm(B - D):.2f} m (verificar en campo)", h=1.5, color=GRIS,
                       offset_mm=1.6)
    # vértices y ángulos
    c = np.array(g.LOTE.centroid.coords[0])
    for k, p_ in g.VERT.items():
        dirc = (p_ - c) / np.linalg.norm(p_ - c)
        v.marca_eje(p_ + dirc * 1.5, k, r_mm=2.8, h=2.2)
        v.texto(p_ - dirc * 2.6, f"{g.ANGULOS[k]:.1f}°", h=1.9, color=ROJO)
    # cotas de lados (exteriores)
    v.cota(A, B, offset_mm=26, lado=-1, texto="30.00", h=2.4)
    v.cota(B, C, offset_mm=16, lado=-1, texto="40.00", h=2.4)
    v.cota(C, D, offset_mm=12, lado=-1, texto="30.00", h=2.4)
    v.cota(D, A, offset_mm=40, lado=-1, texto="20.00", h=2.4)
    # área
    pc = c + np.array([1.0, -3.0])
    caja = dict(fc="white", ec="none", pad=1.5)
    v.texto(pc + np.array([0, 2.6]), "ÁREA DEL TERRENO", h=2.6, weight="bold", bbox=caja)
    v.texto(pc, f"{g.LOTE.area:,.2f} m²", h=4.0, weight="bold", bbox=caja)
    v.texto(pc + np.array([0, -2.6]), f"PERÍMETRO = {g.LOTE.length:.2f} ml", h=2.0, bbox=caja)
    _norte(v)
    v.escala_grafica((215, 20), metros=10, paso=2)
    h.titulo_vista(80, 23, "PLANO PERIMÉTRICO", "ESC. 1/150")

    # Cuadro de datos técnicos
    filas = []
    orden = ["A", "B", "C", "D"]
    for i, k in enumerate(orden):
        sig = orden[(i + 1) % 4]
        p_, q = g.VERT[k], g.VERT[sig]
        filas.append([k, f"{k}-{sig}", f"{np.linalg.norm(q - p_):.2f}", f"{g.ANGULOS[k]:.1f}°",
                      f"{p_[0]:.2f}", f"{p_[1]:.2f}"])
    yb = h.tabla(h.x_franja + 2.5, 280, ["VÉRT.", "LADO", "DIST. (m)", "ÁNGULO", "u (m)", "v (m)"], filas,
                 [10, 12, 15, 15, 16, 17], h_fila=4.6, h_txt=1.7, titulo="CUADRO DE DATOS TÉCNICOS",
                 alinear=["c", "c", "r", "r", "r", "r"])
    h.texto(h.x_franja + 2.5, yb - 3, f"Área = {g.LOTE.area:,.2f} m²     Perímetro = {g.LOTE.length:.2f} ml", h=1.8,
            weight="bold")
    h.texto(h.x_franja + 2.5, yb - 7, "Coordenadas locales: origen en B, eje u sobre el lindero B-C.", h=1.5)
    yb = h.tabla(h.x_franja + 2.5, yb - 15, ["LINDERO", "COLINDA CON", "LONG."],
                 [["Frente (A-B)", "Jr. Rodríguez de Mendoza", "30.00"],
                  ["Izquierda (D-A)", "Calle lateral", "20.00"],
                  ["Derecha (B-C)", "Prop. de terceros (edif.)", "40.00"],
                  ["Fondo (C-D)", "Prop. de terceros", "30.00"]],
                 [24, 46, 15], h_fila=4.4, h_txt=1.6, titulo="COLINDANCIAS", alinear=["l", "l", "r"])
    notas = [
        "1. Lados medidos por el propietario con la herramienta de medición de Google Maps (precisión aprox. ±0.5 a ±1.0 m).",
        "2. Ángulos reconstruidos de la imagen satelital (A ≈ 130°); coherentes con las 4 capturas.",
        "3. ANTES DE CONSTRUIR: levantamiento topográfico y control de diagonales A-C y B-D. Si difieren más de 0.50 m, actualizar la distribución.",
        "4. Verificar en la Municipalidad Provincial: retiro municipal, ochavo en esquina A y parámetros urbanísticos.",
        "5. Norte referencial según imagen satelital.",
    ]
    yb = h.notas(yb - 8, "NOTAS", notas, h=1.5, ancho_chars=62)

    # Esquema de localización (en la franja derecha)
    xs, ys, ws, hs = h.x_franja + 2.5, h.y_cajetin_top + 4, 86, yb - h.y_cajetin_top - 14
    h.ax.add_patch(Rectangle((xs, ys), ws, hs, fill=False, lw=LW["medio"]))
    h.texto(xs, ys + hs + 2.5, "ESQUEMA DE LOCALIZACIÓN (S/E)", h=2.0, weight="bold")
    esc_l = 900
    vl = h.vista(xs + ws / 2, ys + hs / 2, esc_l, (g.A + g.C) / 2 + np.array([-4.0, 4.0]))
    medio_x = ws / 2 / vl.k
    medio_y = hs / 2 / vl.k
    marco = Polygon([vl.o + np.array(q) for q in [(-medio_x, -medio_y), (medio_x, -medio_y), (medio_x, medio_y),
                                                  (-medio_x, medio_y)]]).buffer(-0.5)
    tBA = (A - B) / np.linalg.norm(A - B)
    tAD = (D - A) / np.linalg.norm(D - A)
    nAB = np.array([tBA[1], -tBA[0]])
    nDA = np.array([-tAD[1], tAD[0]])
    via1 = LineString([B - tBA * 60 - nAB * 5.2, A + tBA * 60 - nAB * 5.2]).buffer(4.0, cap_style=2)
    via2 = LineString([A + nDA * 5.0 - tAD * 5, D + tAD * 60 + nDA * 5.0]).buffer(3.0, cap_style=2)
    vl.poly(unary_union([via1, via2]).intersection(marco), fc="#e3e3e3", ec=GRIS, lw="fino")
    # manzanas vecinas (esquemáticas)
    vl.poly(g.LOTE, fc="#c62828", ec="k", lw="fino", alpha=0.9)
    vl.texto(np.array(g.LOTE.centroid.coords[0]), "TERRENO", h=1.6, weight="bold", color="white")
    vl.texto_a_lo_largo(B - tBA * 10 - nAB * 5.2, A + tBA * 10 - nAB * 5.2, "JR. RODRÍGUEZ DE MENDOZA", h=1.4)
    vl.texto_a_lo_largo(D + tAD * 4 + nDA * 5.0, D + tAD * 24 + nDA * 5.0, "CALLE LATERAL", h=1.3)
    vl.norte((xs + ws - 9, ys + 12), g.NORTE, largo=8)
    h.texto(xs + 2, ys + 3, "Mendoza (San Nicolás) - Rodríguez de Mendoza - Amazonas", h=1.4, color=GRIS)
    h.guardar(pdf, os.path.join(png_dir, "L-01.png") if png_dir else None)


# ==========================================================================
# A-01  Distribución general
# ==========================================================================
def _flechas_circulacion(v: Vista):
    dA = (g.D_PASILLO[0] + g.D_PASILLO[1]) / 2
    esq = _interseccion(g.DC.punto(0, dA), g.DC.t, g.BC.punto(0, dA), g.BC.t)
    s_esq = float(np.dot(esq - g.DC.p0, g.DC.t))
    u_esq = float(np.dot(esq - g.BC.p0, g.BC.t))
    for a, b in ((1.4, 7.0), (10.5, 16.5), (19.0, s_esq - 1.0)):
        v.flecha(g.DC.punto(a, dA), g.DC.punto(b, dA), ancho_mm=5.0)
    for a, b in ((u_esq - 1.0, u_esq - 6.5), (u_esq - 9.0, 15.2), (13.6, 8.6)):
        v.flecha(g.BC.punto(a, dA), g.BC.punto(b, dA), ancho_mm=5.0)
    v.texto_a_lo_largo(g.DC.punto(8.0, dA - 2.0), g.DC.punto(14.0, dA - 2.0), "CIRCULACIÓN - SENTIDO ÚNICO",
                       h=1.6, color=AZUL, weight="bold")
    v.texto_a_lo_largo(g.BC.punto(24.0, dA + 2.0), g.BC.punto(16.0, dA + 2.0), "CIRCULACIÓN - SENTIDO ÚNICO",
                       h=1.6, color=AZUL, weight="bold")
    # velocidad máxima
    v.circulo(g.DC.punto(8.6, dA + 2.0), 2.6, fc="white", ec=ROJO, lw="grueso")
    v.texto(g.DC.punto(8.6, dA + 2.0), "10", h=1.8, weight="bold")
    # PARE en la salida
    q = v.T(g.BC.punto(12.6, dA - 2.0))
    oct_ = [(q[0] + 2.6 * math.cos(math.radians(22.5 + 45 * i)), q[1] + 2.6 * math.sin(math.radians(22.5 + 45 * i)))
            for i in range(8)]
    v.ax.add_patch(MplPolygon(oct_, closed=True, fc=ROJO, ec="k", lw=LW["fino"], zorder=7))
    v.ax.text(q[0], q[1], "PARE", fontsize=pt(1.3), color="white", ha="center", va="center", weight="bold",
              zorder=8)


def _cotas_A01(v: Vista):
    b = g.BC
    # cotas generales de franjas (perpendiculares a B-C) en la zona de la fila B / pasillo / fila C
    s = 22.0
    for (d0, d1) in ((0.0, g.D_FILA_EXT[0]), g.D_FILA_EXT, g.D_PASILLO, g.D_FILA_INT):
        v.cota(b.punto(s, d0), b.punto(s, d1), offset_mm=0, ext=False, h=1.6,
               texto=f"{d1 - d0:.2f}", lado=-1)
    # a lo largo del fondo (fila A)
    dc = g.DC
    s = 12.75
    for (d0, d1) in (g.D_FILA_EXT, g.D_PASILLO):
        v.cota(dc.punto(s, d0), dc.punto(s, d1), offset_mm=0, ext=False, h=1.6, texto=f"{d1 - d0:.2f}",
               lado=1)
    # anchos típicos de plazas
    fA = g.FILA_A.plazas
    for p in fA[4:6]:
        v.cota(dc.punto(p.s0, p.d1), dc.punto(p.s1, p.d1), offset_mm=2.5, lado=-1, h=1.5)
    fB = g.FILA_B.plazas
    for p in fB[:3]:
        v.cota(b.punto(p.s0, 0.25), b.punto(p.s1, 0.25), offset_mm=5, lado=-1, h=1.5)
    # portones (posición)
    v.cota(g.D, np.array(g.PORTON_INGRESO.coords[0]), offset_mm=5.5, lado=-1, h=1.5)
    v.cota(np.array(g.PORTON_INGRESO.coords[0]), np.array(g.PORTON_INGRESO.coords[1]), offset_mm=5.5, lado=-1,
           h=1.5)
    v.cota(g.B, np.array(g.PORTON_SALIDA.coords[0]), offset_mm=5.5, lado=1, h=1.5)
    v.cota(np.array(g.PORTON_SALIDA.coords[0]), np.array(g.PORTON_SALIDA.coords[1]), offset_mm=5.5, lado=1,
           h=1.5)
    # lados generales
    v.cota(g.A, g.B, offset_mm=26, lado=-1, texto="30.00", h=2.0)
    v.cota(g.B, g.C, offset_mm=16, lado=-1, texto="40.00", h=2.0)
    v.cota(g.C, g.D, offset_mm=12, lado=-1, texto="30.00", h=2.0)
    v.cota(g.D, g.A, offset_mm=40, lado=-1, texto="20.00", h=2.0)


def lamina_A01(pdf, png_dir):
    h = Hoja("A-01", "DISTRIBUCIÓN GENERAL", "ARQUITECTURA", "1/150", 2, TOTAL_LAMINAS,
             subtitulo="CIRCULACIÓN Y SEÑALIZACIÓN")
    v = vista_planta(h)
    dibujar_entorno(v)
    # superficies
    v.poly(g.CIRCULACION, fc=F_CIRC, ec="none", z=1)
    v.poly(g.ZONA_INTERIOR, fc=F_VERDE, ec="none", z=1)
    for m in g.MOTOS:
        v.poly(m, fc=F_MOTO, ec="k", lw="fino", z=2)
    for i, m in enumerate(g.MOTOS):
        v.texto(np.array(m.centroid.coords[0]), f"M{i + 1}", h=1.2, ang=_ang_borde(v, g.DC) + 90)
    for i, m in enumerate(g.MOTOTAXIS):
        v.poly(m, fc=F_MOTO, ec="k", lw="fino", z=2)
        v.texto(np.array(m.centroid.coords[0]), f"MT{i + 1}", h=1.3, ang=90)
    v.poly(g.PASO_MOTO, fc="none", ec="none", hatch="..", hatch_color=GRIS, z=1.5)
    v.texto(np.array(g.PASO_MOTO.centroid.coords[0]), "PASO MOTOS\n/ PEATONAL", h=1.2, ang=_ang_borde(v, g.DC) + 90)
    # bolardos en el paso de motos
    for s in np.linspace(g.FRANJA_MURO + 0.5, g.FILA_D.s_ini - 0.5, 2):
        v.circulo(g.DC.punto(s, g.D_FILA_INT[0] + 0.15), 0.6, fc="k")
    # servicios
    v.poly(g.SSHH, fc=F_SERV, ec="k", lw="grueso", z=3)
    v.poly(g.DEPOSITO, fc=F_SERV, ec="k", lw="grueso", z=3)
    v.texto(np.array(g.SSHH.centroid.coords[0]), "SS.HH.\nACCES.", h=1.3, ang=_ang_borde(v, g.BA) + 0)
    v.texto(np.array(g.DEPOSITO.centroid.coords[0]), "DEP.", h=1.3, ang=_ang_borde(v, g.BA))
    v.poly(g.GARITA, fc=F_SERV, ec="k", lw="grueso", z=3)
    v.texto(np.array(g.GARITA.centroid.coords[0]), "GARITA", h=1.1)
    gar_c = np.array(g.GARITA.centroid.coords[0])
    # jardinera en la punta de la isla
    punta = (g.UTIL.intersection(g.banda(g.BC, g.D_FILA_INT[0] + 0.0, g.D_FILA_INT[1]))
             .difference(unary_union([p.poly for p in g.FILA_C.plazas]).buffer(0.3, join_style=2))
             .difference(g.CIRCULACION))
    punta = min(getattr(punta, "geoms", [punta]), key=lambda x: x.centroid.x)
    v.poly(punta, fc=F_VERDE, ec=VERDE, lw="fino", z=2)
    v.texto(np.array(punta.centroid.coords[0]) + np.array([-0.3, -0.6]), "JARD.", h=1.1, color=VERDE)

    dibujar_coberturas(v)
    dibujar_plazas(v)
    dibujar_columnas(v)
    dibujar_lote(v)
    dibujar_portones(v)
    _flechas_circulacion(v)
    _cotas_A01(v)
    # rótulos de filas
    for fila, txt, d in ((g.FILA_A, "FILA A", -0.0), (g.FILA_B, "FILA B", 0), (g.FILA_C, "FILA C", 0),
                         (g.FILA_D, "FILA D", 0)):
        pass
    # cortes
    corte_marca(v, g.DC.punto(S_CORTE_A, -1.0), g.DC.punto(S_CORTE_A, g.D_FILA_INT[1] + 0.5), "A", lado=1)
    corte_marca(v, g.BC.punto(U_CORTE_B, -1.0), g.BC.punto(U_CORTE_B, g.D_FILA_INT[1] + 1.2), "B", lado=1)
    _norte(v)
    v.escala_grafica((215, 20), metros=10, paso=2)
    h.titulo_vista(80, 23, "PLANTA DE DISTRIBUCIÓN GENERAL", "ESC. 1/150")

    # ---- franja derecha: cuadros y leyenda
    r = g.resumen()
    x = h.x_franja + 2.5
    filas = [["Plazas autos estándar 2.50 x 5.00 m (techadas)", f"{r['plazas_estandar']}"],
             ["Plazas accesibles 3.80 x 5.00 m (techadas)", f"{r['plazas_accesibles']}"],
             ["TOTAL PLAZAS VEHICULARES TECHADAS", f"{r['plazas_total']}"],
             ["Motos 1.00 x 2.20 m", f"{r['motos']}"],
             ["Mototaxis 1.50 x 3.00 m", f"{r['mototaxis']}"]]
    yb = h.tabla(x, 280, ["DESCRIPCIÓN", "CANT."], filas, [72, 14], h_fila=4.3, h_txt=1.6,
                 titulo="CUADRO DE ESTACIONAMIENTOS", alinear=["l", "r"])
    area_serv = g.SSHH.area + g.DEPOSITO.area + g.GARITA.area
    filas = [["Área del terreno", f"{r['area_lote']:.2f}"],
             ["Área techada (coberturas T-1 a T-4)", f"{r['area_techada']:.2f}"],
             ["Plazas vehiculares", f"{r['area_plazas']:.2f}"],
             ["Circulación vehicular", f"{r['area_circulacion']:.2f}"],
             ["Servicios (garita, SS.HH., depósito)", f"{area_serv:.2f}"],
             ["Zona motos / jardines / franjas", f"{r['area_lote'] - r['area_plazas'] - r['area_circulacion'] - area_serv:.2f}"]]
    yb = h.tabla(x, yb - 9, ["ÁREAS", "m²"], filas, [72, 14], h_fila=4.3, h_txt=1.6, titulo="CUADRO DE ÁREAS",
                 alinear=["l", "r"])
    # leyenda
    y = yb - 9
    h.texto(x, y + 1, "LEYENDA", h=2.0, weight="bold", va="bottom")
    items = [("rect", F_CIRC, "Circulación vehicular (sentido único)"),
             ("rect", F_ACC, "Plaza accesible (RNE A.120)"),
             ("dash", AZUL, "Proyección de cobertura metálica T-1...T-4"),
             ("col", "k", f"Columna metálica {est.COLUMNA.nombre}"),
             ("tope", "#555555", "Tope de llantas (concreto prefabricado)"),
             ("rect", F_MOTO, "Motos / mototaxis"),
             ("rect", F_SERV, "Garita, SS.HH. y depósito"),
             ("rect", F_VERDE, "Zona peatonal / jardín")]
    for i, (tipo, col, txt) in enumerate(items):
        yy = y - 3.0 - i * 4.0
        if tipo == "rect":
            h.ax.add_patch(Rectangle((x, yy - 1.3), 7, 2.6, fc=col, ec="k", lw=LW["fino"]))
        elif tipo == "dash":
            h.ax.plot([x, x + 7], [yy, yy], color=col, lw=LW["medio"], ls=(0, (5, 2)))
        elif tipo == "col":
            h.ax.add_patch(Rectangle((x + 2.5, yy - 1.0), 2.0, 2.0, fc="k"))
        elif tipo == "tope":
            h.ax.add_patch(Rectangle((x + 0.5, yy - 0.4), 6, 0.8, fc=col))
        h.texto(x + 9, yy, txt, h=1.55)
    y = y - 3.0 - len(items) * 4.0 - 2
    notas = [
        "1. Cotas en metros. Plazas según RNE A.010 (uso público) y A.120 (accesibilidad). Distancia entre plazas opuestas 6.50 m (criterio conservador).",
        "2. Circulación en sentido único: INGRESO por P-1 (calle lateral) y SALIDA por P-2 (Jr. Rodríguez de Mendoza). Las colas de ingreso quedan en la vía de menor tránsito.",
        "3. Gálibo libre mínimo bajo estructura: 2.80 m (camionetas pick-up y minivans).",
        "4. Pendiente de piso 1.0 % a 1.5 % hacia canaletas con rejilla; descarga a la vía pública.",
        "5. Señalización: pintura de tráfico amarilla (líneas de 0.10 m), flechas, numeración, PARE en salida, espejo convexo y velocidad máx. 10 km/h.",
    ]
    h.notas(y, "NOTAS", notas, h=1.45, ancho_chars=62)
    h.guardar(pdf, os.path.join(png_dir, "A-01.png") if png_dir else None)


# ==========================================================================
# A-02  Techos y cortes
# ==========================================================================
def _silueta_camioneta(L=5.30, H=1.82, invertir=False):
    """Perfil lateral simplificado de una camioneta pick-up (origen: parachoques posterior, suelo)."""
    pts = [(0, 0.35), (0.05, 0.85), (0.15, 0.95), (2.05, 0.95), (2.15, 1.80), (2.40, H), (3.55, H),
           (4.25, 1.15), (5.10, 1.05), (L, 0.85), (L, 0.40), (4.70, 0.35)]
    if invertir:
        pts = [(L - x, y) for x, y in pts]
    return pts


def _dibujar_corte(h, x0, y0, escala, fila_ext, fila_int, cob_ext, cob_int, titulo, letra):
    """Corte transversal: plaza exterior - pasillo - plaza interior (coordenada d)."""
    v = h.vista(x0, y0, escala, (0, 0))
    k = v.k
    d_tot = fila_int.d1 + 0.7
    # terreno
    v.linea([(-0.8, 0), (d_tot, 0)], lw="grueso")
    v.poly(Polygon([(-0.8, 0), (d_tot, 0), (d_tot, -0.30), (-0.8, -0.30)]), fc="none", ec="none", hatch="////",
           hatch_color=GRIS_CLARO)
    # cerco perimetral
    v.poly(Polygon([(0, 0), (0.15, 0), (0.15, 2.40), (0, 2.40)]), fc="#9e9e9e", ec="k", lw="medio", z=4)
    v.texto((0.07, 2.62), "CERCO", h=1.2)

    def cobertura(d_atras, d_frente, d_col, sentido):
        # sentido: +1 si el frente está a mayor d
        L = abs(d_frente - d_atras)

        def X(x):  # x desde el borde posterior
            return d_atras + sentido * x
        xs = np.linspace(0, L, 41)
        sup = [est.niv_sup_cubierta(x) for x in xs]
        top = [est.peralte_viga(x)[1] for x in xs]
        inf = [est.peralte_viga(x)[2] for x in xs]
        v.linea([(X(x), y) for x, y in zip(xs, sup)], lw="grueso", color=AZUL)
        v.linea([(X(x), y) for x, y in zip(xs, top)], lw="medio")
        v.linea([(X(x), y) for x, y in zip(xs, inf)], lw="medio")
        # diagonales
        n = 10
        for i in range(n):
            xa, xb = L * i / n, L * (i + 1) / n
            _, ta, ia = est.peralte_viga(xa)
            _, tb, ib = est.peralte_viga(xb)
            if i % 2 == 0:
                v.linea([(X(xa), ia), (X(xb), tb)], lw="fino")
            else:
                v.linea([(X(xa), ta), (X(xb), ib)], lw="fino")
            v.linea([(X(xb), ib), (X(xb), tb)], lw="fino")
        # correas
        for i in range(est.N_CORREAS):
            x = 0.10 + i * est.SEP_CORREAS
            y = est.niv_sup_cubierta(x)
            v.poly(Polygon([(X(x) - 0.03, y - est.PERALTE_CORREA), (X(x) + 0.03, y - est.PERALTE_CORREA),
                            (X(x) + 0.03, y - 0.005), (X(x) - 0.03, y - 0.005)]), fc="k", ec="k", lw="fino")
        # canaleta posterior
        y_c = est.niv_sup_cubierta(0)
        v.poly(Polygon([(X(0) - sentido * 0.0, y_c), (X(0) - sentido * 0.25, y_c), (X(0) - sentido * 0.25, y_c - 0.18),
                        (X(0), y_c - 0.18)]), fc="none", ec="k", lw="medio")
        # columna
        xc = abs(d_col - d_atras)
        y_top = est.peralte_viga(xc)[1]
        hw = est.COLUMNA.h / 2000
        v.poly(Polygon([(d_col - hw, est.NIV_SUP_DADO), (d_col + hw, est.NIV_SUP_DADO), (d_col + hw, y_top),
                        (d_col - hw, y_top)]), fc="#cfd8e3", ec="k", lw="medio", z=4)
        # dado + zapata
        bz = est.ZAP_B / 2
        v.poly(Polygon([(d_col - est.DADO_B / 2, est.NIV_SUP_DADO), (d_col + est.DADO_B / 2, est.NIV_SUP_DADO),
                        (d_col + est.DADO_B / 2, -(est.DF_ZAPATA - est.H_ZAPATA)),
                        (d_col - est.DADO_B / 2, -(est.DF_ZAPATA - est.H_ZAPATA))]), fc="#e0e0e0", ec="k", lw="medio", z=3)
        v.poly(Polygon([(d_col - bz, -est.DF_ZAPATA + est.H_ZAPATA), (d_col + bz, -est.DF_ZAPATA + est.H_ZAPATA),
                        (d_col + bz, -est.DF_ZAPATA), (d_col - bz, -est.DF_ZAPATA)]), fc="#e0e0e0", ec="k",
               lw="medio", hatch="..", z=3)
        return X, L

    X1, L1 = cobertura(cob_ext.d_atras, cob_ext.d_frente, cob_ext.d_col, +1)
    X2, L2 = cobertura(cob_int.d_atras, cob_int.d_frente, cob_int.d_col, -1)
    # vehículos
    for (d0, d1, inv) in ((fila_ext.d0 + 0.0, fila_ext.d1, False), (fila_int.d0, fila_int.d1, True)):
        L = 5.30
        base = d0 - 0.15 if not inv else d1 + 0.15 - L
        pts = [(base + x, y) for x, y in _silueta_camioneta(L, invertir=not inv)]
        v.poly(Polygon(pts), fc="#f5f5f5", ec=GRIS, lw="fino", z=1.5)
        for xr in (0.95, 4.15):
            xr2 = base + (xr if not inv else L - xr)
            v.circulo((xr2, 0.38), 0.38 * v.k, fc="white", ec=GRIS, lw="fino", z=1.6)
    # cotas verticales
    xc1 = cob_ext.d_col
    v.cota((xc1 + 0.30, 0), (xc1 + 0.30, est.peralte_viga(abs(xc1 - cob_ext.d_atras))[2]),
           offset_mm=0, ext=False, texto=f"{est.NIV_INF_VIGA_COL:.2f} libre", h=1.4)
    v.cota((cob_ext.d_frente, 0), (cob_ext.d_frente, est.niv_sup_cubierta(L1)), offset_mm=4, lado=-1,
           texto=f"{est.niv_sup_cubierta(L1):.2f}", h=1.5)
    v.cota((cob_ext.d_atras, est.niv_sup_cubierta(0)), (cob_ext.d_atras, 0), offset_mm=4, lado=-1,
           texto=f"{est.niv_sup_cubierta(0):.2f}", h=1.5)
    # cotas horizontales
    yC = -1.75
    for (a, b) in ((fila_ext.d0, fila_ext.d1), (fila_ext.d1, fila_int.d0), (fila_int.d0, fila_int.d1)):
        v.cota((a, yC), (b, yC), offset_mm=0, ext=False, h=1.5, lado=1)
    v.cota((cob_ext.d_atras, est.niv_sup_cubierta(L1) + 0.8), (cob_ext.d_col, est.niv_sup_cubierta(L1) + 0.8),
           offset_mm=0, ext=False, h=1.4)
    v.cota((cob_ext.d_col, est.niv_sup_cubierta(L1) + 0.8), (cob_ext.d_frente, est.niv_sup_cubierta(L1) + 0.8),
           offset_mm=0, ext=False, h=1.4)
    # rótulos
    v.texto(((fila_ext.d1 + fila_int.d0) / 2, 0.9), "PASILLO DE CIRCULACIÓN", h=1.6, weight="bold")
    v.texto(((fila_ext.d1 + fila_int.d0) / 2, 0.35), "(SENTIDO ÚNICO)", h=1.3)
    v.texto((cob_ext.d_atras + L1 * 0.55, est.niv_sup_cubierta(L1 * 0.55) + 0.40), "TR-4 e=0.40 mm  PEND. 10 %",
            h=1.3, color=AZUL)
    v.texto((cob_int.d_atras - L2 * 0.5, est.niv_sup_cubierta(L2 * 0.5) + 0.35), "PEND. 10 %", h=1.3, color=AZUL)
    v.texto((fila_ext.d0 + 2.5, -0.85), "N.P.T. ±0.00", h=1.3)
    h.titulo_vista(x0 - 6, y0 - 22, titulo, f"ESC. 1/{escala}")
    return v


def lamina_A02(pdf, png_dir):
    h = Hoja("A-02", "PLANTA DE TECHOS Y CORTES", "ARQUITECTURA", "INDICADAS", 3, TOTAL_LAMINAS)
    v = h.vista(20, 100, 200, (-3.0, -2.0))
    dibujar_entorno(v, rotular=False)
    dibujar_plazas(v, numerar=False, topes=False, tenue=True)
    dibujar_coberturas(v, rotular=False, relleno=F_TECHO, ls="-", lw="medio")
    dibujar_lote(v, cerco=False)
    dibujar_columnas(v)
    for cob in g.COBERTURAS:
        b = cob.fila.borde
        sm = (cob.s0 + cob.s1) / 2
        # flecha de pendiente (hacia el fondo / canaleta)
        p_hi = b.punto(sm, cob.d_frente - (0.6 if cob.mira_hacia > 0 else -0.6))
        p_lo = b.punto(sm, cob.d_atras + (0.9 if cob.mira_hacia > 0 else -0.9))
        v.flecha_simple(p_hi, p_lo, lw="fino", cab=1.2)
        v.texto(b.punto(sm + 2.6, (cob.d_atras + cob.d_frente) / 2), "10 %", h=1.3,
                ang=_ang_borde(v, b) + 90)
        v.texto(b.punto(cob.s0 + 1.6, (cob.d_atras + cob.d_frente) / 2), cob.nombre, h=1.9, weight="bold",
                color=AZUL, ang=_ang_borde(v, b) + 90)
        # canaleta y bajadas
        v.linea([b.punto(cob.s0, cob.d_atras), b.punto(cob.s1, cob.d_atras)], lw="grueso", color=AZUL)
        for (pt_, s, d) in cob.columnas:
            v.circulo(b.punto(s, cob.d_atras + 0.15 * cob.mira_hacia), 0.55, fc=AZUL, ec=AZUL, lw="fino")
    corte_marca(v, g.DC.punto(S_CORTE_A, -1.0), g.DC.punto(S_CORTE_A, g.D_FILA_INT[1] + 1.2), "A", lado=1, h=2.0)
    corte_marca(v, g.BC.punto(U_CORTE_B, -1.0), g.BC.punto(U_CORTE_B, g.D_FILA_INT[1] + 1.2), "B", lado=1, h=2.0)
    v.norte((222, 266), g.NORTE, largo=11)
    h.titulo_vista(250, 112, "PLANTA DE TECHOS", "ESC. 1/200", ancho=56)
    # cuadro de coberturas
    filas = []
    for cob in g.COBERTURAS:
        filas.append([cob.nombre, f"Fila {cob.fila.nombre}", f"{len(cob.fila.plazas)}", f"{len(cob.columnas)}",
                      f"{cob.s1 - cob.s0:.2f} x {abs(cob.d_frente - cob.d_atras):.2f}", f"{cob.poly.area:.1f}"])
    filas.append(["TOTAL", "", f"{len(g.PLAZAS)}", f"{len(g.COLUMNAS)}", "", f"{est.AREA_TECHADA:.1f}"])
    yb = h.tabla(240, 238, ["TECHO", "FILA", "PLAZ.", "COL.", "L x A (m)", "m²"], filas,
                 [11, 11, 10, 9, 23, 12], h_fila=4.4, h_txt=1.45, titulo="CUADRO DE COBERTURAS",
                 alinear=["c", "c", "r", "r", "c", "r"], negrita_ultima=True)
    h.texto(240, yb - 4, "Canaleta posterior galvanizada e=0.6 mm", h=1.45)
    h.texto(240, yb - 7.4, "y bajadas PVC-SAP ø 4\" junto a cada", h=1.45)
    h.texto(240, yb - 10.8, "columna (●) a canaleta de piso.", h=1.45)
    # cortes
    _dibujar_corte(h, 22, 42, 125, g.FILA_A, g.FILA_D, g.COB_A, g.COB_D, "CORTE A-A (FILA A - PASILLO - FILA D)", "A")
    _dibujar_corte(h, 172, 42, 125, g.FILA_B, g.FILA_C, g.COB_B, g.COB_C, "CORTE B-B (FILA B - PASILLO - FILA C)", "B")
    notas = [
        f"1. Cobertura de plancha TR-4 aluzinc prepintada e = 0.40 mm sobre correas {est.CORREA.nombre} galvanizadas.",
        "2. Pendiente 10 % hacia el borde posterior (cerco o zona interior): el agua no cae sobre el pasillo.",
        f"3. Nivel de cobertura: {est.niv_sup_cubierta(0):.2f} m en el borde posterior y {est.niv_sup_cubierta(est.ANCHO_COB):.2f} m en el borde frontal.",
        f"4. Gálibo libre mínimo {est.NIV_INF_VIGA_COL:.2f} m bajo la viga (en la columna).",
        "5. Vehículo de diseño: camioneta pick-up 5.30 x 1.85 x 1.82 m (tipo Toyota Hilux).",
        "6. Remate frontal (fascia) de plancha prepintada h = 0.25 m y babeta de encuentro con cerco.",
    ]
    h.notas(283, "NOTAS", notas, h=1.45, ancho_chars=62)
    h.guardar(pdf, os.path.join(png_dir, "A-02.png") if png_dir else None)


# ==========================================================================
# E-01  Cimentación y columnas
# ==========================================================================
def _zapata_poly(cob, s):
    b = cob.fila.borde
    return b.rect(s - est.ZAP_L / 2, s + est.ZAP_L / 2, cob.d_col - est.ZAP_B / 2, cob.d_col + est.ZAP_B / 2)


def _dado_poly(cob, s):
    b = cob.fila.borde
    return b.rect(s - est.DADO_L / 2, s + est.DADO_L / 2, cob.d_col - est.DADO_B / 2, cob.d_col + est.DADO_B / 2)


def lamina_E01(pdf, png_dir):
    h = Hoja("E-01", "CIMENTACIÓN Y COLUMNAS", "ESTRUCTURAS", "1/150", 4, TOTAL_LAMINAS)
    v = vista_planta(h)
    dibujar_lote(v, cerco=True)
    dibujar_plazas(v, numerar=False, topes=False, tenue=True)
    dibujar_coberturas(v, rotular=False, color=GRIS_CLARO, lw="fino")
    for cob in g.COBERTURAS:
        for (pt_, s, d) in cob.columnas:
            v.poly(_zapata_poly(cob, s), fc="none", ec="k", lw="medio", ls=(0, (4, 2)), z=5)
            v.poly(_dado_poly(cob, s), fc="#d9d9d9", ec="k", lw="fino", z=6)
    dibujar_columnas(v)
    for cod, cob, c in etiquetas_columnas():
        b = cob.fila.borde
        off = -1 if cob.mira_hacia > 0 else 1
        q = c + b.n * cob.mira_hacia * (est.ZAP_B / 2 + 1.0)
        v.marca_eje(q, cod.replace("C-", ""), r_mm=2.0, h=1.4)
    # cotas de ejes de columnas (fila A y fila B)
    for cob, lado in ((g.COB_A, 1), (g.COB_B, -1)):
        b = cob.fila.borde
        ss = [s for (_, s, _) in cob.columnas]
        dref = -0.9 if cob.nombre != "T-1" else -0.9
        for a, c in zip(ss, ss[1:]):
            v.cota(b.punto(a, cob.d_col), b.punto(c, cob.d_col), offset_mm=10, lado=-lado if cob is g.COB_A else 1,
                   h=1.5, ext=True)
    v.cota(g.BC.punto(g.COB_B.columnas[0][1], 0), g.BC.punto(g.COB_B.columnas[0][1], g.COB_B.d_col),
           offset_mm=4, lado=1, h=1.4)
    _norte(v)
    v.escala_grafica((215, 20), metros=10, paso=2)
    h.titulo_vista(80, 23, "PLANTA DE CIMENTACIÓN Y COLUMNAS", "ESC. 1/150")

    # Tabla de columnas (coordenadas locales)
    filas = []
    for cod, cob, c in etiquetas_columnas():
        filas.append([cod, cob.nombre, f"{c[0]:.2f}", f"{c[1]:.2f}"])
    yb = h.tabla(h.x_franja + 2.5, 278, ["COLUMNA", "TECHO", "u (m)", "v (m)"], filas, [20, 18, 22, 22],
                 h_fila=3.6, h_txt=1.45, titulo="UBICACIÓN DE COLUMNAS (ejes)", alinear=["c", "c", "r", "r"])
    z = est.ZAPATA
    filas = [["Z-1", f"{est.ZAP_L:.2f} x {est.ZAP_B:.2f}", f"{est.H_ZAPATA:.2f}", f"{est.DF_ZAPATA:.2f}",
              f"{len(g.COLUMNAS)}"]]
    yb = h.tabla(h.x_franja + 2.5, yb - 8, ["TIPO", "L x B (m)", "h (m)", "Df (m)", "CANT."], filas,
                 [12, 22, 14, 16, 18], h_fila=4.2, h_txt=1.55, titulo="CUADRO DE ZAPATAS", alinear=["c"] * 5)
    notas = [
        "CONCRETO: solado f'c = 100 kg/cm² e = 0.10 m; zapatas y dados f'c = 210 kg/cm²; cemento Portland tipo I.",
        "ACERO DE REFUERZO: fy = 4200 kg/cm² (ASTM A615 Gr. 60). Recubrimientos: zapata 7.5 cm, dado 4 cm.",
        f"TERRENO: capacidad portante asumida qadm ≥ {est.Q_ADM_SUPUESTA / 98.07:.1f} kg/cm² - CONFIRMAR CON EMS (E.050). Presión máx. calculada {z['qmax'] / 98.07:.2f} kg/cm², FS volteo {z['fs_volteo']:.1f}.",
        "Desplantar sobre terreno natural firme; eliminar capa orgánica (césped) y rellenos.",
        "Pernos de anclaje con plantilla metálica; nivelar placa con mortero sin contracción (grout) e = 25 mm.",
    ]
    h.notas(yb - 8, "ESPECIFICACIONES", notas, h=1.45, ancho_chars=62)

    # Detalle zapata (planta y corte) - ESC 1/25
    h.guardar(pdf, os.path.join(png_dir, "E-01.png") if png_dir else None)


def _detalle_zapata(h, x0, y0):
    """Corte y planta de la zapata Z-1 a ESC 1/20. (x0, y0) = esquina inferior izquierda del área."""
    esc = 20
    k = 1000 / esc
    B, L, Hz, Df = est.ZAP_B, est.ZAP_L, est.H_ZAPATA, est.DF_ZAPATA
    db, dl = est.DADO_B, est.DADO_L
    nd = est.NIV_SUP_DADO
    # ---- CORTE (en la dirección del voladizo)
    v = h.vista(x0 + 30 + B / 2 * k, y0 + 22 + (Df + 0.1) * k, esc, (0, 0))
    v.poly(Polygon([(-B / 2 - 0.1, -Df - 0.1), (B / 2 + 0.1, -Df - 0.1), (B / 2 + 0.1, -Df), (-B / 2 - 0.1, -Df)]),
           fc="#f3f3f3", ec="k", lw="fino")
    v.poly(Polygon([(-B / 2, -Df), (B / 2, -Df), (B / 2, -Df + Hz), (-B / 2, -Df + Hz)]), fc="#eeeeee", ec="k",
           lw="grueso", hatch="..")
    v.poly(Polygon([(-db / 2, -Df + Hz), (db / 2, -Df + Hz), (db / 2, nd), (-db / 2, nd)]),
           fc="#eeeeee", ec="k", lw="grueso", hatch="..")
    v.linea([(-B / 2 - 0.5, 0), (-db / 2, 0)], lw="medio")
    v.linea([(db / 2, 0), (B / 2 + 0.5, 0)], lw="medio")
    v.poly(Polygon([(-B / 2 - 0.5, 0), (-db / 2, 0), (-db / 2, -0.05), (-B / 2 - 0.5, -0.05)]), fc="none", ec="none",
           hatch="////", hatch_color=GRIS_CLARO)
    v.texto((B / 2 + 0.05, 0.08), "N.P.T. ±0.00", h=1.4, ha="left", va="bottom")
    v.texto((B / 2 + 0.05, -Df + Hz + 0.08), "relleno compactado", h=1.3, ha="left", va="bottom", color=GRIS)
    pb = est.PLACA["placa"] / 1000
    v.poly(Polygon([(-pb / 2, nd), (pb / 2, nd), (pb / 2, nd + 0.025), (-pb / 2, nd + 0.025)]), fc="k", ec="k",
           lw="fino")
    hc = est.COLUMNA.h / 1000
    v.poly(Polygon([(-hc / 2, nd + 0.025), (hc / 2, nd + 0.025), (hc / 2, nd + 0.40), (-hc / 2, nd + 0.40)]),
           fc="#cfd8e3", ec="k", lw="medio")
    v.linea([(-hc / 2, nd + 0.40), (-hc / 2 + 0.05, nd + 0.43), (hc / 2 - 0.05, nd + 0.37), (hc / 2, nd + 0.40)],
            lw="fino")
    sp = est.PLACA["sep"]
    for x in (-sp / 2, sp / 2):
        v.linea([(x, nd + 0.07), (x, -0.62), (x + (0.12 if x < 0 else -0.12), -0.62)], lw="grueso", color=ROJO)
    rec = 0.075
    v.linea([(-B / 2 + rec, -Df + rec + 0.15), (-B / 2 + rec, -Df + rec), (B / 2 - rec, -Df + rec),
             (B / 2 - rec, -Df + rec + 0.15)], lw="medio", color=ROJO)
    for x in np.linspace(-L / 2 + rec + 0.05, L / 2 - rec - 0.05, 7) * (B / L):
        v.circulo((x, -Df + rec + 0.025), 0.45, fc=ROJO, ec=ROJO, lw="fino")
    for x in (-db / 2 + 0.05, db / 2 - 0.05):
        v.linea([(x, nd - 0.04), (x, -Df + rec + 0.05), (x + (0.30 if x < 0 else -0.30), -Df + rec + 0.05)],
                lw="medio", color=ROJO)
    for y in np.arange(-Df + Hz + 0.05, nd - 0.04, 0.15):
        v.linea([(-db / 2 + 0.05, y), (db / 2 - 0.05, y)], lw="fino", color=ROJO)
    v.cota((-B / 2, -Df - 0.1), (B / 2, -Df - 0.1), offset_mm=5, lado=-1, h=1.6)
    v.cota((B / 2 + 0.1, -Df - 0.1), (B / 2 + 0.1, -Df), offset_mm=14, lado=-1, h=1.4)
    v.cota((B / 2 + 0.1, -Df), (B / 2 + 0.1, -Df + Hz), offset_mm=14, lado=-1, h=1.4)
    v.cota((B / 2 + 0.1, -Df + Hz), (B / 2 + 0.1, 0), offset_mm=14, lado=-1, h=1.4)
    v.cota((B / 2 + 0.1, 0), (B / 2 + 0.1, nd), offset_mm=14, lado=-1, h=1.3)
    v.cota((-db / 2, nd + 0.45), (db / 2, nd + 0.45), offset_mm=4, lado=1, h=1.5)
    _leader(v, (-B / 2 - 0.25, -Df + 0.30), (-0.45, -Df + rec + 0.03), "ø 1/2\" @ 0.20 m\nambos sentidos", ha="right",
            color=ROJO)
    _leader(v, (-B / 2 - 0.25, -0.30), (-db / 2 + 0.05, -0.30), "8 ø 5/8\" (dado)", ha="right", color=ROJO)
    _leader(v, (-B / 2 - 0.25, -0.05), (-db / 2 + 0.05, -0.10), "Estr. ø 3/8\": 1@0.05,\n5@0.10, resto @0.15",
            ha="right", color=ROJO)
    _leader(v, (-B / 2 - 0.25, 0.35), (-sp / 2, 0.0), "4 pernos ø 1\" F1554\nL = 0.75 m c/gancho", ha="right",
            color=ROJO)
    _leader(v, (-B / 2 - 0.25, -Df - 0.25), (-B / 2 + 0.2, -Df - 0.05), "Solado e=0.10 m\nf'c = 100 kg/cm²", ha="right")
    _leader(v, (B / 2 + 0.25, nd + 0.30), (hc / 2, nd + 0.30), f"Columna {est.COLUMNA.nombre}")
    _leader(v, (B / 2 + 0.25, nd + 0.15), (pb / 2, nd + 0.012), "Placa base + grout 25 mm")
    h.titulo_vista(x0, y0 + 8, "ZAPATA Z-1 - CORTE (dirección del voladizo)", "ESC. 1/20", ancho=86)
    # ---- PLANTA
    v2 = h.vista(x0 + 190 + L / 2 * k, y0 + 30 + B / 2 * k, esc, (0, 0))
    v2.poly(Polygon([(-L / 2, -B / 2), (L / 2, -B / 2), (L / 2, B / 2), (-L / 2, B / 2)]), fc="#eeeeee", ec="k",
            lw="grueso")
    for x in np.linspace(-L / 2 + 0.1, L / 2 - 0.1, 7):
        v2.linea([(x, -B / 2 + 0.08), (x, B / 2 - 0.08)], lw="fino", color=ROJO, ls=(0, (4, 2)))
    for y in np.linspace(-B / 2 + 0.1, B / 2 - 0.1, 9):
        v2.linea([(-L / 2 + 0.08, y), (L / 2 - 0.08, y)], lw="fino", color=ROJO, ls=(0, (4, 2)))
    v2.poly(Polygon([(-dl / 2, -db / 2), (dl / 2, -db / 2), (dl / 2, db / 2), (-dl / 2, db / 2)]), fc="#d9d9d9",
            ec="k", lw="medio", z=4)
    v2.poly(Polygon([(-est.PLACA["placa_l"] / 2000, -pb / 2), (est.PLACA["placa_l"] / 2000, -pb / 2),
                     (est.PLACA["placa_l"] / 2000, pb / 2), (-est.PLACA["placa_l"] / 2000, pb / 2)]),
            fc="#9e9e9e", ec="k", lw="fino", z=5)
    v2.poly(Polygon([(-est.COLUMNA.b / 2000, -hc / 2), (est.COLUMNA.b / 2000, -hc / 2), (est.COLUMNA.b / 2000, hc / 2),
                     (-est.COLUMNA.b / 2000, hc / 2)]), fc="#cfd8e3", ec="k", lw="medio", z=6)
    v2.cota((-L / 2, -B / 2), (L / 2, -B / 2), offset_mm=5, lado=-1, h=1.6)
    v2.cota((L / 2, -B / 2), (L / 2, B / 2), offset_mm=5, lado=1, h=1.6)
    v2.cota((-dl / 2, B / 2), (dl / 2, B / 2), offset_mm=5, lado=1, h=1.4)
    v2.flecha_simple((-L / 2 - 0.35, -0.6), (-L / 2 - 0.35, 0.6), lw="fino")
    v2.texto((-L / 2 - 0.55, 0), "dirección del voladizo", h=1.3, ang=90)
    h.titulo_vista(x0 + 175, y0 + 8, "ZAPATA Z-1 - PLANTA", "ESC. 1/20", ancho=50)


# ==========================================================================
# E-02  Estructura de techo
# ==========================================================================
def lamina_E02(pdf, png_dir):
    h = Hoja("E-02", "ESTRUCTURA DE TECHO", "ESTRUCTURAS", "1/150", 5, TOTAL_LAMINAS,
             subtitulo="VIGAS, CORREAS Y ARRIOSTRES")
    v = vista_planta(h, y0=Y0 + 6)
    dibujar_lote(v, cerco=False, lw="medio")
    dibujar_plazas(v, numerar=False, topes=False, tenue=True)
    for cob in g.COBERTURAS:
        b = cob.fila.borde
        v.poly(cob.poly, fc="none", ec="k", lw="medio")
        # correas
        for i in range(est.N_CORREAS):
            x = 0.10 + i * est.SEP_CORREAS
            d = cob.d_atras + cob.mira_hacia * x
            v.linea([b.punto(cob.s0, d), b.punto(cob.s1, d)], lw="fino", color=AZUL)
        # vigas en voladizo
        ss = [s for (_, s, _) in cob.columnas]
        for s in ss:
            v.linea([b.punto(s, cob.d_atras), b.punto(s, cob.d_frente)], lw="mgrueso", color="k")
        # templadores a tercios
        for a, c in zip(ss, ss[1:]):
            for f in (1 / 3, 2 / 3):
                s = a + (c - a) * f
                v.linea([b.punto(s, cob.d_atras), b.punto(s, cob.d_frente)], lw="fino", color=GRIS,
                        ls=(0, (2, 2)))
        # arriostres en X en los paños extremos
        if len(ss) >= 2:
            for (a, c) in {(ss[0], ss[1]), (ss[-2], ss[-1])}:
                v.linea([b.punto(a, cob.d_atras), b.punto(c, cob.d_frente)], lw="fino", color=ROJO)
                v.linea([b.punto(a, cob.d_frente), b.punto(c, cob.d_atras)], lw="fino", color=ROJO)
        v.texto(b.punto((ss[0] + ss[1]) / 2 if len(ss) > 1 else ss[0], (cob.d_atras + cob.d_frente) / 2 + 0.0),
                cob.nombre, h=2.0, weight="bold", color=AZUL, ang=_ang_borde(v, b),
                bbox=dict(fc="white", ec="none", pad=0.6))
        for s in ss:
            v.texto(b.punto(s, cob.d_frente + 0.75 * cob.mira_hacia), "VV-1", h=1.2, ang=_ang_borde(v, b) + 90)
    dibujar_columnas(v)
    # cotas de luces de correas en T-1
    cob = g.COB_A
    b = cob.fila.borde
    ss = [cob.s0] + [s for (_, s, _) in cob.columnas] + [cob.s1]
    for a, c in zip(ss, ss[1:]):
        v.cota(b.punto(a, cob.d_frente), b.punto(c, cob.d_frente), offset_mm=4, lado=-1, h=1.4)
    cob = g.COB_B
    b = cob.fila.borde
    ss = [s for (_, s, _) in cob.columnas]
    for a, c in zip(ss, ss[1:]):
        v.cota(b.punto(a, cob.d_atras), b.punto(c, cob.d_atras), offset_mm=5, lado=-1, h=1.4)
    _norte(v, (300, 270))
    h.titulo_vista(80, 29, "PLANTA DE ESTRUCTURA DE TECHO", "ESC. 1/150")
    # leyenda / cuadro de elementos
    x = h.x_franja + 2.5
    filas = [["COL", est.COLUMNA.nombre, f"{est.COLUMNA.peso:.1f}"],
             ["VV-1", "Viga en voladizo reticulada", "-"],
             ["  cordones", est.CORDON.nombre, f"{est.CORDON.peso:.1f}"],
             ["  diagonales", est.DIAGONAL.nombre, f"{est.DIAGONAL.peso:.1f}"],
             ["CO", est.CORREA.nombre + " galv.", f"{est.CORREA.peso:.1f}"],
             ["TE", "Templador ø 3/8\" a L/3", "0.56"],
             ["AR", "Arriostre en X ø 1/2\" + templador", "0.99"]]
    yb = h.tabla(x, 278, ["ELEM.", "PERFIL", "kg/m"], filas, [16, 56, 14], h_fila=4.0, h_txt=1.45,
                 titulo="CUADRO DE ELEMENTOS ESTRUCTURALES", alinear=["l", "l", "r"])
    y = yb - 7
    h.texto(x, y + 1, "LEYENDA", h=2.0, weight="bold", va="bottom")
    items = [("k", "mgrueso", "-", "Viga en voladizo VV-1 (sobre columna)"),
             (AZUL, "fino", "-", f"Correa {est.CORREA.nombre}"),
             (GRIS, "fino", (0, (2, 2)), "Templador ø 3/8\" (a tercios de la luz)"),
             (ROJO, "fino", "-", "Arriostre en X ø 1/2\" (paños extremos)")]
    for i, (c, lw, ls, t) in enumerate(items):
        yy = y - 3 - i * 4
        h.ax.plot([x, x + 8], [yy, yy], color=c, lw=LW[lw], ls=ls)
        h.texto(x + 10, yy, t, h=1.5)
    y = y - 3 - len(items) * 4 - 3
    # metrado de acero
    filas = []
    for f in est.METRADO:
        filas.append([f[0][:34], f"{f[-1]:,.0f}"])
    filas.append(["TOTAL ACERO ESTRUCTURAL", f"{est.ACERO_TOTAL_KG:,.0f}"])
    yb = h.tabla(x, y, ["METRADO DE ACERO", "kg"], filas, [70, 16], h_fila=3.7, h_txt=1.4, alinear=["l", "r"],
                 negrita_ultima=True)
    h.texto(x, yb - 3.5, f"Ratio: {est.ACERO_TOTAL_KG / est.AREA_TECHADA:.1f} kg/m² de techo ({est.AREA_TECHADA:.0f} m²)",
            h=1.6, weight="bold")
    notas = [
        "Correas continuas sobre 2 o más vigas, empalmes sobre apoyo con 4 pernos ø 1/2\".",
        "Voladizos laterales de correas ≤ 2.50 m.",
        "Uniones soldadas en taller con electrodo E70XX; uniones de obra empernadas (A325).",
    ]
    h.notas(yb - 9, "NOTAS", notas, h=1.45, ancho_chars=62)
    h.guardar(pdf, os.path.join(png_dir, "E-02.png") if png_dir else None)


# ==========================================================================
# E-03  Pórtico típico, detalles y especificaciones
# ==========================================================================
def _leader(v, p_txt, p_obj, texto, h=1.45, ha="left", color="k"):
    a, b = v.T(p_txt), v.T(p_obj)
    v.ax.annotate("", xy=b, xytext=a, arrowprops=dict(arrowstyle="-|>,head_length=0.35,head_width=0.15",
                                                      lw=LW["fino"], color=color), zorder=8)
    off = 1.0 if ha == "left" else -1.0
    v.ax.text(a[0] + off, a[1], texto, fontsize=pt(h), ha=ha, va="center", color=color, zorder=8)


def lamina_E03(pdf, png_dir):
    h = Hoja("E-03", "PÓRTICO TÍPICO Y CONEXIONES", "ESTRUCTURAS", "INDICADAS", 6, TOTAL_LAMINAS)
    esc = 40
    v = h.vista(72, 100, esc, (0, 0))
    L = est.ANCHO_COB
    xc = est.BRAZO_POSTERIOR
    xs = np.linspace(0, L, 61)
    v.linea([(x, est.niv_sup_cubierta(x)) for x in xs], lw="grueso", color=AZUL)
    v.linea([(x, est.peralte_viga(x)[1]) for x in xs], lw="grueso")
    v.linea([(x, est.peralte_viga(x)[2]) for x in xs], lw="grueso")
    n = 10
    for i in range(n):
        xa, xb = L * i / n, L * (i + 1) / n
        _, ta, ia = est.peralte_viga(xa)
        _, tb, ib = est.peralte_viga(xb)
        if i % 2 == 0:
            v.linea([(xa, ia), (xb, tb)], lw="medio")
        else:
            v.linea([(xa, ta), (xb, ib)], lw="medio")
        v.linea([(xb, ib), (xb, tb)], lw="medio")
    v.linea([(0, est.peralte_viga(0)[2]), (0, est.peralte_viga(0)[1])], lw="medio")
    for i in range(est.N_CORREAS):
        x = 0.10 + i * est.SEP_CORREAS
        y = est.niv_sup_cubierta(x)
        v.poly(Polygon([(x - 0.03, y - est.PERALTE_CORREA), (x + 0.03, y - est.PERALTE_CORREA), (x + 0.03, y),
                        (x - 0.03, y)]), fc="k", ec="k", lw="fino")
    hc = est.COLUMNA.h / 1000
    y_top = est.peralte_viga(xc)[1]
    v.poly(Polygon([(xc - hc / 2, est.NIV_SUP_DADO + 0.025), (xc + hc / 2, est.NIV_SUP_DADO + 0.025),
                    (xc + hc / 2, y_top), (xc - hc / 2, y_top)]), fc="#cfd8e3", ec="k", lw="grueso")
    v.linea([(xc, -est.DF_ZAPATA - 0.2), (xc, y_top + 0.35)], lw="fino", ls=(0, (8, 2, 1, 2)))
    yi = est.peralte_viga(xc)[2]
    for sgn in (-1, 1):
        v.poly(Polygon([(xc + sgn * hc / 2, yi), (xc + sgn * (hc / 2 + 0.30), yi), (xc + sgn * hc / 2, yi - 0.30)]),
               fc="#9fb3c8", ec="k", lw="fino")
    v.linea([(-0.6, 0), (L + 0.6, 0)], lw="grueso")
    db = est.DADO_B
    v.poly(Polygon([(xc - db / 2, est.NIV_SUP_DADO), (xc + db / 2, est.NIV_SUP_DADO), (xc + db / 2, -0.6),
                    (xc - db / 2, -0.6)]), fc="#eeeeee", ec="k", lw="medio", hatch="..")
    v.poly(Polygon([(xc - est.ZAP_B / 2, -0.6), (xc + est.ZAP_B / 2, -0.6), (xc + est.ZAP_B / 2, -est.DF_ZAPATA),
                    (xc - est.ZAP_B / 2, -est.DF_ZAPATA)]), fc="#eeeeee", ec="k", lw="medio", hatch="..")
    pb = est.PLACA["placa"] / 1000
    v.poly(Polygon([(xc - pb / 2, est.NIV_SUP_DADO), (xc + pb / 2, est.NIV_SUP_DADO), (xc + pb / 2, est.NIV_SUP_DADO + 0.025),
                    (xc - pb / 2, est.NIV_SUP_DADO + 0.025)]), fc="k", ec="k", lw="fino")
    v.poly(Polygon([(-0.15, 0), (0.0, 0), (0.0, 2.4), (-0.15, 2.4)]), fc="#9e9e9e", ec="k", lw="medio")
    yc = est.niv_sup_cubierta(0)
    v.poly(Polygon([(0.0, yc), (0.10, yc), (0.10, yc - 0.20), (-0.12, yc - 0.20), (-0.12, yc + 0.08)]),
           fc="none", ec=AZUL, lw="medio")
    v.linea([(0.02, yc - 0.20), (0.02, 0.15)], lw="medio", color=AZUL, ls=(0, (6, 2)))
    # cotas
    v.cota((0, -1.65), (xc, -1.65), offset_mm=0, ext=False, h=1.6)
    v.cota((xc, -1.65), (L, -1.65), offset_mm=0, ext=False, h=1.6)
    v.cota((0, -2.25), (L, -2.25), offset_mm=0, ext=False, h=1.6)
    v.cota((L + 0.25, 0), (L + 0.25, est.peralte_viga(L)[2]), offset_mm=3, lado=-1, h=1.5)
    v.cota((L + 0.25, 0), (L + 0.25, est.niv_sup_cubierta(L)), offset_mm=11, lado=-1, h=1.5)
    v.cota((-0.35, 0), (-0.35, est.niv_sup_cubierta(0)), offset_mm=6, lado=1, h=1.5)
    v.cota((xc + 0.55, 0), (xc + 0.55, est.peralte_viga(xc)[2]), offset_mm=0, ext=False, h=1.5,
           texto=f"{est.NIV_INF_VIGA_COL:.2f} gálibo")
    _, t0, i0 = est.peralte_viga(xc)
    v.cota((xc + 0.45, i0), (xc + 0.45, t0), offset_mm=0, ext=False, h=1.3, texto=f"{t0 - i0:.2f}")
    _, t1, i1 = est.peralte_viga(L)
    v.cota((L - 0.12, i1), (L - 0.12, t1), offset_mm=0, ext=False, h=1.2, texto=f"{t1 - i1:.2f}")
    v.cota((-0.6, 0), (-0.6, -est.DF_ZAPATA), offset_mm=3, lado=1, h=1.4)
    # rótulos con líneas guía
    _leader(v, (2.2, 4.65), (2.5, est.niv_sup_cubierta(2.5)), "COBERTURA TR-4 e=0.40 mm, PENDIENTE 10 %", color=AZUL)
    x_cor = 0.10 + 3 * est.SEP_CORREAS
    _leader(v, (3.9, 4.35), (x_cor, est.niv_sup_cubierta(x_cor) - 0.06),
            f"CORREA {est.CORREA.nombre} @ {est.SEP_CORREAS:.2f} m")
    _leader(v, (6.25, 3.75), (5.0, est.peralte_viga(5.0)[1] - 0.01), f"CORDÓN SUPERIOR\n{est.CORDON.nombre}")
    _leader(v, (6.25, 2.95), (4.6, est.peralte_viga(4.6)[2] + 0.01), f"CORDÓN INFERIOR\n{est.CORDON.nombre}")
    xm = L * 5.5 / n
    _, tm, im = est.peralte_viga(xm)
    _leader(v, (6.25, 2.35), (xm, (tm + im) / 2), f"DIAGONALES Y MONTANTES\n{est.DIAGONAL.nombre}")
    _leader(v, (2.4, 1.75), (xc + hc / 2, 1.75), f"COLUMNA {est.COLUMNA.nombre}")
    _leader(v, (2.4, 2.35), (xc + hc / 2 + 0.12, yi - 0.08), "CARTELAS PL 10 mm")
    _leader(v, (2.4, 0.65), (xc + pb / 2, est.NIV_SUP_DADO + 0.02),
            f"PLACA BASE PL {est.PLACA['placa']:.0f}x{est.PLACA['placa_l']:.0f}x25 + 4 pernos ø 1\"")
    _leader(v, (-1.3, 3.75), (-0.05, yc - 0.1), "CANALETA", ha="right", color=AZUL)
    _leader(v, (-1.3, 1.6), (0.02, 1.6), "BAJADA PVC ø 4\"", ha="right", color=AZUL)
    _leader(v, (-1.3, 0.9), (-0.15, 0.9), "CERCO", ha="right")
    _leader(v, (2.4, -0.9), (xc + est.ZAP_B / 2, -0.9), "ZAPATA Z-1 (ver E-04)")
    v.texto((L * 0.78, 0.22), "← PLAZA     |     PASILLO →", h=1.3, color=GRIS)
    v.texto((xc, -1.0), "", h=1)
    h.titulo_vista(60, 30, "PÓRTICO TÍPICO EN VOLADIZO  VV-1", "ESC. 1/40", ancho=82)

    # Detalle placa base (planta) ESC 1/10
    vd = h.vista(272, 245, 10, (0, 0))
    pl = est.PLACA["placa_l"] / 1000
    vd.poly(Polygon([(-pb / 2, -pl / 2), (pb / 2, -pl / 2), (pb / 2, pl / 2), (-pb / 2, pl / 2)]), fc="#eeeeee",
            ec="k", lw="grueso")
    hc_, bc_, tc = est.COLUMNA.h / 1000, est.COLUMNA.b / 1000, est.COLUMNA.t / 1000
    vd.poly(Polygon([(-hc_ / 2, -bc_ / 2), (hc_ / 2, -bc_ / 2), (hc_ / 2, bc_ / 2), (-hc_ / 2, bc_ / 2)]),
            fc="#cfd8e3", ec="k", lw="grueso")
    vd.poly(Polygon([(-hc_ / 2 + tc, -bc_ / 2 + tc), (hc_ / 2 - tc, -bc_ / 2 + tc), (hc_ / 2 - tc, bc_ / 2 - tc),
                     (-hc_ / 2 + tc, bc_ / 2 - tc)]), fc="white", ec="k", lw="fino")
    sp, sl = est.PLACA["sep"], est.PLACA["sep_l"]
    for x in (-sp / 2, sp / 2):
        for y in (-sl / 2, sl / 2):
            vd.circulo((x, y), 0.0127 * vd.k * 1.2, fc="white", ec=ROJO, lw="medio")
    for sgn in (-1, 1):
        vd.poly(Polygon([(sgn * hc_ / 2, -0.005), (sgn * pb / 2, -0.005), (sgn * pb / 2, 0.005), (sgn * hc_ / 2, 0.005)]),
                fc="k", ec="k", lw="fino")
        vd.poly(Polygon([(-0.005, sgn * bc_ / 2), (0.005, sgn * bc_ / 2), (0.005, sgn * pl / 2), (-0.005, sgn * pl / 2)]),
                fc="k", ec="k", lw="fino")
    vd.cota((-pb / 2, -pl / 2), (pb / 2, -pl / 2), offset_mm=5, lado=-1, h=1.5, decimales=3)
    vd.cota((pb / 2, -pl / 2), (pb / 2, pl / 2), offset_mm=5, lado=1, h=1.5, decimales=3)
    vd.cota((-sp / 2, pl / 2), (sp / 2, pl / 2), offset_mm=4, lado=1, h=1.4, decimales=3)
    h.titulo_vista(240, 280, "DETALLE PLACA BASE", "ESC. 1/10 - PLANTA", ancho=52)
    yb = 219
    for t in [f"PL {est.PLACA['placa']:.0f}x{est.PLACA['placa_l']:.0f}x25 mm (ASTM A36)",
              "4 cartelas PL 10 mm, h = 200 mm",
              f"4 pernos {est.PLACA['perno']}",
              "Grout sin contracción e = 25 mm",
              "Soldadura columna-placa: filete 8 mm E70XX"]:
        h.texto(240, yb, t, h=1.45)
        yb -= 3.2

    # Franja derecha: cargas, verificaciones, especificaciones
    cargas = [f"Carga muerta D = {est.D_KPA:.2f} kPa ({est.D_KPA * 102:.0f} kg/m²)",
              f"Carga viva de techo Lr = {est.LR_KPA:.2f} kPa (30 kg/m², E.020)",
              f"Viento: V = {est.V_VIENTO:.0f} km/h, C neto = ±{est.C_VIENTO}, p = {est.W_KPA:.2f} kPa (E.020)",
              f"Sismo: Z = {est.Z_SISMO}, U = 1.0, C = 2.5, S = {est.S_SISMO}, R = {est.R_SISMO} (E.030; verificar zona sísmica)",
              "Combinaciones LRFD (E.090): 1.4D; 1.2D+1.6Lr; 1.2D+1.3W+0.5Lr; 0.9D-1.3W; 1.2D+1.0E"]
    y = h.notas(278, "CARGAS DE DISEÑO", cargas, h=1.45, ancho_chars=62)
    v_ = est.VIGA
    c_ = est.COLUMNA_SEL
    verif = [f"Correa: ratio {est.CORREA_SEL['ratio']:.2f}; flecha {est.CORREA_SEL['flecha']:.0f} mm ≤ L/180 = {est.CORREA_SEL['flecha_lim']:.0f} mm",
             f"Viga VV-1: Mu = {v_['mu_raiz']:.1f} kN·m; fuerza en cordón {v_['f_cordon']:.0f} kN ≤ φPn {v_['phic']:.0f} kN",
             f"Columna: Mu = {c_['mu']:.1f} kN·m; interacción {c_['inter']:.2f} ≤ 1.0",
             f"Flecha en punta del voladizo (Lr): {c_['flecha_total']:.0f} mm ≤ 2L/180 = {c_['flecha_lim']:.0f} mm",
             f"Perno más cargado: {est.PLACA['t_perno']:.0f} kN ≤ φRn {est.PLACA['phirn']:.0f} kN",
             f"Zapata: qmax = {est.ZAPATA['qmax'] / 98.07:.2f} kg/cm²; FS volteo = {est.ZAPATA['fs_volteo']:.1f}"]
    y = h.notas(y - 1, "VERIFICACIONES (PREDIMENSIONAMIENTO)", verif, h=1.45, ancho_chars=62)
    espec = ["Tubos ASTM A500 Gr. B (o LAC equivalente); planchas ASTM A36; correas galvanizadas ASTM A653.",
             "Soldadura SMAW E70XX (AWS D1.1) con soldadores calificados. Uniones de obra con pernos A325.",
             "Pintura: limpieza SSPC-SP3, 2 capas de base epóxica anticorrosiva (3 mils c/u) + esmalte (2 mils).",
             "Verticalidad de columnas H/500. Contraflecha en punta de voladizo: 15 mm.",
             "Predimensionamiento para anteproyecto: debe ser verificado y firmado por ingeniero civil colegiado (CIP)."]
    h.notas(y - 1, "ESPECIFICACIONES TÉCNICAS", espec, h=1.45, ancho_chars=62)
    h.guardar(pdf, os.path.join(png_dir, "E-03.png") if png_dir else None)


def lamina_E04(pdf, png_dir):
    h = Hoja("E-04", "DETALLES DE CIMENTACIÓN", "ESTRUCTURAS", "INDICADAS", 7, TOTAL_LAMINAS,
             subtitulo="Y CONEXIONES")
    _detalle_zapata(h, 34, 34)
    # Detalle unión correa - viga ESC 1/5
    vc = h.vista(52, 222, 5, (0, 0))
    vc.poly(Polygon([(-0.0375, -0.075), (0.0375, -0.075), (0.0375, 0.0), (-0.0375, 0.0)]), fc="#cfd8e3", ec="k",
            lw="grueso")
    hcor, bcor, ccor = est.CORREA.h / 1000, est.CORREA.b / 1000, est.CORREA.c / 1000
    vc.poly(Polygon([(0.0, 0.0), (0.006, 0.0), (0.006, 0.10), (0.0, 0.10)]), fc="#555555", ec="k", lw="fino")
    vc.poly(Polygon([(-0.05, 0.0), (0.006, 0.0), (0.006, 0.006), (-0.05, 0.006)]), fc="#555555", ec="k", lw="fino")
    x0c = 0.006
    vc.linea([(x0c + bcor, hcor - ccor), (x0c + bcor, hcor), (x0c, hcor), (x0c, 0.0), (x0c + bcor, 0.0),
              (x0c + bcor, ccor)], lw="grueso")
    vc.linea([(-0.07, hcor + 0.003), (0.12, hcor + 0.003)], lw="medio", color=AZUL)
    for y in (0.03, 0.075):
        vc.circulo((0.003, y), 0.9, fc=ROJO, ec=ROJO, lw="fino")
    vc.cota((x0c + bcor + 0.01, 0.0), (x0c + bcor + 0.01, hcor), offset_mm=3, lado=-1, h=1.3, decimales=3)
    h.titulo_vista(30, 278, "DETALLE UNIÓN CORREA - VIGA", "ESC. 1/5", ancho=62)
    yb = 250
    for t in ["Clip L 2\"x2\"x1/4\" soldado al cordón", "superior, 2 pernos ø 1/2\" A325", "por correa.",
              f"Correa {est.CORREA.nombre}", "Cordón sup. " + est.CORDON.nombre]:
        h.texto(100, yb, t, h=1.45)
        yb -= 3.3

    # Detalle canaleta ESC 1/10
    vg = h.vista(200, 222, 10, (0, 0))
    vg.poly(Polygon([(-0.15, -0.35), (0.0, -0.35), (0.0, 0.25), (-0.15, 0.25)]), fc="#9e9e9e", ec="k", lw="medio")
    vg.linea([(0.0, 0.30), (0.0, 0.08), (0.25, 0.08), (0.25, 0.28), (0.29, 0.28)], lw="grueso", color=AZUL)
    vg.linea([(-0.17, 0.26), (0.0, 0.32), (0.06, 0.29)], lw="medio", color="k")
    vg.linea([(0.12, 0.33), (0.62, 0.38)], lw="grueso", color=AZUL)
    vg.linea([(0.10, 0.08), (0.10, -0.35)], lw="medio", color=AZUL, ls=(0, (5, 2)))
    vg.cota((0.0, 0.08), (0.25, 0.08), offset_mm=4, lado=-1, h=1.3)
    vg.cota((0.25, 0.08), (0.25, 0.28), offset_mm=5, lado=1, h=1.3)
    _leader(vg, (0.45, 0.50), (0.45, 0.365), "cobertura TR-4 (pend. 10 %)", color=AZUL)
    _leader(vg, (0.45, -0.15), (0.10, -0.15), "bajada PVC ø 4\"", color=AZUL)
    _leader(vg, (-0.40, 0.0), (-0.15, 0.0), "cerco", ha="right")
    _leader(vg, (-0.40, 0.40), (-0.05, 0.30), "babeta", ha="right")
    h.titulo_vista(170, 278, "DETALLE CANALETA POSTERIOR", "ESC. 1/10", ancho=62)
    h.texto(170, 184, "Plancha galvanizada e=0.6 mm, desarrollo 0.60 m;", h=1.4)
    h.texto(170, 180.6, "soportes cada 1.00 m; pendiente 0.5 % hacia bajadas.", h=1.4)


    notas = [
        "CONCRETO: solado f'c = 100 kg/cm², e = 0.10 m; zapata y dado f'c = 210 kg/cm²; cemento Portland tipo I; agregado máx. 3/4\".",
        "ACERO: fy = 4200 kg/cm² (ASTM A615 Gr. 60). Recubrimiento libre: zapata 7.5 cm; dado 4.0 cm.",
        "Traslapes ø 1/2\" = 0.45 m; ø 5/8\" = 0.60 m. Ganchos estándar de 90° en extremos.",
        "Pernos de anclaje ASTM F1554 Gr. 36 con plantilla metálica; tolerancia de posición ±3 mm.",
        "Vaciar el dado en una sola etapa con los pernos fijados; curado mínimo 7 días.",
        f"Capacidad portante asumida qadm ≥ {est.Q_ADM_SUPUESTA / 98.07:.1f} kg/cm²: CONFIRMAR CON ESTUDIO DE MECÁNICA DE SUELOS (E.050).",
        "Si se encuentra relleno, material orgánico o nivel freático alto, consultar al ingeniero.",
    ]
    y = h.notas(278, "ESPECIFICACIONES DE CIMENTACIÓN", notas, h=1.45, ancho_chars=62)
    proceso = [
        "1. Trazo y replanteo de ejes según tabla de coordenadas (lámina E-01).",
        "2. Excavación hasta -1.30 m (incluye solado) y compactación del fondo.",
        "3. Solado, armadura de zapata y dado, plantilla de pernos.",
        "4. Vaciado de zapata, luego dado hasta +0.10 m.",
        "5. Relleno compactado por capas de 0.20 m al 95 % del Proctor modificado.",
        "6. Montaje de columnas sobre tuercas de nivelación y grout.",
    ]
    h.notas(y - 1, "PROCESO CONSTRUCTIVO", proceso, h=1.45, ancho_chars=62)
    h.guardar(pdf, os.path.join(png_dir, "E-04.png") if png_dir else None)


def generar(salida_dir, png_dir=None):
    os.makedirs(salida_dir, exist_ok=True)
    if png_dir:
        os.makedirs(png_dir, exist_ok=True)
    ruta = os.path.join(salida_dir, "Planos_Estacionamiento_Rodriguez_de_Mendoza.pdf")
    with PdfPages(ruta) as pdf:
        lamina_L01(pdf, png_dir)
        lamina_A01(pdf, png_dir)
        lamina_A02(pdf, png_dir)
        lamina_E01(pdf, png_dir)
        lamina_E02(pdf, png_dir)
        lamina_E03(pdf, png_dir)
        lamina_E04(pdf, png_dir)
        d = pdf.infodict()
        d["Title"] = "Estacionamiento techado - Rodríguez de Mendoza (anteproyecto)"
        d["Subject"] = "Planos de arquitectura y estructuras"
    return ruta


if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "salida"
    png = sys.argv[2] if len(sys.argv) > 2 else None
    print(generar(out, png))
