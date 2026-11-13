# -*- coding: utf-8 -*-
"""Láminas A3 del proyecto AZOTEA GYM (PDF multipágina + vistas previas PNG)."""
import os
import math
import datetime
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle, Polygon, Circle, FancyBboxPatch, Arc, FancyArrowPatch
from matplotlib import font_manager

import diseno as D

AQUI = os.path.dirname(os.path.abspath(__file__))
SALIDA = D.SALIDA
B = D.VERSION == "B"
FECHA = "Noviembre 2026"
if any("Inter" == f.name for f in font_manager.fontManager.ttflist):
    plt.rcParams["font.family"] = ["Inter", "DejaVu Sans"]
plt.rcParams["pdf.fonttype"] = 42
MM = 1 / 25.4
A3 = (420, 297)
TINTA, GRIS, ROJO = "#17181b", "#8a8d93", "#d81f26"
COL_ZONA = {k: v["color"] for k, v in D.ZONAS.items()}


# --------------------------------------------------------------------------- lámina
def nueva(codigo, titulo, escala, notas=()):
    fig = plt.figure(figsize=(A3[0] * MM, A3[1] * MM))
    marco = fig.add_axes([0, 0, 1, 1]); marco.set_xlim(0, A3[0]); marco.set_ylim(0, A3[1]); marco.axis("off")
    marco.add_patch(Rectangle((8, 8), A3[0] - 16, A3[1] - 16, fill=False, lw=1.2, ec=TINTA))
    x0 = A3[0] - 8 - 64
    marco.add_patch(Rectangle((x0, 8), 64, A3[1] - 16, fill=False, lw=1.0, ec=TINTA))
    marco.add_patch(Rectangle((x0, A3[1] - 8 - 46), 64, 46, fc=TINTA, ec=TINTA))
    marco.text(x0 + 32, A3[1] - 26, "AZOTEA", color="white", ha="center", va="center", fontsize=21, fontweight="black")
    marco.text(x0 + 32, A3[1] - 40, "GYM", color=ROJO, ha="center", va="center", fontsize=27, fontweight="black")
    y = A3[1] - 62

    def campo(rot, txt, alto=15, tam=8.5, negrita=False):
        nonlocal y
        marco.plot([x0, x0 + 64], [y + 4, y + 4], color=TINTA, lw=0.5)
        marco.text(x0 + 3, y, rot, fontsize=5.2, color=GRIS, va="top")
        marco.text(x0 + 3, y - 4.2, txt, fontsize=tam, color=TINTA, va="top", fontweight="bold" if negrita else "normal", linespacing=1.25)
        y -= alto

    campo("PROYECTO", "Gimnasio en azotea «Azotea Gym»\nVERSIÓN B · con zona de cardio" if B else "Gimnasio en azotea\n«Azotea Gym»", 18, 7.6 if B else 8.5)
    campo("UBICACIÓN", "Jr. San Miguel, Huambo\nRodríguez de Mendoza, Amazonas", 18, 7.2)
    campo("LÁMINA", titulo, 24, 8.6, True)
    campo("ESCALA", escala, 12)
    campo("FECHA", FECHA, 12)
    campo("BASE", "Plano de distribución (ago-2026)\nSS.HH. medidas de obra (nov-2026)\nTecho metálico (jul-2024)\nCatálogo Fitness Extreme 2026", 26, 6.2)
    if notas:
        marco.plot([x0, x0 + 64], [y + 4, y + 4], color=TINTA, lw=0.5)
        marco.text(x0 + 3, y, "NOTAS", fontsize=5.2, color=GRIS, va="top")
        marco.text(x0 + 3, y - 4.5, "\n".join(_envolver("• " + n, 46) for n in notas), fontsize=5.3, color=TINTA, va="top", linespacing=1.3)
    marco.add_patch(Rectangle((x0, 8), 64, 26, fc="white", ec=TINTA, lw=1.0))
    marco.text(x0 + 32, 21, codigo, ha="center", va="center", fontsize=30, fontweight="black", color=TINTA)
    return fig, marco


def eje(fig, x_mm, y_mm, xlim, ylim, escala):
    """Ejes a escala exacta; (x_mm, y_mm) es la esquina superior izquierda en la lámina; y crece hacia abajo."""
    w = (xlim[1] - xlim[0]) * 1000 / escala
    h = (ylim[1] - ylim[0]) * 1000 / escala
    ax = fig.add_axes([x_mm / A3[0], 1 - (y_mm + h) / A3[1], w / A3[0], h / A3[1]])
    ax.set_xlim(*xlim); ax.set_ylim(ylim[1], ylim[0]); ax.set_aspect("equal"); ax.axis("off")
    return ax


def rect(ax, r, **kw):
    p = Rectangle((r[0], r[1]), r[2] - r[0], r[3] - r[1], **kw); ax.add_patch(p); return p


def cota(ax, p1, p2, sep=0.35, txt=None, tam=5.6, color=TINTA):
    """Cota alineada entre p1 y p2, desplazada 'sep' m (perpendicular)."""
    (x1, y1), (x2, y2) = p1, p2
    L = math.hypot(x2 - x1, y2 - y1); nx, ny = -(y2 - y1) / L, (x2 - x1) / L
    a, b = (x1 + nx * sep, y1 + ny * sep), (x2 + nx * sep, y2 + ny * sep)
    ax.plot([a[0], b[0]], [a[1], b[1]], color=color, lw=0.45)
    for (px, py), (qx, qy) in ((p1, a), (p2, b)):
        ax.plot([px + nx * 0.05 * (1 if sep > 0 else -1), qx + nx * 0.08 * (1 if sep > 0 else -1)], [py + ny * 0.05 * (1 if sep > 0 else -1), qy + ny * 0.08 * (1 if sep > 0 else -1)], color=color, lw=0.3)
        ax.plot([qx - 0.06 * (nx + (x2 - x1) / L), qx + 0.06 * (nx + (x2 - x1) / L)], [qy - 0.06 * (ny + (y2 - y1) / L), qy + 0.06 * (ny + (y2 - y1) / L)], color=color, lw=0.7)
    ang = math.degrees(math.atan2(-(y2 - y1), x2 - x1))
    if ang > 90 or ang <= -90:
        ang += 180
    ax.text((a[0] + b[0]) / 2 + nx * 0.11 * (1 if sep > 0 else -1), (a[1] + b[1]) / 2 + ny * 0.11 * (1 if sep > 0 else -1),
            txt or ("%.2f" % L), fontsize=tam, color=color, ha="center", va="center", rotation=ang, rotation_mode="anchor")


# --------------------------------------------------------------------------- planta base
def planta_base(ax, ejes=True, textos=True, suave=False):
    c_muro = "#3a3c41" if not suave else "#9a9da3"
    # losa
    cont = [(0, D.Y_BLOQUE), (D.X_TRAG_E0, D.Y_BLOQUE), (D.X_TRAG_E0, 0), (D.L, 0), (D.L, D.W), (0, D.W)]
    ax.add_patch(Polygon(cont, closed=True, fc="#f6f5f2", ec="none", zorder=0))
    # tragaluces y vacío de escalera
    for t in D.TRAGALUCES:
        r = t["rect"]; rect(ax, r, fc="white", ec=GRIS, lw=0.5, zorder=1)
        ax.plot([r[0], r[2]], [r[1], r[3]], color=GRIS, lw=0.4, zorder=1); ax.plot([r[0], r[2]], [r[3], r[1]], color=GRIS, lw=0.4, zorder=1)
    e = D.ESCALERA["rect"]; rect(ax, e, fc="white", ec=GRIS, lw=0.5, zorder=1)
    es = D.ESCALERA["espina"]; rect(ax, es, fc="#d9d9d6", ec=TINTA, lw=0.4, zorder=2)
    for i in range(6):
        y = 1.17 - i * 0.2; ax.plot([es[2], e[2]], [y, y], color=GRIS, lw=0.35, zorder=1)
    for i in range(8):
        y = 0.45 + i * 0.2; ax.plot([e[0], es[0]], [y, y], color=GRIS, lw=0.35, zorder=1)
    cx, cy = (es[0] + es[2]) / 2, es[1]
    for k in range(1, 6):
        a = math.pi * k / 6; ax.plot([cx, cx - 1.25 * math.cos(a)], [cy, cy - 0.95 * math.sin(a)], color=GRIS, lw=0.35, zorder=1)
    ax.annotate("", xy=((D.X_VANO0 + D.X_VANO1) / 2, 2.55), xytext=((D.X_VANO0 + D.X_VANO1) / 2, 1.5), arrowprops=dict(arrowstyle="-|>", color=TINTA, lw=0.7), zorder=6)
    # muros
    for x0, y0, x1, y1, h, clave in D.MUROS:
        if clave == "bano":
            rect(ax, (x0, y0, x1, y1), fc=c_muro, ec=c_muro, lw=0.3, zorder=4)
        else:
            rect(ax, (x0, y0, x1, y1), fc="white", ec=c_muro, lw=0.5, hatch="////", zorder=3)
    for x0, y0, x1, y1, h in D.COLUMNAS:
        rect(ax, (x0, y0, x1, y1), fc=TINTA if not suave else GRIS, ec="none", zorder=5)
    # puertas de baños
    for p in D.PUERTAS:
        a = p["ancho"]; xb = p["x1"] if p["bisagra"] == "x1" else p["x0"]
        ax.plot([xb, xb], [p["y"], p["y"] - a], color="#2a9a4b", lw=0.8, zorder=6)
        ax.add_patch(Arc((xb, p["y"]), 2 * a, 2 * a, theta1=(180 if p["bisagra"] == "x1" else 270) if False else 0, theta2=0, color="#2a9a4b", lw=0.5))
        t1, t2 = ((180, 270) if p["bisagra"] == "x1" else (270, 360))
        ax.add_patch(Arc((xb, p["y"]), 2 * a, 2 * a, theta1=t1, theta2=t2, color="#2a9a4b", lw=0.5, zorder=6))
    # aparatos y duchas
    for b in D.BANOS:
        rect(ax, b["ducha"], fc="#e6eef1", ec="#7fa3b3", lw=0.4, hatch="xx", zorder=2)
        ix, iy = b["inodoro"]; ax.add_patch(FancyBboxPatch((ix - 0.17, iy - 0.18), 0.34, 0.46, boxstyle="round,pad=0,rounding_size=0.15", fc="white", ec="#2f7f9f", lw=0.5, zorder=3))
        rect(ax, (ix - 0.2, iy - 0.38, ix + 0.2, iy - 0.18), fc="white", ec="#2f7f9f", lw=0.5, zorder=3)
        lx, ly = b["lavatorio"]; ax.add_patch(FancyBboxPatch((lx - 0.2, ly - 0.16), 0.4, 0.32, boxstyle="round,pad=0,rounding_size=0.1", fc="white", ec="#2f7f9f", lw=0.5, zorder=3))
    # tanque, lavadero
    tq = D.TANQUE; rect(ax, tq["plataforma"], fc="none", ec="#e07b00", lw=0.7, zorder=6)
    ax.add_patch(Circle(tq["centro"], tq["diam"] / 2, fc="#eef3fb", ec="#1f4fa3", lw=0.9, zorder=6))
    lv = D.LAVADERO["rect"]; rect(ax, lv, fc="#eeeeea", ec=TINTA, lw=0.5, zorder=5)
    ym = (lv[1] + lv[3]) / 2
    for a, b in ((lv[1] + 0.06, ym - 0.04), (ym + 0.04, lv[3] - 0.06)):
        rect(ax, (lv[0] + 0.06, a, lv[2] - 0.06, b), fc="white", ec=GRIS, lw=0.4, zorder=6)
    if textos:
        kw = dict(fontsize=4.6, color="#3a3c41", ha="center", va="center", zorder=8)
        ax.text(1.28, 1.25, "SS.HH. 1\n+ DUCHA\n2.83 m²", **kw); ax.text(3.0, 1.45, "SS.HH. 2\n1.86 m²", **kw)
        ax.text((D.X_TRAG_E0 + D.X_TRAG_E1) / 2, 1.1, "TRAGALUZ E\n(existente)", rotation=90, **kw)
        ax.text(0.54, 2.5, "TQ-1\n1100 L", **dict(kw, fontsize=4.4, color="#1f4fa3"))
        ax.text(1.355, 2.64, "LAVADERO", rotation=90, **dict(kw, fontsize=4.2))
        ax.text(5.7, 0.36, "ESCALERA", **dict(kw, fontsize=4.4)); ax.text(7.02, 1.62, "LLEGA", **dict(kw, fontsize=4.0))
        ax.text(1.4, 1.755, "", **kw)
        ax.text(2.1, 1.93, "P-1", **dict(kw, fontsize=3.8, color="#2a9a4b")); ax.text(2.83, 2.17, "P-2", **dict(kw, fontsize=3.8, color="#2a9a4b"))
    if ejes:
        for k, x in D.EJES.items():
            ax.plot([x, x], [-0.75, D.W + 0.2], color="#b5b7bc", lw=0.35, ls=(0, (8, 3, 1.5, 3)), zorder=0.5)
            ax.add_patch(Circle((x, -1.0), 0.22, fc="white", ec=GRIS, lw=0.5, clip_on=False, zorder=9))
            ax.text(x, -1.0, k, fontsize=5.6, ha="center", va="center", color=TINTA, zorder=10)
        ax.text(-0.62, D.W / 2 + 0.6, "LADO MERCADO", rotation=90, fontsize=5.4, color=GRIS, ha="center", va="center")
        ax.text(D.L + 0.58, D.W / 2 + 1.4, "LADO CALLE", rotation=-90, fontsize=5.4, color=GRIS, ha="center", va="center")


def dibujar_maquinas(ax, etiquetas=True, relleno=True, nombres=True, alpha=0.26):
    for m in D.MAQUINAS:
        r = D.rect_maquina(m); col = COL_ZONA[m["zona"]]
        ax.add_patch(FancyBboxPatch((r[0] + 0.02, r[1] + 0.02), r[2] - r[0] - 0.04, r[3] - r[1] - 0.04, boxstyle="round,pad=0,rounding_size=0.05",
                                    fc=col if relleno else "white", alpha=1, ec="none", zorder=6.4)).set_alpha(alpha if relleno else 1)
        ax.add_patch(FancyBboxPatch((r[0] + 0.02, r[1] + 0.02), r[2] - r[0] - 0.04, r[3] - r[1] - 0.04, boxstyle="round,pad=0,rounding_size=0.05",
                                    fc="none", ec=TINTA, lw=0.7, zorder=6.5))
        # marca del frente de uso
        cx, cy = m["c"]; f = m["frente"]
        dx, dy = {"N": (0, -1), "S": (0, 1), "E": (1, 0), "O": (-1, 0)}[f]
        hx, hy = (r[2] - r[0]) / 2, (r[3] - r[1]) / 2
        px, py = cx + dx * (hx - 0.02), cy + dy * (hy - 0.02)
        tx, ty = -dy, dx
        ax.add_patch(Polygon([(px + tx * 0.11, py + ty * 0.11), (px - tx * 0.11, py - ty * 0.11), (px + dx * 0.13, py + dy * 0.13)], fc=TINTA, ec="none", zorder=7))
        if etiquetas:
            n = int(m["id"][1:])
            ax.add_patch(Circle((cx, cy - (0.13 if nombres else 0)), 0.17, fc=TINTA, ec="none", zorder=8))
            ax.text(cx, cy - (0.13 if nombres else 0), str(n), fontsize=5.0, color="white", ha="center", va="center", fontweight="bold", zorder=9)
            if nombres:
                nom = m["nombre"].replace("Máquina ", "").replace(" olímpico", "\nolímpico").replace(" + ", "\n+ ").replace("graduable pro", "grad. pro")
                vert = (r[3] - r[1]) > 1.45 * (r[2] - r[0]) and (r[2] - r[0]) < 0.9
                ax.text(cx, cy + 0.2, nom, fontsize=3.9, color=TINTA, ha="center", va="top" if not vert else "center", rotation=90 if vert else 0, zorder=9, linespacing=1.0)
    for x, y in D.PORTA_DISCOS:
        ax.add_patch(Circle((x, y), 0.26, fc="white", ec=TINTA, lw=0.5, zorder=6.5)); ax.text(x, y, "PD", fontsize=3.6, ha="center", va="center", zorder=7)


def dibujar_recepcion(ax, textos=True):
    R = D.RECEPCION
    for p in D.PISOS:
        if p["id"] == "vinilico":
            ax.add_patch(Polygon(p["poligono"], closed=True, fc="#f3e3c8", ec="none", zorder=0.6))
        if p["id"] == "grass":
            rect(ax, p["rect"], fc="#cfe8c6", ec="#3f8f3a", lw=0.6, zorder=0.7)
        if p["id"] == "caucho_pl":
            r = p["rect"]; ax.plot([r[0], r[2], r[2]], [r[3], r[3], r[1]], color=ROJO, lw=0.6, ls="--", zorder=0.8)
        if p["id"] == "caucho_cardio":
            r = p["rect"]; ax.plot([r[0], r[0], r[2], r[2]], [r[3], r[1], r[1], r[3]], color=ROJO, lw=0.6, ls="--", zorder=0.8)
    if D.ZONA_SEGURIDAD:
        rect(ax, D.ZONA_SEGURIDAD, fc="#fff3c4", ec="#d99a00", lw=0.6, ls="--", hatch="///", alpha=0.75, zorder=0.9)
        if textos:
            zs = D.ZONA_SEGURIDAD; ax.text((zs[0] + zs[2]) / 2, (zs[1] + zs[3]) / 2, "ZONA LIBRE DE SEGURIDAD\n1.00 m detrás de las cintas", fontsize=3.7, color="#8a5d00", ha="center", va="center", zorder=9)
    rect(ax, R["mostrador"], fc="#c9925a", ec=TINTA, lw=0.7, zorder=6)
    rect(ax, R["panel_marca"], fc=ROJO, ec=TINTA, lw=0.5, zorder=6)
    la = R["lockers"]; rect(ax, la, fc="#d7d9dd", ec=TINTA, lw=0.6, zorder=6)
    for i in range(1, 4):
        y = la[1] + i * (la[3] - la[1]) / 4; ax.plot([la[0], la[2]], [y, y], color=TINTA, lw=0.35, zorder=7)
    rect(ax, R["banca"], fc="#e3c9a1", ec=TINTA, lw=0.5, zorder=6)
    rect(ax, R["estante"], fc="#e9e9e6", ec=TINTA, lw=0.4, zorder=6)
    mo = R["mostrador"]
    ax.add_patch(Circle((5.55, (mo[1] + mo[3]) / 2 + 0.15), 0.17, fc="white", ec=TINTA, lw=0.5, zorder=6))
    for x0, y0, x1, y1, h in D.CELOSIAS:
        ax.plot([x0, x1], [y0, y1], color="#a8763e", lw=1.6, zorder=6)
    for a, b in D.ESPEJOS:
        ax.plot([a, b], [D.T + 0.03, D.T + 0.03], color="#39a0c8", lw=1.5, zorder=6)
    if textos:
        kw = dict(fontsize=4.2, color=TINTA, ha="center", va="center", zorder=9)
        ax.text(6.25, (mo[1] + mo[3]) / 2, "MOSTRADOR", rotation=90, **dict(kw, fontsize=3.9))
        ax.text(4.81, 2.82, "LOCKERS (12)", rotation=90, **dict(kw, fontsize=3.8))
        ax.text(5.56, mo[3] - 0.3, "RECEPCIÓN", **dict(kw, fontsize=4.4, fontweight="bold"))
        ax.text(3.65, 2.41, "banca", **dict(kw, fontsize=3.6))
        if D.ZONA_FUNCIONAL:
            zf = D.ZONA_FUNCIONAL; ax.text((zf[0] + zf[2]) / 2, (zf[1] + zf[3]) / 2, "ZONA FUNCIONAL\nY ESTIRAMIENTO\ngrass sintético", **dict(kw, fontsize=4.6, color="#2f6d2c"))
        ax.text(sum(D.ESPEJOS[0]) / 2, 0.02, "ESPEJOS 4.00 x 1.80 m", **dict(kw, fontsize=3.8, color="#1f7fa8", va="bottom"))
        ax.text(2.9, 2.82 if B else 3.05, "VESTÍBULO\nDE SERVICIOS", **dict(kw, fontsize=4.2))


def tabla(marco, x, y, cols, filas, anchos, alto=4.4, tam=5.4, titulo=None):
    """Tabla simple en mm sobre el marco de la lámina; (x, y) esquina superior izquierda."""
    if titulo:
        marco.text(x, y + 2.2, titulo, fontsize=6.6, fontweight="bold", color=TINTA, va="bottom")
    xs = [x]
    for a in anchos:
        xs.append(xs[-1] + a)
    marco.add_patch(Rectangle((x, y - alto), xs[-1] - x, alto, fc=TINTA, ec=TINTA, lw=0.4))
    for i, c in enumerate(cols):
        marco.text(xs[i] + 1.2, y - alto / 2, c, fontsize=tam, color="white", va="center", fontweight="bold")
    for j, f in enumerate(filas):
        yy = y - alto * (j + 1)
        marco.add_patch(Rectangle((x, yy - alto), xs[-1] - x, alto, fc="#f3f3f1" if j % 2 else "white", ec="#c9cbd0", lw=0.25))
        for i, c in enumerate(f):
            der = isinstance(c, (int, float))
            marco.text(xs[i + 1] - 1.2 if der else xs[i] + 1.2, yy - alto / 2, ("{:,}".format(c) if isinstance(c, int) else ("%.2f" % c if isinstance(c, float) else str(c))),
                       fontsize=tam, color=TINTA, va="center", ha="right" if der else "left")
    return y - alto * (len(filas) + 1)


XL, YL = (-0.95, D.L + 0.72), (-1.45, D.W + 1.15)      # ventana de la planta general


# --------------------------------------------------------------------------- láminas
def A01():
    fig, mk = nueva("A-01", "Planta de distribución\npropuesta", "1 / 50",
                    ["Triángulo negro = lado de uso de cada máquina.", "Máquinas pesadas alineadas con las vigas de los ejes, como en el plano de distribución base.",
                     "Medidas generales según plano base; baños según medidas de obra. Verificar en sitio (lámina V-01)."]
                    + (["Versión B: 2 cintas y 2 bicicletas en la esquina del lado mercado; se conservan las 13 máquinas y se elimina la zona funcional."] if B else []))
    ax = eje(fig, 12, 14, XL, YL, 50)
    planta_base(ax); dibujar_recepcion(ax); dibujar_maquinas(ax)
    cota(ax, (0, D.W), (D.L, D.W), 0.75, "%.2f  (plano base 14.62 + 0.35 por medida de obra del baño)" % D.L)
    cota(ax, (D.L, 0), (D.L, D.W), -0.38, "%.2f" % D.W)
    ar = D.areas()
    filas = [(int(m["id"][1:]), m["nombre"], m["dim_cat"], D.ZONAS[m["zona"]]["nombre"], m["precio"]) for m in D.MAQUINAS]
    yf = tabla(mk, 14, 94, ["N.º", "Equipo (Catálogo Fitness Extreme 2026)", "Alto x ancho x largo", "Zona", "Precio S/"], filas, [9, 62, 50, 36, 20], alto=4.0 if B else 4.6, tam=5.1 if B else 5.4, titulo="RELACIÓN DE MÁQUINAS")
    mk.text(14 + 177 - 1.2, yf - 3, "Total máquinas  S/ {:,}".format(sum(m["precio"] for m in D.MAQUINAS)), fontsize=6.6, fontweight="bold", ha="right", va="center")
    x2 = 204
    mk.text(x2, 96.2, "ZONAS", fontsize=6.6, fontweight="bold", va="bottom")
    for i, (k, z) in enumerate(D.ZONAS.items()):
        mk.add_patch(Rectangle((x2, 89 - i * 6.2), 6, 4, fc=z["color"], alpha=0.45, ec=TINTA, lw=0.4)); mk.text(x2 + 8, 91 - i * 6.2, z["nombre"], fontsize=5.8, va="center")
    mk.text(x2, 48, "CUADRO DE ÁREAS", fontsize=6.6, fontweight="bold", va="bottom")
    datos = [("Área techada de azotea", "%.1f m²" % ar["techada"]), ("Sala de entrenamiento y hall", "%.1f m²" % ar["sala"]), ("SS.HH. y duchas (construidos)", "%.2f m²" % ar["banos"]),
             ("Huella de máquinas", "%.1f m²  (%d %%)" % (ar["huella_maquinas"], ar["ocupacion"])), ("Aforo simultáneo recomendado", "%d personas" % ar["aforo"]), ("Lockers", "12")]
    for i, (a, b) in enumerate(datos):
        mk.text(x2, 43 - i * 5.6, a, fontsize=5.8, va="center"); mk.text(x2 + 132, 43 - i * 5.6, b, fontsize=5.8, va="center", ha="right", fontweight="bold")
        mk.plot([x2, x2 + 132], [40.4 - i * 5.6, 40.4 - i * 5.6], color="#c9cbd0", lw=0.25)
    x3 = 270
    mk.text(x3, 96.2, "SIMBOLOGÍA", fontsize=6.6, fontweight="bold", va="bottom")
    sim = [("PD", "Porta discos"), ("▲", "Lado de uso"), ("╳", "Tragaluz (no se cubre)"), ("—", "Celosía de listones"), ("—", "Espejo"), ("- -", "Límite peso libre (caucho 25 mm)")]
    colr = [TINTA, TINTA, GRIS, "#a8763e", "#39a0c8", ROJO]
    for i, (s, t) in enumerate(sim):
        mk.text(x3 + 2.5, 91 - i * 6.2, s, fontsize=6, va="center", ha="center", color=colr[i], fontweight="bold"); mk.text(x3 + 8, 91 - i * 6.2, t, fontsize=5.8, va="center")
    return fig


def A02():
    fig, mk = nueva("A-02", "Cotas, circulación\ny evacuación", "1 / 50",
                    ["Una sola salida: la escalera. Aforo máximo recomendado: %d personas." % D.areas()["aforo"],
                     "Paso principal ≥ 1.10 m; acceso lateral a máquinas ≥ 0.55 m.", "Recorrido máximo de evacuación ≈ 17 m (menor que 45 m, RNE A.130).",
                     "Extintor PQS 6 kg junto a la salida y en el lado calle; luces de emergencia sobre la ruta."])
    ax = eje(fig, 12, 14, XL, YL, 50)
    planta_base(ax, textos=False); dibujar_recepcion(ax, textos=False); dibujar_maquinas(ax, nombres=False, alpha=0.14)
    # ruta principal y ramales
    vx = (D.X_VANO0 + D.X_VANO1) / 2
    rutas = [[(vx, 2.35), (vx, 3.62), (9.95, 3.62), (10.02, 4.8), (12.85, 4.8), (12.85, 1.95)],
             [(vx, 3.62), (6.75, 4.45), (5.0, 4.45), (4.2, 3.95), (3.0, 3.55), (2.45, 2.55)], [(3.0, 3.55), (2.3, 3.62), (2.3, 4.25)], [(10.0, 3.62), (10.1, 1.6), (11.6, 1.75)]]
    flechas = [((12.85, 2.6), (12.85, 4.0)), ((11.8, 4.8), (10.6, 4.8)), ((9.0, 3.62), (7.8, 3.62)), ((3.4, 3.7), (4.4, 4.1)), ((5.4, 4.45), (6.4, 4.45)), ((vx, 3.3), (vx, 2.5))]
    if B:
        rutas = [[(vx, 2.35), (vx, 3.62), (9.95, 3.62), (10.15, 4.92), (12.55, 4.95), (12.58, 1.95)],
                 [(vx, 3.62), (6.75, 3.97), (5.0, 3.97), (4.3, 3.6), (3.0, 2.92), (2.45, 2.5)], [(3.0, 2.92), (1.76, 3.7), (1.73, 4.65)], [(10.0, 3.62), (10.12, 1.9), (11.9, 1.95)]]
        flechas = [((12.58, 2.6), (12.58, 4.2)), ((11.8, 4.94), (10.7, 4.92)), ((9.0, 3.62), (7.8, 3.62)), ((3.3, 3.08), (4.2, 3.55)), ((5.3, 3.97), (6.3, 3.96)), ((vx, 3.3), (vx, 2.5))]
    for i, r in enumerate(rutas):
        ax.plot([p[0] for p in r], [p[1] for p in r], color="#2a9a4b", lw=2.2 if i == 0 else 1.5, alpha=0.75, solid_capstyle="round", zorder=5.5, ls="-" if i < 2 else (0, (3, 2)))
    for (a, b) in flechas:
        ax.annotate("", xy=b, xytext=a, arrowprops=dict(arrowstyle="-|>", color="#1c7a38", lw=1.0), zorder=9)
    ax.text(vx + 0.04, 1.86, "SALIDA", fontsize=5.4, color="white", ha="center", va="center", fontweight="bold", zorder=10, bbox=dict(boxstyle="round,pad=0.25", fc="#2a9a4b", ec="none"))
    for x, y in D.EXTINTORES:
        ax.add_patch(Circle((x, y), 0.14, fc=ROJO, ec="white", lw=0.5, zorder=10)); ax.text(x, y, "E", fontsize=4.2, color="white", ha="center", va="center", fontweight="bold", zorder=11)
    for x, y in D.LUCES_EMERGENCIA:
        ax.add_patch(Rectangle((x - 0.14, y - 0.08), 0.28, 0.16, fc="#f2c200", ec=TINTA, lw=0.4, zorder=10))
    # cotas generales y pasos libres
    M = {m["id"]: D.rect_maquina(m) for m in D.MAQUINAS}; R = D.RECEPCION
    cota(ax, (0, D.W), (D.L, D.W), 0.8, "%.2f" % D.L); cota(ax, (D.L, 0), (D.L, D.W), -0.38)
    xs = [0, D.X_BANO_D + D.T, D.X_ESC1 + D.T, D.L]
    for a, b in zip(xs, xs[1:]):
        cota(ax, (a, D.W), (b, D.W), 0.42)
    cota(ax, (0, D.Y_BLOQUE), (0, 2.05), 0.38); cota(ax, (0, 2.05), (0, D.W), 0.38)

    def paso(p, q, sep=0.0, col=ROJO):
        cota(ax, p, q, sep, None, 5.2, col)
    if B:
        zs = D.ZONA_SEGURIDAD
        for p, q in [((4.8, R["lockers"][3]), (4.8, M["M11"][1])), ((6.25, R["mostrador"][3]), (6.25, M["M11"][1])), ((8.45, M["M05"][3]), (8.45, M["M10"][1])),
                     ((M["M15"][2], 5.9), (M["M11"][0], 5.9)), ((M["M11"][2], 5.9), (M["M10"][0], 5.9)), ((M["M10"][2], 5.75), (M["M09"][0], 5.75)),
                     ((9.0, M["M01"][3]), (9.0, M["M05"][1])), ((13.9, M["M04"][3]), (13.9, M["M07"][1])), ((2.6, 2.05), (2.6, zs[1])), ((3.55, zs[1]), (3.55, zs[3])),
                     ((D.X_VANO0, 2.42), (D.X_VANO1, 2.42)), ((M["M06"][2], 2.7), (M["M12"][0], 2.7)), ((11.77, M["M03"][3]), (11.77, M["M12"][1])),
                     ((11.77, M["M12"][3]), (11.77, M["M09"][1])), ((M["M12"][2], 3.0), (M["M07"][0], 3.0)), ((M["M16"][2], 4.62), (M["M14"][0], 4.62))]:
            paso(p, q, 0.0)
    else:
        paso((M["M11"][2] - 0.25, R["lockers"][3]), (M["M11"][2] - 0.25, M["M11"][1]), 0.0)
        paso((6.25, R["mostrador"][3]), (6.25, M["M13"][1]), 0.0)
        paso((8.45, M["M05"][3]), (8.45, M["M10"][1]), 0.0)
        paso((M["M12"][2], 5.3), (M["M11"][0], 5.3), 0.0); paso((M["M11"][2], 5.9), (M["M13"][0], 5.9), 0.0); paso((M["M13"][2], 5.9), (M["M10"][0], 5.9), 0.0)
        paso((M["M10"][2], 5.75), (M["M09"][0], 5.75), 0.0); paso((9.0, M["M01"][3]), (9.0, M["M05"][1]), 0.0)
        paso((13.9, M["M04"][3]), (13.9, M["M07"][1]), 0.0); paso((13.9, M["M07"][3]), (13.9, M["M08"][1]), 0.0)
        paso((2.9, 2.05), (2.9, M["M11"][1]), 0.0); paso((D.X_VANO0, 2.42), (D.X_VANO1, 2.42), 0.0)
        paso((11.2, D.ZONA_FUNCIONAL[3]), (11.2, M["M09"][1]), 0.0)
    filas = [(d, v, mn, "Conforme" if ok else "REVISAR") for d, v, mn, ok in D.verificar()]
    if B:
        filas = [f for f in filas if not any(k in f[0] for k in ("bíceps dual", "Extensión dual", "Aductor dual"))]
    tabla(mk, 14, 94, ["Verificación", "Valor (m)", "Mínimo (m)", "Estado"], filas[:24], [92, 18, 20, 20], alto=3.45 if B else 3.95, tam=4.6 if B else 4.9, titulo="PASOS LIBRES Y ALTURAS (calculados por diseno.py)")
    x2 = 176
    mk.text(x2, 96.2, "LEYENDA", fontsize=6.6, fontweight="bold", va="bottom")
    ley = [("#2a9a4b", "Circulación principal y ruta de evacuación"), (ROJO, "Paso libre mínimo (m)"), (ROJO, "E  Extintor PQS 6 kg"), ("#f2c200", "Luz de emergencia"), (TINTA, "Cota general (m)")]
    for i, (c, t) in enumerate(ley):
        mk.add_patch(Rectangle((x2, 89 - i * 6.2), 6, 2.4, fc=c, ec="none")); mk.text(x2 + 8, 90.2 - i * 6.2, t, fontsize=5.8, va="center")
    mk.text(x2, 52, "CRITERIOS", fontsize=6.6, fontweight="bold", va="bottom")
    crit = ["La llegada de la escalera queda libre 1.50 m al frente: allí se registra el ingreso.", "Frente de los baños P-1 / P-2 libre 2.47 m: no hay máquinas frente a las puertas.",
            "El lavadero conserva su acceso por el vestíbulo de servicios.", "Los tragaluces E y SO no se cubren ni se usan como depósito.",
            "Equipos de más de 2.20 m (crossover, dominadas) bajo techo ≥ 2.48 m.", "Barras olímpicas con 0.45–0.60 m libres en cada extremo para cargar discos."]
    if B:
        crit = ["Frente a la escalera quedan 2.30 m libres; el hall entre mostrador y hip thrust mide 1.10 m.", "Detrás de las cintas: 1.00 m de zona de seguridad marcada en el piso y luego 1.20 m de paso a los baños.",
                "Cintas donde el techo es más alto (2.73 m): un corredor de 1.85 m tiene 0.53 m libres.", "El lavadero conserva su acceso; los tragaluces E y SO no se cubren.",
                "Dominadas (2.23 m) bajo techo de 2.43 m; crossover (2.30 m) bajo techo de 2.48 m.", "Barras olímpicas con 0.45–0.90 m libres en cada extremo para cargar discos."]
    for i, t in enumerate(crit):
        mk.text(x2, 47 - i * 6.0, "• " + t, fontsize=5.6, va="center")
    return fig


def A03():
    fig, mk = nueva("A-03", "Comparativo: plano base\nvs. propuesta", "1 / 75",
                    ["Se conservan las 13 máquinas del plano base y se suman 2 cintas y 2 bicicletas.", "Prensa, crossover, extensión, aductor, mancuernero y bancos no se mueven."] if B else
                    ["Sala este: se conserva la ubicación del plano de distribución.", "Sala oeste: 3 equipos reubicados por los baños construidos y la recepción."])
    xl, yl = (-1.0, D.L + 1.0), (-1.35, D.W + 0.6)
    for k, (yy, tit) in enumerate([(16, "PLANO BASE (agosto 2026) sobre la obra actual"), (142, "VERSIÓN B: cardio en la esquina del lado mercado y peso libre reunido" if B else "PROPUESTA: sala oeste reorganizada")]):
        ax = eje(fig, 16, yy + 8, xl, yl, 75)
        mk.text(16, A3[1] - yy - 3, tit, fontsize=8.5, fontweight="bold", va="center")
        planta_base(ax, textos=False)
        if k == 0:
            for m in D.MAQUINAS:
                if m["zona"] == "cardio":
                    continue
                r = D.MAQUINAS_P1.get(m["id"], D.rect_maquina(m)); mov = m["id"] in D.MAQUINAS_P1
                rect(ax, r, fc="#f7c9c9" if mov else "#e8e8e6", ec=ROJO if mov else GRIS, lw=0.8 if mov else 0.5, zorder=6)
                ax.text((r[0] + r[2]) / 2, (r[1] + r[3]) / 2, str(int(m["id"][1:])), fontsize=5.6, ha="center", va="center", zorder=8, fontweight="bold")
            notas = [((5.6, 3.9), "Sin recepción: el ingreso\nda directo a las máquinas"), ((2.65, 6.25), "Barra del press contra el\nmuro: no se pueden cargar discos"),
                     ((5.45, 4.25), "Hip thrust frente a la llegada:\npaso de 0.90 m hacia los baños"), ((2.5, 2.6), "Baños construidos: puertas P-1 y\nP-2 abren a este vestíbulo")]
            if B:
                notas = [((5.6, 3.4), "Sin recepción y sin\nmáquinas de cardio"), ((2.65, 6.25), "Barra del press contra el\nmuro: no se pueden cargar discos"),
                         ((2.5, 2.6), "Baños construidos: puertas P-1 y\nP-2 abren a este vestíbulo"), ((12.2, 2.9), "Centro de la sala libre")]
            for (x, y), t in notas:
                ax.text(x, y, t, fontsize=4.6, color=ROJO, ha="center", va="center", zorder=10, bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=ROJO, lw=0.5))
        else:
            dibujar_recepcion(ax, textos=False); dibujar_maquinas(ax, nombres=False)
            for mid in D.MAQUINAS_P1:
                r0 = D.MAQUINAS_P1[mid]; m = next(q for q in D.MAQUINAS if q["id"] == mid)
                rect(ax, r0, fc="none", ec=ROJO, lw=0.5, ls="--", zorder=5)
                ax.add_patch(FancyArrowPatch(((r0[0] + r0[2]) / 2, (r0[1] + r0[3]) / 2 - 0.5), (m["c"][0], m["c"][1] - 0.5), arrowstyle="-|>", mutation_scale=7, color=ROJO, lw=0.9, connectionstyle="arc3,rad=-0.3", zorder=10))
    filas = [("12  Press plano olímpico", "Pasa a la esquina del lado mercado, con la barra a 0.45 m del muro.", "Se pueden cargar discos por ambos extremos; el ayudante cabe detrás."),
             ("11  Hip thrust", "Se corre 1.70 m hacia el lado mercado (sobre la viga del eje 6).", "Libera el hall de llegada y deja 2.47 m frente a los baños."),
             ("13  Dominadas asistidas", "Pasa entre el hip thrust y la prensa, frente a la recepción.", "Equipo esbelto (1.15 m): deja 1.53 m de hall. Techo libre 2.62 m."),
             ("Recepción y lockers", "Mostrador junto a la llegada de escalera; 12 lockers a su espalda.", "Control de ingreso, cobro y guardado sin invadir la sala."),
             ("Zona funcional", "Grass sintético 2.40 x 2.20 m al centro de la sala este.", "Calentamiento y estiramiento; no existía en el plano base.")]
    if B:
        filas = [("14–17  Cintas y bicicletas", "2 trotadoras y 2 bicicletas en la esquina del lado mercado, frente a un ventanal.", "Es donde el techo es más alto (2.73 m); cinta 1 sobre la viga del eje 6 y baños a un paso."),
                 ("12  Press plano olímpico", "Pasa al centro de la sala este, donde estaba la zona funcional.", "El peso libre queda reunido: mancuernas, bancos y press, con las barras libres en ambos extremos."),
                 ("13  Dominadas asistidas", "Pasa al muro del fondo, sobre la viga del eje 2.", "Deja su esquina a las bicicletas. Techo libre de 2.43 m sobre un equipo de 2.23 m."),
                 ("2 y 3  Porta barras y tríceps", "El tríceps se corre 1.00 m; el porta barras pasa entre extensión y aductor.", "Hacen sitio a las dominadas en el muro del fondo."),
                 ("Lo que se cede", "Se elimina la zona funcional de grass y el mostrador baja de 1.50 a 1.20 m.", "Es el costo de sumar cuatro equipos sin retirar ninguno: la ocupación sube de 38 % a 45 %.")]
    tabla(mk, 232, 262, ["Elemento", "Cambio", "Por qué"], filas, [28, 54, 0], alto=0.1, tam=0.1)
    # tabla manual con texto ajustado (columna derecha)
    x, y = 232, 262
    mk.add_patch(Rectangle((x - 2, 60), 116, 215, fc="white", ec="none", zorder=3))
    mk.text(x, 268, "QUÉ CAMBIA Y POR QUÉ", fontsize=8.5, fontweight="bold", va="center", zorder=4)
    for i, (a, b, c) in enumerate(filas):
        yy = 256 - i * 37
        mk.add_patch(Rectangle((x, yy - 30), 110, 33, fc="#f6f5f2", ec="#c9cbd0", lw=0.3, zorder=4))
        mk.text(x + 3, yy - 2.5, a, fontsize=7.4, fontweight="bold", va="center", color=ROJO, zorder=5)
        mk.text(x + 3, yy - 10, _envolver(b, 62), fontsize=6.2, va="top", zorder=5, linespacing=1.3)
        mk.text(x + 3, yy - 20.5, _envolver("→ " + c, 62), fontsize=6.2, va="top", color="#3a3c41", zorder=5, linespacing=1.3, style="italic")
    return fig


def _envolver(t, n):
    import textwrap
    return "\n".join(textwrap.wrap(t, n))


def A04():
    fig, mk = nueva("A-04", "Recepción, lockers y\nvestíbulo de servicios", "1 / 30  y  1 / 25",
                    ["Mostrador: estructura de melamina 18 mm, frente de listones de madera, tablero negro.", "Panel de marca: bastidor metálico + MDF 15 mm, vinil y LED perimetral.",
                     "Muro de luz: policarbonato alveolar opal 8 mm de +1.00 a +2.40 sobre el muro del tragaluz E."])
    xl, yl = (1.5, 7.9), (1.6, 5.3)
    ax = eje(fig, 16, 18, xl, yl, 30)
    planta_base(ax, ejes=False); dibujar_recepcion(ax); dibujar_maquinas(ax, alpha=0.12)
    R = D.RECEPCION; mo, lo, pa, ba = R["mostrador"], R["lockers"], R["panel_marca"], R["banca"]
    cota(ax, (mo[2], mo[1]), (mo[2], mo[3]), -0.28); cota(ax, (mo[0], mo[3]), (mo[2], mo[3]), 0.22)
    cota(ax, (lo[0], lo[1]), (lo[0], lo[3]), 0.25); cota(ax, (lo[0], lo[3]), (pa[2], lo[3]), 0.2); cota(ax, (pa[2], mo[3]), (mo[0], mo[3]), 0.22 if not B else 0.45)
    cota(ax, (ba[0], ba[3]), (ba[2], ba[3]), 0.2); cota(ax, (D.X_VANO0, 2.3), (D.X_VANO1, 2.3), 0.0, None, 5.4, ROJO)
    cota(ax, (1.63, 4.1 if not B else 3.05), (lo[0], 4.1 if not B else 3.05), 0.0, None, 5.4, ROJO); cota(ax, (2.2, 2.05), (2.2, 4.52 if not B else 3.25), 0.0, None, 5.4, ROJO)
    for (x, y), t in [((5.56, 2.36), "estante de productos"), ((7.84, 2.35), "dispensador\nde agua"), ((1.2, 3.62), "celosía de listones h = 2.20"), ((4.3, 1.75), "muro de luz (policarbonato opal)")]:
        ax.text(x, y, t, fontsize=4.6, ha="center", va="center", color="#3a3c41", zorder=12, bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85))
    for t in ax.texts:
        t.set_clip_on(True)
    mk.text(16, A3[1] - 13.5, "PLANTA  1 / 30", fontsize=8, fontweight="bold")
    # elevación del conjunto visto desde el ingreso (mirando al oeste) 1/25
    ex = eje(fig, 16, 160, (2.0, 4.3), (-2.55, 0.15), 25)
    ex.set_ylim(0.15, -2.55)   # z hacia arriba = negativo
    mk.text(16, A3[1] - 155, "ELEVACIÓN DESDE EL INGRESO (mirando al lado mercado)  1 / 25", fontsize=8, fontweight="bold")
    ex.plot([2.0, 4.3], [0, 0], color=TINTA, lw=1.0)
    y1 = mo[3]; ym = (2.22 + y1) / 2; Lm = y1 - 2.22
    rect(ex, (2.22, -2.40, 3.72, -1.0), fc="#eef6f8", ec=GRIS, lw=0.5, hatch="||"); rect(ex, (2.07, -1.0, 2.22, 0), fc="white", ec=TINTA, lw=0.6, hatch="////")
    rect(ex, (2.22, -2.30, y1, 0), fc="#17181b", ec=TINTA, lw=0.8)
    ex.text(ym, -1.55, "AZOTEA", color="white", fontsize=13 if Lm > 1.3 else 10.5, fontweight="black", ha="center"); ex.text(ym, -1.15, "GYM", color=ROJO, fontsize=18 if Lm > 1.3 else 14.5, fontweight="black", ha="center")
    ex.text(ym, -0.98 if Lm > 1.3 else -1.08, "ENTRENA EN LAS ALTURAS", color="#c9cbd0", fontsize=4.2 if Lm > 1.3 else 3.4, ha="center")
    rect(ex, (2.22, -1.05, y1 + 0.04, -1.01), fc=TINTA, ec=TINTA); rect(ex, (2.24, -1.01, y1, -0.08), fc="#c9925a", ec=TINTA, lw=0.6)
    for i in range(int((y1 - 2.24) / 0.07) + 1):
        ex.plot([2.24 + i * 0.07, 2.24 + i * 0.07], [-1.01, -0.08], color="#7b5630", lw=0.4)
    rect(ex, (2.24, -0.08, y1, 0), fc="#17181b", ec=TINTA)
    cota(ex, (y1, 0), (y1, -1.05), 0.2, "1.05"); cota(ex, (2.22, 0), (2.22, -2.30), -0.25, "2.30"); cota(ex, (2.22, 0.0), (y1, 0.0), -0.12, "%.2f" % Lm)
    ex.text(4.0, -2.15, "muro de luz\n+1.00 a +2.40", fontsize=4.6, ha="center", color="#3a3c41")
    # elevación de lockers
    el = eje(fig, 130, 160, (2.0, 4.0), (-2.55, 0.15), 25); el.set_ylim(0.15, -2.55)
    mk.text(130, A3[1] - 155, "LOCKERS Y BANCA (desde el vestíbulo)  1 / 25", fontsize=8, fontweight="bold")
    el.plot([2.0, 4.0], [0, 0], color=TINTA, lw=1.0)
    rect(el, (2.22, -2.30, 3.72, 0), fc="#e9e9e6", ec=GRIS, lw=0.4)
    pal = ["#2a2c31", "#c9925a", "#2a2c31", ROJO]
    for i in range(4):
        for j in range(3):
            rect(el, (2.22 + i * 0.3 + 0.012, -0.08 - (j + 1) * 0.6 + 0.012, 2.22 + (i + 1) * 0.3 - 0.012, -0.08 - j * 0.6 - 0.012), fc=pal[(i + j * 3) % 4], ec=TINTA, lw=0.5)
            el.text(2.22 + i * 0.3 + 0.15, -0.08 - j * 0.6 - 0.12, str(j * 4 + i + 1), color="white", fontsize=4.6, ha="center")
    rect(el, (2.22, -0.08, 3.42, 0), fc="#17181b", ec=TINTA)
    cota(el, (2.22, 0), (3.42, 0), -0.12, "1.20  (4 x 0.30)"); cota(el, (3.42, -0.08), (3.42, -1.88), 0.2, "1.80  (3 x 0.60)")
    # especificaciones
    x = 238
    mk.text(x, 272, "ESPECIFICACIONES", fontsize=8.5, fontweight="bold", va="center")
    esp = [("Mostrador", "%.2f x 0.50 m, alto 1.05 m. Mesa de trabajo interior a 0.75 m. Zócalo con tira LED roja y luz blanca bajo el tablero." % Lm),
           ("Panel de marca", "%.2f x 2.30 m, visible apenas se sale de la escalera. Logo «Azotea Gym» retroiluminado." % Lm),
           ("Lockers", "12 casilleros metálicos de 0.30 x 0.60 x 0.42 m con candado propio del socio, espalda con espalda con el panel."),
           ("Banca", "0.80 x 0.38 m, listones de madera sobre estructura de tubo 40 x 40."),
           ("Muro de luz", "El muro sur del tragaluz E y de la escalera se completa con policarbonato opal hasta +2.40: protege la caída, deja pasar la luz y no tapa el tragaluz."),
           ("Lavadero y tanque", "Se conservan. Celosía de listones de 2.20 m los oculta desde la sala; el lavadero se usa como estación de limpieza del gimnasio."),
           ("Piso", "Vinílico SPC tono madera en recepción y vestíbulo; marca el área «limpia» frente al caucho de la sala.")]
    yy = 262
    for a, b in esp:
        mk.text(x, yy, a, fontsize=7.2, fontweight="bold", color=ROJO, va="top")
        t = _envolver(b, 58); mk.text(x, yy - 5, t, fontsize=6.0, va="top", linespacing=1.3)
        yy -= 9 + 3.6 * (t.count("\n") + 1)
    return fig


def A05():
    fig, mk = nueva("A-05", "Cortes y alturas", "1 / 50",
                    ["Alturas de techo según plano de techo metálico: 2.80 m (eje 7) a 2.40 m (eje 1), bajo cercha.", "Peralte de cerchas 0.40 m; calamina TR4.",
                     "Sobre los tragaluces se prevé calamina translúcida (plano de techo)."])
    # corte longitudinal por y = 5.9 (mirando al lado B)
    ax = eje(fig, 16, 22, (-1.0, D.L + 1.0), (-3.6, 0.7), 50); ax.set_ylim(0.7, -3.6)
    mk.text(16, A3[1] - 16, "CORTE LONGITUDINAL A-A (mirando al lado B)", fontsize=8.5, fontweight="bold")
    ax.add_patch(Rectangle((0, 0), D.L, 0.25, fc="#d9d9d6", ec=TINTA, lw=0.6, hatch="...."))
    ax.plot([-1, D.L + 1], [0, 0], color=TINTA, lw=0.9)
    xs = [0, D.L]; hs = [D.altura_techo(0), D.altura_techo(D.L)]
    import numpy as np
    xx = np.linspace(-0.1, D.L + 0.1, 60); hh = np.array([D.altura_techo(x) for x in xx])
    ax.plot(xx, -hh, color=TINTA, lw=0.8); ax.plot(xx, -(hh + D.PERALTE_CERCHA), color=TINTA, lw=0.8)
    for i in range(len(xx) - 1):
        a, b = (xx[i], -hh[i]), (xx[i + 1], -(hh[i + 1] + 0.4))
        if i % 2:
            a, b = (xx[i], -(hh[i] + 0.4)), (xx[i + 1], -hh[i + 1])
        ax.plot([a[0], b[0]], [a[1], b[1]], color=GRIS, lw=0.35)
    ax.plot(xx, -(hh + D.PERALTE_CERCHA + 0.06), color="#7d8a93", lw=1.6)
    for r in D.TRANSLUCIDO[:1]:
        m = (xx >= r[0]) & (xx <= r[2]); ax.plot(xx[m], -(hh[m] + 0.46), color="#f2c200", lw=2.2)
    ax.text((D.TRANSLUCIDO[0][0] + D.TRANSLUCIDO[0][2]) / 2, -3.42, "calamina translúcida sobre tragaluz E y escalera", fontsize=5, ha="center", color="#9a7b00")
    for k, x in D.X_CERCHA.items():
        h = D.H_TECHO[k]; ax.add_patch(Rectangle((x - 0.15, -h), 0.30, h, fc="#bdbfc4", ec=TINTA, lw=0.5))
        ax.text(x, -h - 0.62, "eje %s\n%.2f m" % (k, h), fontsize=5.6, ha="center", va="center", fontweight="bold")
        cota(ax, (x + 0.2, 0), (x + 0.2, -h), -0.18, "%.2f" % h, 5)
    ax.add_patch(Rectangle((0.3, -1.0), D.L - 0.3, 1.0, fc="#ecebe7", ec=GRIS, lw=0.4))        # parapeto del lado B
    ax.plot([0.3, D.L], [-2.2, -2.2], color=GRIS, lw=0.5); ax.text(D.L - 0.3, -1.6, "policarbonato\n+1.00 a +2.20", fontsize=4.6, ha="right", va="center", color="#3a3c41")
    ax.text(D.L - 0.3, -2.32, "lamas de ventilación", fontsize=4.4, ha="right", va="center", color="#3a3c41")
    for m in D.MAQUINAS:
        r = D.rect_maquina(m)
        if r[3] > 4.4:
            ax.add_patch(FancyBboxPatch((r[0], -m["alto"]), r[2] - r[0], m["alto"], boxstyle="round,pad=0,rounding_size=0.04", fc=COL_ZONA[m["zona"]], alpha=0.35, ec=TINTA, lw=0.6))
            ax.text((r[0] + r[2]) / 2, -m["alto"] / 2, "%s\nh = %.2f" % (m["nombre"].replace(" + ", "\n+ ").replace(" olímpic", "\nolímpic"), m["alto"]), fontsize=4.4, ha="center", va="center")
            if m["alto"] > 2.0:
                h = D.altura_techo(m["c"][0]); ax.text((r[0] + r[2]) / 2, -m["alto"] - 0.09, "libre %.2f" % (h - m["alto"]), fontsize=4.4, ha="center", color=ROJO)
            if m["tipo"] == "cinta" and m["id"] == "M14":
                xc = (r[0] + r[2]) / 2 + 0.55; h = D.altura_techo(xc)
                ax.add_patch(Circle((xc, -2.0), 0.11, fc="none", ec=ROJO, lw=0.6)); ax.plot([xc, xc], [-1.89, -1.0], color=ROJO, lw=0.6); ax.plot([xc - 0.18, xc, xc + 0.18], [-0.25, -1.0, -0.25], color=ROJO, lw=0.6)
                ax.text(xc, -2.24, "corredor 1.85 m\nlibre %.2f" % (h - 2.2), fontsize=4.4, ha="center", color=ROJO)
    ax.add_patch(Rectangle((0.0, -D.H_BANO), 0.15, D.H_BANO, fc="#3a3c41", ec="none"))
    # persona de referencia
    ax.add_patch(Circle((9.5, -1.6), 0.11, fc="none", ec=GRIS, lw=0.6)); ax.plot([9.5, 9.5], [-1.49, -0.8], color=GRIS, lw=0.6); ax.plot([9.3, 9.5, 9.7], [0, -0.8, 0], color=GRIS, lw=0.6); ax.plot([9.25, 9.75], [-1.3, -1.3], color=GRIS, lw=0.6)
    ax.text(9.5, -1.85, "1.70", fontsize=4.2, ha="center", color=GRIS)
    # corte transversal por la recepción (x = 5.6) mirando al lado calle
    bx = eje(fig, 16, 122, (-1.0, D.W + 1.0), (-3.6, 0.7), 50); bx.set_ylim(0.7, -3.6)
    mk.text(16, A3[1] - 116, "CORTE TRANSVERSAL B-B por la recepción", fontsize=8.5, fontweight="bold")
    h = D.altura_techo(5.6)
    bx.add_patch(Rectangle((D.Y_ESC1, 0), D.W - D.Y_ESC1, 0.25, fc="#d9d9d6", ec=TINTA, lw=0.6, hatch="....")); bx.add_patch(Rectangle((0, 0), 0.15, 0.25, fc="#d9d9d6", ec=TINTA, lw=0.6))
    bx.plot([-1, D.W + 1], [0, 0], color=TINTA, lw=0.9)
    bx.plot([-0.1, D.W + 0.1], [-h, -h], color=TINTA, lw=0.8); bx.plot([-0.1, D.W + 0.1], [-h - 0.4, -h - 0.4], color=TINTA, lw=0.8)
    n = 12
    for i in range(n):
        a = -0.1 + i * (D.W + 0.2) / n; b = a + (D.W + 0.2) / n
        bx.plot([a, b], [-h - (0.4 if i % 2 else 0), -h - (0 if i % 2 else 0.4)], color=GRIS, lw=0.35)
    bx.plot([-0.2, D.W + 0.2], [-h - 0.46, -h - 0.46], color="#7d8a93", lw=1.6); bx.plot([-0.2, 1.67], [-h - 0.46, -h - 0.46], color="#f2c200", lw=2.2)
    for y0, y1, hh_, t in [(0, 0.15, 1.0, ""), (D.Y_ESC1, D.Y_HALL0, 1.0, ""), (D.W - 0.15, D.W, 1.0, "")]:
        bx.add_patch(Rectangle((y0, -hh_), y1 - y0, hh_, fc="white", ec=TINTA, lw=0.6, hatch="////"))
    bx.add_patch(Rectangle((D.Y_ESC1 + 0.05, -2.4), 0.05, 1.4, fc="#eef6f8", ec="#39a0c8", lw=0.6)); bx.text(1.1, -1.6, "vacío de\nescalera", fontsize=4.6, ha="center", color=GRIS)
    bx.text(D.Y_ESC1 + 0.07, -2.52, "muro de luz", fontsize=4.4, ha="center", color="#1f7fa8")
    R = D.RECEPCION
    bx.add_patch(Rectangle((R["mostrador"][1], -1.05), R["mostrador"][3] - R["mostrador"][1], 1.05, fc="#c9925a", ec=TINTA, lw=0.6)); bx.text((R["mostrador"][1] + R["mostrador"][3]) / 2, -0.5, "mostrador\nh = 1.05", fontsize=4.6, ha="center")
    Lp = R["panel_marca"][3] - R["panel_marca"][1]; xm = R["panel_marca"][1] + Lp / 2
    bx.add_patch(Rectangle((R["panel_marca"][1], -2.3), Lp, 1.22, fc="#17181b", ec=TINTA, lw=0.6)); bx.text(xm, -1.7, "panel de marca\nh = 2.30", fontsize=4.6, ha="center", color="white")
    m13 = next(m for m in D.MAQUINAS if m["id"] == ("M11" if B else "M13")); r = D.rect_maquina(m13)
    bx.add_patch(FancyBboxPatch((r[1], -m13["alto"]), r[3] - r[1], m13["alto"], boxstyle="round,pad=0,rounding_size=0.04", fc=COL_ZONA[m13["zona"]], alpha=0.35, ec=TINTA, lw=0.6))
    bx.text((r[1] + r[3]) / 2, -1.1 if not B else -0.75, ("hip thrust\nh = 0.50" if B else "dominadas\nh = 2.23"), fontsize=4.6, ha="center")
    cota(bx, (R["mostrador"][3], -0.25), (r[1], -0.25), 0.0, None, 5.2, ROJO); cota(bx, (D.W + 0.3, 0), (D.W + 0.3, -h), -0.2, "%.2f" % h, 5)
    bx.add_patch(Rectangle((D.W - 0.1, -2.2), 0.03, 1.2, fc="#eef6f8", ec=GRIS, lw=0.5))
    # cuadro de alturas
    filas = [(m["nombre"], m["alto"], round(D.altura_techo(m["c"][0]), 2), round(D.altura_techo(m["c"][0]) - m["alto"], 2)) for m in sorted(D.MAQUINAS, key=lambda q: -q["alto"])[:8]]
    tabla(mk, 200, 170, ["Equipo", "Alto (m)", "Techo libre (m)", "Holgura (m)"], filas, [64, 22, 30, 26], alto=5.2, titulo="ALTURA DE LOS EQUIPOS MÁS ALTOS FRENTE AL TECHO")
    if B:
        mk.text(200, 114, _envolver("Las cintas de correr quedan en el lado más alto del techo: 2.73 m libres bajo cercha. Con la plataforma a 0.25 m, un corredor de 1.85 m deja 0.53 m sobre la cabeza. "
                                    "En el lado calle (2.40 m) esa holgura bajaría a 0.20 m: por eso el cardio va en la esquina del lado mercado.", 100), fontsize=6.2, va="top", linespacing=1.35)
        mk.text(200, 92, _envolver("Las dominadas (2.23 m) pasan al muro del fondo, donde hay 2.43 m bajo cercha y unos 2.80 m hasta la calamina entre cerchas. El crossover (2.30 m) no se mueve: "
                                   "confirmar 2.35 m o más bajo la cercha del eje 2.", 100), fontsize=6.2, va="top", linespacing=1.35)
        return fig
    mk.text(200, 114, _envolver("El crossover (2.30 m) queda entre los ejes 3 y 2, donde la cercha está a 2.48 m: holgura de 18 cm. Si en obra la altura real bajo la cercha del eje 2 fuera menor de 2.35 m, "
                               "pedir el crossover con altura reducida (el fabricante personaliza medidas) o correrlo hacia el eje 3.", 100), fontsize=6.2, va="top", linespacing=1.35)
    mk.text(200, 90, _envolver("En las dominadas la cabeza del usuario sube por encima de la barra (≈ 2.45 m): se ubican entre cerchas secundarias, donde hay 2.62 m bajo cercha y ≈ 3.00 m hasta la calamina.", 100), fontsize=6.2, va="top", linespacing=1.35)
    return fig


def _area_poligono(p):
    return abs(sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p)))) / 2


def metrados():
    ar = D.areas()
    R = D.RECEPCION; huella = lambda r: (r[2] - r[0]) * (r[3] - r[1])
    vin = next(p for p in D.PISOS if p["id"] == "vinilico"); a_vin = _area_poligono(vin["poligono"]) - huella(R["mostrador"]) - huella(R["lockers"])
    pl = next(p for p in D.PISOS if p["id"] == "caucho_pl")["rect"]; a_pl = (pl[2] - pl[0]) * (pl[3] - pl[1])
    zf = D.ZONA_FUNCIONAL; a_gr = (zf[2] - zf[0]) * (zf[3] - zf[1]) if zf else 0.0
    a_car = sum(huella(p["rect"]) for p in D.PISOS if p["id"] == "caucho_cardio")
    a_c15 = ar["sala"] - a_vin - a_pl - a_gr - a_car
    cer = {}
    for x0, y0, x1, y1, tipo in D.CERRAMIENTO:
        Lg = math.hypot(x1 - x0, y1 - y0); xm = (x0 + x1) / 2
        if tipo in ("muro_luz", "panel"):
            cer[tipo] = cer.get(tipo, 0) + Lg * 1.4
        else:
            cer[tipo] = cer.get(tipo, 0) + Lg * 1.2
            cer["lamas"] = cer.get("lamas", 0) + Lg * max(0.1, D.altura_techo(xm) - 2.2)
    cel = sum(math.hypot(c[2] - c[0], c[3] - c[1]) * c[4] for c in D.CELOSIAS) + 1.39 * 1.3
    esp = sum(b - a for a, b in D.ESPEJOS) * 1.8
    return {"vinilico": round(a_vin, 1), "caucho_pl": round(a_pl, 1), "grass": round(a_gr, 1), "caucho_cardio": round(a_car, 1), "caucho15": round(a_c15, 1),
            "cerramiento": {k: round(v, 1) for k, v in cer.items()}, "celosia": round(cel, 1), "espejos": round(esp, 1),
            "pintura": round((2 * (D.L + D.W) - 4.0) * 1.0 + 14.0, 0)}


def A06():
    me = metrados()
    fig, mk = nueva("A-06", "Pisos, cerramiento\ny acabados", "1 / 50",
                    ["El caucho se coloca flotante sobre la losa limpia y nivelada; protege la losa y reduce el ruido de impacto hacia el piso inferior.",
                     "El cerramiento se apoya en el parapeto existente de 1.00 m y llega hasta la cercha; la franja superior de lamas mantiene la ventilación cruzada."])
    ax = eje(fig, 12, 14, XL, YL, 50)
    cont = [(0.15, 2.05), (0.15, D.W - 0.15), (D.L - 0.15, D.W - 0.15), (D.L - 0.15, 0.15), (D.X_ESC1 + 0.15, 0.15), (D.X_ESC1 + 0.15, D.Y_HALL0), (D.X_BANO_D, D.Y_HALL0), (D.X_BANO_D, 2.05)]
    planta_base(ax, textos=False)
    ax.add_patch(Polygon(cont, closed=True, fc="#c9cbd0", ec="none", zorder=0.4, hatch=".."))
    for p in D.PISOS:
        if p["id"] in ("caucho_pl", "caucho_cardio"):
            rect(ax, p["rect"], fc="#e8b9b9", ec=ROJO, lw=0.6, zorder=0.5, hatch="..")
        if p["id"] == "vinilico":
            ax.add_patch(Polygon(p["poligono"], closed=True, fc="#f0d9b0", ec="#a8763e", lw=0.6, zorder=0.6, hatch="---"))
        if p["id"] == "grass":
            rect(ax, p["rect"], fc="#bfe3b4", ec="#3f8f3a", lw=0.6, zorder=0.7, hatch="||")
    dibujar_maquinas(ax, etiquetas=False, relleno=False, alpha=1)
    for m in D.MAQUINAS:
        r = D.rect_maquina(m); rect(ax, r, fc="white", ec=GRIS, lw=0.4, alpha=0.6, zorder=6.6)
    R = D.RECEPCION
    for k in ("mostrador", "lockers", "panel_marca", "banca"):
        rect(ax, R[k], fc="white", ec=GRIS, lw=0.4, zorder=6)
    colc = {"policarbonato": "#39a0c8", "ventanal": "#1f4fa3", "panel_espejo": "#3a3c41", "muro_luz": "#f2c200", "panel": ROJO}
    for x0, y0, x1, y1, tipo in D.CERRAMIENTO:
        dx = 0.33 * (1 if x0 == D.L else -1 if x0 == 0 and x1 == 0 else 0); dy = 0.33 * (1 if y0 == D.W else -1 if y0 == 0 and y1 == 0 else 0)
        if tipo == "muro_luz":
            dy = 0.0
        ax.plot([x0 + dx, x1 + dx], [y0 + dy, y1 + dy], color=colc[tipo], lw=3.0, solid_capstyle="butt", zorder=9, clip_on=False)
    for a, b in D.ESPEJOS:
        ax.plot([a, b], [0.19, 0.19], color="#39a0c8", lw=1.6, zorder=9, ls=(0, (1, 1)))
    for x0, y0, x1, y1, h in D.CELOSIAS:
        ax.plot([x0, x1], [y0, y1], color="#a8763e", lw=2.0, zorder=9)
    kw = dict(fontsize=5.2, ha="center", va="center", zorder=12, bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.9))
    ax.text(10.0, 4.75, "CAUCHO 15 mm  %.1f m²" % me["caucho15"], **kw); ax.text(9.9, 1.25, "CAUCHO 25 mm  %.1f m²" % me["caucho_pl"], **dict(kw, color=ROJO))
    ax.text(3.2, 3.2, "VINÍLICO SPC  %.1f m²" % me["vinilico"], **dict(kw, color="#7b5630")); zf = D.ZONA_FUNCIONAL
    if zf:
        ax.text((zf[0] + zf[2]) / 2, (zf[1] + zf[3]) / 2, "GRASS  %.1f m²" % me["grass"], **dict(kw, color="#2f6d2c"))
    if me["caucho_cardio"]:
        ax.text(2.98, 3.72, "CAUCHO 25 mm (cintas)  %.1f m²" % me["caucho_cardio"], **dict(kw, color=ROJO))
    c = me["cerramiento"]
    filas = [("Caucho reciclado 15 mm en losetas de 1 x 1 m", "Sala de máquinas", "%.1f m²" % me["caucho15"]), ("Caucho reciclado 25 mm", "Peso libre (mancuernas y bancos)", "%.1f m²" % me["caucho_pl"]),
             (("Caucho reciclado 25 mm bajo cintas (antivibración)", "Zona de cardio", "%.1f m²" % me["caucho_cardio"]) if B else ("Grass sintético deportivo 12 mm", "Zona funcional y estiramiento", "%.1f m²" % me["grass"])), ("Piso vinílico SPC tono madera", "Recepción y vestíbulo de servicios", "%.1f m²" % me["vinilico"]),
             ("Policarbonato alveolar 8 mm + tubo 50 x 50", "Lado B, lado mercado y fondo (escalera)", "%.1f m²" % c.get("policarbonato", 0)), ("Ventanal transparente (policarbonato compacto o vidrio templado)", "Lado calle y esquina de cardio" if B else "Lado calle", "%.1f m²" % c.get("ventanal", 0)),
             ("Panel de fibrocemento 8 mm (lleva los espejos)", "Fondo, zona de peso libre", "%.1f m²" % c.get("panel_espejo", 0)), ("Lamas metálicas de ventilación", "Franja superior de todo el perímetro", "%.1f m²" % c.get("lamas", 0)),
             ("Muro de luz: policarbonato opal 8 mm", "Tragaluz E y escalera hacia la sala", "%.1f m²" % c.get("muro_luz", 0)), ("Espejo 4 mm con lámina de seguridad sobre tablero", "Peso libre: 4.00 x 1.80 m", "%.1f m²" % me["espejos"]),
             ("Celosía de listones de madera 2\" x 1\"", "Tanque, tragaluz SO y lavadero", "%.1f m²" % me["celosia"]), ("Pintura látex gris oscuro / esmalte negro en metal", "Parapetos, columnas y carpintería", "%.0f m²" % me["pintura"])]
    tabla(mk, 14, 94, ["Acabado", "Dónde", "Metrado"], filas, [112, 80, 22], alto=4.5, tam=5.3, titulo="CUADRO DE ACABADOS")
    x2 = 240
    mk.text(x2, 96.2, "CERRAMIENTO SOBRE PARAPETO", fontsize=6.6, fontweight="bold", va="bottom")
    for i, (k, t) in enumerate([("policarbonato", "Policarbonato alveolar translúcido"), ("ventanal", "Ventanal transparente (vista a la calle)"), ("panel_espejo", "Panel ciego con espejos"), ("muro_luz", "Muro de luz del tragaluz E"), ("panel", "Panel con mural de marca")]):
        mk.add_patch(Rectangle((x2, 89 - i * 6.2), 8, 2.2, fc=colc[k], ec="none")); mk.text(x2 + 10, 90.1 - i * 6.2, t, fontsize=5.8, va="center")
    mk.text(x2, 52, _envolver("Si ya existe un cerramiento sobre el parapeto, esta partida se descuenta del presupuesto. Protege de la lluvia con viento y da seguridad a S/ 70 mil en equipos.", 52), fontsize=5.6, va="top", linespacing=1.3)
    return fig


def IE01():
    fig, mk = nueva("IE-01", "Iluminación,\ntomacorrientes y ventilación", "1 / 50",
                    ["Luminarias LED lineales 40 W, 4000 K, colgadas de las cerchas secundarias a 2.30–2.70 m.", "Tablero de distribución existente: verificar capacidad y puesta a tierra antes de conectar.",
                     "Circuitos independientes para alumbrado, tomacorrientes y ventiladores, con interruptor diferencial de 30 mA."])
    ax = eje(fig, 12, 14, XL, YL, 50)
    planta_base(ax, textos=False, suave=True); dibujar_recepcion(ax, textos=False); dibujar_maquinas(ax, etiquetas=False, relleno=False)
    for z in D.CERCHAS_SEC_Y:
        ax.plot([0, D.L], [z, z], color="#2a6f3c", lw=0.5, ls=(0, (6, 2)), zorder=7)
    for k, x in D.X_CERCHA.items():
        ax.plot([x, x], [D.Y_BLOQUE if k == "7" else 0, D.W], color="#1f4fa3", lw=0.7, zorder=7)
    for r in D.TRANSLUCIDO:
        rect(ax, r, fc="#fff2a8", ec="#c9a400", lw=0.6, alpha=0.5, zorder=0.9, hatch="//")
    for x, y in D.LUMINARIAS:
        rect(ax, (x - 0.06, y - 0.6, x + 0.06, y + 0.6), fc="#ffd400", ec=TINTA, lw=0.5, zorder=11)
    for x, y, d in D.VENTILADORES:
        ax.add_patch(Circle((x, y), 0.24, fc="white", ec="#1f7fa8", lw=0.8, zorder=11)); ax.text(x, y, "V", fontsize=4.6, ha="center", va="center", color="#1f7fa8", fontweight="bold", zorder=12)
    for i, (x, y, t) in enumerate(D.TOMACORRIENTES):
        ax.add_patch(Polygon([(x - 0.13, y + 0.11), (x + 0.13, y + 0.11), (x, y - 0.13)], fc=ROJO, ec="white", lw=0.4, zorder=12))
    for x, y in D.LUCES_EMERGENCIA:
        ax.add_patch(Rectangle((x - 0.14, y - 0.08), 0.28, 0.16, fc="#2a9a4b", ec=TINTA, lw=0.4, zorder=12))
    ax.text(5.9, 0.9, "calamina translúcida\n(luz natural)", fontsize=4.4, ha="center", va="center", color="#8a7000", zorder=12)
    n = len(D.LUMINARIAS)
    filas = [("C-1  Alumbrado sala este", "%d luminarias LED 40 W" % 12, 12 * 40, "2 x 2.5 mm² — ITM 16 A"), ("C-2  Alumbrado sala oeste y recepción", "%d luminarias LED 40 W + tiras LED" % (n - 12), (n - 12) * 40 + 120, "2 x 2.5 mm² — ITM 16 A"),
             ("C-3  Tomacorrientes", "%d puntos dobles con tierra" % len(D.TOMACORRIENTES), 1500, "2 x 4 mm² + T — ITM 20 A + ID 30 mA"), ("C-4  Ventiladores", "%d ventiladores de pared 20\"" % len(D.VENTILADORES), len(D.VENTILADORES) * 120, "2 x 2.5 mm² + T — ITM 16 A"),
             ("C-5  Emergencia y sonido", "3 luces de emergencia + equipo de sonido", 200, "2 x 2.5 mm² — ITM 16 A")]
    if B:
        filas[2] = ("C-3  Tomacorrientes", "%d puntos dobles con tierra" % (len(D.TOMACORRIENTES) - 2), 1500, "2 x 4 mm² + T — ITM 20 A + ID 30 mA")
        filas += [("C-6  Cinta de correr 1 (circuito propio)", "Trotadora 3 HP, tomacorriente dedicado", 2200, "2 x 4 mm² + T — ITM 20 A + ID 30 mA"),
                  ("C-7  Cinta de correr 2 (circuito propio)", "Trotadora 3 HP, tomacorriente dedicado", 2200, "2 x 4 mm² + T — ITM 20 A + ID 30 mA")]
    yf = tabla(mk, 14, 94, ["Circuito", "Cargas", "Potencia (W)", "Conductor y protección"], filas, [62, 68, 24, 60], alto=5.2, titulo="CUADRO DE CARGAS (referencial)")
    tot = sum(f[2] for f in filas)
    mk.text(14, yf - 5, "Potencia instalada ≈ {:,} W  ·  demanda máxima estimada ≈ {:,} W  ·  alimentador monofásico 220 V, {}".format(tot, int(tot * 0.8), "2 x 10 mm² + T (confirmar potencia contratada)" if B else "2 x 6 mm² + T"), fontsize=6.0, fontweight="bold")
    mk.text(14, yf - 13, _envolver("Iluminación: %d luminarias x 4 000 lm sobre %.0f m² ≈ %d lux medios (recomendado para gimnasios: 300 lux). De día, la calamina translúcida sobre los tragaluces y el policarbonato del perímetro permiten apagar la mitad."
                                  % (n, D.areas()["sala"], n * 4000 * 0.55 / D.areas()["sala"]), 150), fontsize=5.8, va="top", linespacing=1.35)
    x2 = 240
    mk.text(x2, 96.2, "LEYENDA", fontsize=6.6, fontweight="bold", va="bottom")
    ley = [("#ffd400", "Luminaria LED lineal 40 W"), ("#1f7fa8", "V  Ventilador de pared"), (ROJO, "Tomacorriente doble con tierra"), ("#2a9a4b", "Luz de emergencia"), ("#1f4fa3", "Cercha principal"), ("#2a6f3c", "Cercha secundaria"), ("#fff2a8", "Calamina translúcida")]
    for i, (c, t) in enumerate(ley):
        mk.add_patch(Rectangle((x2, 89 - i * 6.0), 6, 2.4, fc=c, ec=TINTA, lw=0.3)); mk.text(x2 + 8, 90.2 - i * 6.0, t, fontsize=5.8, va="center")
    return fig


def E01():
    fig, mk = nueva("E-01", "Cargas sobre la losa", "1 / 50",
                    ["Lámina de coordinación: NO reemplaza la evaluación estructural.", "Norma E.020: sobrecarga de diseño para gimnasios 400 kgf/m². Una losa de vivienda suele estar diseñada para 200 kgf/m².",
                     "Antes de comprar: evaluación de la losa y vigas del último techo por ingeniero civil colegiado.", "Prohibido soltar pesas; peso muerto solo sobre plataforma amortiguada."]
                    + (["Cintas de correr: carga dinámica (impacto ≈ 2.5 veces el peso del corredor) y vibración. Van con base antivibratoria; la cinta 1 queda sobre la viga del eje 6."] if B else []))
    ax = eje(fig, 12, 14, XL, YL, 50)
    planta_base(ax, textos=False, suave=True)
    for a, b in D.VIGAS_X:
        rect(ax, (a, 0.15, b, D.W - 0.15), fc="#bcd3ee", ec="#1f4fa3", lw=0.5, alpha=0.7, zorder=2.5)
    for y0, y1, x0, x1 in D.VIGAS_Y:
        rect(ax, (x0, y0, x1, y1), fc="#bcd3ee", ec="#1f4fa3", lw=0.5, alpha=0.7, zorder=2.5)
    for e in D.INFERIOR:
        rect(ax, e["rect"], fc="#f4d9a0" if e["tipo"] == "muro" else "#3a3c41", ec="#a8763e", lw=0.6, alpha=0.85, zorder=2.7, hatch="////" if e["tipo"] == "muro" else None)
    rect(ax, (D.X_ESC1 + 0.15, 0.15, D.L - 0.15, 1.23), fc="none", ec=ROJO, lw=0.8, ls="--", zorder=3)
    ax.text(11.4, 1.04, "Franja entre ejes D y F: posible volado — solo cargas livianas", fontsize=4.8, color=ROJO, ha="center", va="center", zorder=12, bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.9))
    car = {c[0]: c for c in D.cargas()}
    for m in D.MAQUINAS:
        r = D.rect_maquina(m); q = car[m["id"]][5]
        col = "#d81f26" if q >= 160 else "#e8a33d" if q >= 110 else "#3fa37c"
        rect(ax, r, fc=col, ec=TINTA, lw=0.6, alpha=0.55, zorder=6)
        ax.text(m["c"][0], m["c"][1], "%d\n%d kg" % (int(m["id"][1:]), m["peso_kg"]), fontsize=4.6, ha="center", va="center", zorder=8, fontweight="bold")
    filas = [(int(c[0][1:]), c[1], c[2], c[3], c[4], c[5]) for c in D.cargas()]
    yf = tabla(mk, 14, 94, ["N.º", "Equipo", "Peso + carga (kg)", "Con usuario (kg)", "Área de reparto (m²)", "kg/m²"], filas, [9, 58, 30, 28, 32, 16], alto=4.1 if B else 4.5, tam=5.0 if B else 5.3, titulo="CARGA POR EQUIPO (pesos estimados; confirmar con el fabricante)")
    tot = sum(c[2] for c in D.cargas()); ar = D.areas()
    disc = 300 + 180
    prom = (tot + ar["aforo"] * 80 + ar["sala"] * 20) / ar["sala"]
    x2 = 196
    mk.text(x2, 96.2, "BALANCE GLOBAL (estimado)", fontsize=6.6, fontweight="bold", va="bottom")
    datos = [("Equipos con su carga máxima", "{:,} kg".format(tot)), ("Discos y mancuernas incluidos", "≈ %d kg" % disc), ("%d personas x 80 kg" % ar["aforo"], "{:,} kg".format(ar["aforo"] * 80)),
             ("Piso de caucho (≈ 20 kg/m²)", "{:,} kg".format(int(ar["sala"] * 20))), ("Carga media sobre %.0f m² de sala" % ar["sala"], "≈ %d kg/m²" % prom)]
    for i, (a, b) in enumerate(datos):
        mk.text(x2, 91 - i * 5.6, a, fontsize=5.8, va="center"); mk.text(x2 + 78, 91 - i * 5.6, b, fontsize=5.8, va="center", ha="right", fontweight="bold")
    mk.text(x2, 60, _envolver("La carga media estimada (≈ %d kg/m²) es menor que 200 kg/m², pero las máquinas concentran peso y el uso es dinámico: por eso la norma pide 400 kgf/m² para gimnasios. "
                              "La distribución ya coloca los equipos más pesados sobre las vigas de los ejes; el ingeniero debe confirmar la losa (tipo, peralte, luces y estado) y, si hace falta, indicar refuerzo." % prom, 60), fontsize=5.8, va="top", linespacing=1.35)
    x3 = 290
    mk.text(x3, 96.2, "LEYENDA", fontsize=6.6, fontweight="bold", va="bottom")
    for i, (c, t) in enumerate([("#bcd3ee", "Viga (proyección)"), ("#f4d9a0", "Muro nivel inferior"), ("#3a3c41", "Columna 0.20 x 0.50"), ("#3fa37c", "< 110 kg/m²"), ("#e8a33d", "110–160 kg/m²"), ("#d81f26", "> 160 kg/m²")]):
        mk.add_patch(Rectangle((x3, 89 - i * 6.0), 6, 2.6, fc=c, ec=TINTA, lw=0.3)); mk.text(x3 + 8, 90.3 - i * 6.0, t, fontsize=5.6, va="center")
    return fig


def V01():
    fig, mk = nueva("V-01", "Verificación de medidas\nen obra", "1 / 50",
                    ["Medir con wincha ANTES de pedir las máquinas y de fabricar el cerramiento.", "Si una medida resulta menor que el mínimo, ajustar en diseno.py y regenerar los planos."])
    ax = eje(fig, 12, 14, XL, YL, 50)
    planta_base(ax, textos=True); dibujar_maquinas(ax, etiquetas=False, relleno=False, alpha=1); dibujar_recepcion(ax, textos=False)
    M = {m["id"]: D.rect_maquina(m) for m in D.MAQUINAS}
    med = [("C1", (0.15, 6.9), (D.L - 0.15, 6.9), "Largo interior total (lado B)", "%.2f" % (D.L - 0.3), "14.32 (plano base) / ≈ 15.2 (cotas del plano de techo)", "≥ 14.30"),
           ("C2", (D.L + 0.55, 0.15), (D.L + 0.55, D.W - 0.15), "Ancho interior en el lado calle", "%.2f" % (D.W - 0.3), "6.35 (base) / 6.00 entre columnas (techo)", "≥ 6.00"),
           ("C3", (0.6, 3.2), (0.6, D.W - 0.15), "Del tanque al muro del lado B", "%.2f" % (D.W - 0.15 - 3.2), "El plano de techo acota 5.27 m entre columnas del eje 7", "≥ 3.10"),
           ("C4", (2.9, 2.05), (2.9, D.W - 0.15), "Del frente de baños al muro del lado B", "%.2f" % (D.W - 0.15 - 2.05), "—", "≥ 4.00"),
           ("C5", (D.X_ESC1 + 0.15, 0.6), (D.L - 0.15, 0.6), "Largo de la sala este (escalera a muro calle)", "%.2f" % (D.L - 0.15 - D.X_ESC1 - 0.15), "7.17 (base)", "≥ 7.10"),
           ("C6", (0.15, 3.75), (D.X_ESC1 + 0.15, 3.75), "Del muro mercado al muro este de la escalera", "%.2f" % (D.X_ESC1 + 0.15 - 0.15), "7.16 (base) + 0.35 (baño de obra)", "≥ 7.30"),
           ("C7", (D.X_VANO0, 2.6), (D.X_VANO1, 2.6), "Ancho libre de la llegada de escalera", "%.2f" % (D.X_VANO1 - D.X_VANO0), "0.97 (base)", "≥ 0.90"),
           ("C8", (D.X_BANO_D + D.T, 2.42), (D.X_VANO0, 2.42), "Muro del tragaluz E / escalera hacia la sala", "%.2f" % (D.X_VANO0 - D.X_BANO_D - D.T), "2.54 (base)", "≥ 2.45")]
    for cod, p, q, *_ in med:
        ax.annotate("", xy=q, xytext=p, arrowprops=dict(arrowstyle="<|-|>", color=ROJO, lw=1.0, mutation_scale=7), zorder=12, annotation_clip=False)
        ax.text((p[0] + q[0]) / 2, (p[1] + q[1]) / 2, cod, fontsize=5.6, color="white", ha="center", va="center", fontweight="bold", zorder=13, bbox=dict(boxstyle="round,pad=0.22", fc=ROJO, ec="none"), clip_on=False)
    for k, x in D.X_CERCHA.items():
        ax.text(x, D.W - 0.45, "H%s" % k, fontsize=5.2, color="white", ha="center", va="center", fontweight="bold", zorder=13, bbox=dict(boxstyle="round,pad=0.2", fc="#1f4fa3", ec="none"))
    filas = [(c, d, v, r, mn, "") for c, p, q, d, v, r, mn in med]
    filas += [("H%s" % k, "Altura libre bajo la cercha del eje %s" % k, "%.2f" % D.H_TECHO[k], "Plano de techo", "≥ %.2f" % (2.35 if k in "32" else 2.30), "") for k in D.H_TECHO]
    tabla(mk, 14, 94, ["Cód.", "Medida a tomar", "Modelo (m)", "Referencias que no coinciden", "Mínimo (m)", "Medida real"], filas, [11, 72, 20, 92, 22, 26], alto=4.6, tam=5.2, titulo="MEDIDAS A VERIFICAR CON WINCHA")
    mk.text(262, 86, _envolver("Por qué: el baño construido mide 3.70 m interiores (medidas de obra) y el plano base 3.35 m; además el plano de techo acota luces de 4.73 / 4.87 / 3.52 / 1.26 m, "
                               "mayores que las del plano base. La azotea real sería entre 0.35 y 0.85 m más larga que el plano base. El proyecto se dibujó con la medida más ajustada: si la real es mayor, sobra holgura.", 44), fontsize=5.7, va="top", linespacing=1.35)
    return fig


LAMINAS = [("A-01", A01), ("A-02", A02), ("A-03", A03), ("A-04", A04), ("A-05", A05), ("A-06", A06), ("IE-01", IE01), ("E-01", E01), ("V-01", V01)]


def generar(solo=None):
    os.makedirs(os.path.join(SALIDA, "vistas_previas"), exist_ok=True)
    ruta = os.path.join(SALIDA, "Planos_Azotea_Gym%s.pdf" % D.SUFIJO)
    with PdfPages(ruta) as pdf:
        for cod, f in LAMINAS:
            if solo and cod not in solo:
                continue
            fig = f()
            pdf.savefig(fig)
            fig.savefig(os.path.join(SALIDA, "vistas_previas", cod + ".png"), dpi=130)
            plt.close(fig)
            print("lámina", cod)
    return ruta


if __name__ == "__main__":
    import sys
    print(generar(sys.argv[1:] or None))
