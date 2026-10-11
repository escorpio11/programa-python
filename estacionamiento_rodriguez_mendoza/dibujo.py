"""
Utilidades de dibujo técnico sobre matplotlib (hoja A3, unidades en mm).

Una `Hoja` es una lámina A3 apaisada con marco y cajetín; una `Vista` es una
ventana dentro de la hoja que dibuja en coordenadas del terreno (metros) a una
escala dada (1:escala).
"""
from __future__ import annotations

import math

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon as MplPolygon, Rectangle, Circle, FancyArrow, Arc, PathPatch
from matplotlib.path import Path as MplPath
from shapely.geometry import Polygon, MultiPolygon, LineString

plt.rcParams["font.family"] = ["Liberation Sans", "DejaVu Sans"]
plt.rcParams["pdf.fonttype"] = 42

MM = 72 / 25.4           # puntos por mm
ANCHO_HOJA, ALTO_HOJA = 420.0, 297.0
MARGEN = 10.0
ANCHO_FRANJA = 92.0      # franja derecha (notas + cajetín)

LW = dict(fino=0.13 * MM, medio=0.25 * MM, grueso=0.40 * MM, mgrueso=0.60 * MM, borde=0.80 * MM)
GRIS = "#7a7a7a"
GRIS_CLARO = "#bdbdbd"
AZUL = "#1f4e79"
ROJO = "#b03a2e"
VERDE = "#2e7d32"
F_CIRC = "#eef3f8"
F_ACC = "#d6e6f5"
F_MOTO = "#fbecc8"
F_SERV = "#ece4f3"
F_VERDE = "#e5f0df"
F_TECHO = "#dfe7ef"

PROYECTO = "ESTACIONAMIENTO VEHICULAR TECHADO"
UBICACION = ["Jr. Rodríguez de Mendoza esq. calle lateral",
             "Dist. San Nicolás (Mendoza) - Prov. Rodríguez de Mendoza",
             "Departamento de Amazonas - Perú"]
FECHA = "OCTUBRE 2026"


def pt(mm_text):
    """Altura de texto en mm -> tamaño de fuente en puntos (aprox. altura de mayúscula)."""
    return mm_text * MM / 0.72


class Hoja:
    def __init__(self, codigo, titulo, especialidad, escala_txt, lamina_n, total_laminas, subtitulo=""):
        self.fig = plt.figure(figsize=(ANCHO_HOJA / 25.4, ALTO_HOJA / 25.4))
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.ax.set_xlim(0, ANCHO_HOJA)
        self.ax.set_ylim(0, ALTO_HOJA)
        self.ax.set_aspect("equal")
        self.ax.axis("off")
        self.codigo = codigo
        self._marco()
        self._cajetin(codigo, titulo, especialidad, escala_txt, lamina_n, total_laminas, subtitulo)

    # --- marco y cajetín -------------------------------------------------
    def _marco(self):
        ax = self.ax
        ax.add_patch(Rectangle((MARGEN, MARGEN), ANCHO_HOJA - 2 * MARGEN, ALTO_HOJA - 2 * MARGEN,
                               fill=False, lw=LW["borde"], ec="k"))
        x = ANCHO_HOJA - MARGEN - ANCHO_FRANJA
        ax.plot([x, x], [MARGEN, ALTO_HOJA - MARGEN], color="k", lw=LW["grueso"])
        self.x_franja = x
        # coordenadas de referencia en el marco
        for i, xx in enumerate(np.linspace(MARGEN, x, 5)[:-1]):
            ax.text(xx + (x - MARGEN) / 8, ALTO_HOJA - MARGEN + 2.5, "ABCD"[i], ha="center", va="center",
                    fontsize=pt(1.8), color=GRIS)
        for i, yy in enumerate(np.linspace(MARGEN, ALTO_HOJA - MARGEN, 4)[:-1]):
            ax.text(MARGEN - 3.5, yy + (ALTO_HOJA - 2 * MARGEN) / 6, str(3 - i), ha="center", va="center",
                    fontsize=pt(1.8), color=GRIS)

    def _cajetin(self, codigo, titulo, especialidad, escala_txt, n, total, subtitulo):
        ax = self.ax
        x0 = self.x_franja
        x1 = ANCHO_HOJA - MARGEN
        y0 = MARGEN
        filas = [  # (alto, contenido)
            (16, "lamina"),
            (8, "escala"),
            (13, "plano"),
            (10, "profesional"),
            (10, "propietario"),
            (17, "ubicacion"),
            (12, "proyecto"),
        ]
        y = y0
        cortes = []
        for h, _ in filas:
            cortes.append((y, y + h))
            y += h
        self.y_cajetin_top = y
        for (ya, yb), (h, clave) in zip(cortes, filas):
            ax.plot([x0, x1], [yb, yb], color="k", lw=LW["medio"])
        w = x1 - x0
        cx = x0 + w / 2

        def etiqueta(xx, yy, t):
            ax.text(xx, yy, t, fontsize=pt(1.5), color=GRIS, va="top", ha="left")

        # lámina
        ya, yb = cortes[0]
        ax.plot([x0 + w * 0.62, x0 + w * 0.62], [ya, yb], color="k", lw=LW["medio"])
        etiqueta(x0 + 1.5, yb - 1.2, "ESPECIALIDAD")
        ax.text(x0 + 1.5, ya + 6.5, especialidad, fontsize=pt(2.6), weight="bold", va="center")
        etiqueta(x0 + w * 0.62 + 1.5, yb - 1.2, "LÁMINA")
        ax.text(x0 + w * 0.81, ya + 6.8, codigo, fontsize=pt(5.0), weight="bold", ha="center", va="center")
        ax.text(x0 + w * 0.81, ya + 1.6, f"{n} de {total}", fontsize=pt(1.6), ha="center", va="bottom")
        # escala / fecha
        ya, yb = cortes[1]
        ax.plot([cx, cx], [ya, yb], color="k", lw=LW["medio"])
        etiqueta(x0 + 1.5, yb - 0.8, "ESCALA")
        ax.text(x0 + w / 4, ya + 2.4, escala_txt, fontsize=pt(2.0), ha="center", va="center", weight="bold")
        etiqueta(cx + 1.5, yb - 0.8, "FECHA")
        ax.text(cx + w / 4, ya + 2.4, FECHA, fontsize=pt(2.0), ha="center", va="center", weight="bold")
        # plano
        ya, yb = cortes[2]
        etiqueta(x0 + 1.5, yb - 1.0, "PLANO")
        ax.text(cx, ya + 6.6 if subtitulo else ya + 5.4, titulo, fontsize=pt(2.5), ha="center", va="center",
                weight="bold", wrap=True)
        if subtitulo:
            ax.text(cx, ya + 2.4, subtitulo, fontsize=pt(1.8), ha="center", va="center")
        # profesional responsable
        ya, yb = cortes[3]
        etiqueta(x0 + 1.5, yb - 1.0, "PROFESIONAL RESPONSABLE (FIRMA Y SELLO)")
        ax.text(x0 + 1.5, ya + 2.6, "Arq. / Ing. CIP N.° ____________", fontsize=pt(1.7), va="center")
        # propietario
        ya, yb = cortes[4]
        etiqueta(x0 + 1.5, yb - 1.0, "PROPIETARIO")
        ax.text(x0 + 1.5, ya + 3.0, "______________________________________", fontsize=pt(1.7), va="center")
        # ubicación
        ya, yb = cortes[5]
        etiqueta(x0 + 1.5, yb - 1.0, "UBICACIÓN")
        for i, t in enumerate(UBICACION):
            ax.text(x0 + 1.5, yb - 5.6 - i * 3.6, t, fontsize=pt(1.7), va="center")
        # proyecto
        ya, yb = cortes[6]
        etiqueta(x0 + 1.5, yb - 1.0, "PROYECTO")
        ax.text(cx, ya + 6.6, PROYECTO, fontsize=pt(2.3), ha="center", va="center", weight="bold")
        ax.text(cx, ya + 2.6, "ANTEPROYECTO - ESTRUCTURA METÁLICA LIGERA", fontsize=pt(1.6), ha="center",
                va="center")

    # --- utilidades ------------------------------------------------------
    def vista(self, x0, y0, escala, origen_m=(0.0, 0.0)):
        return Vista(self, x0, y0, escala, origen_m)

    def texto(self, x, y, t, h=2.0, **kw):
        kw.setdefault("va", "center")
        self.ax.text(x, y, t, fontsize=pt(h), **kw)

    def titulo_vista(self, x, y, titulo, escala_txt, ancho=None):
        ax = self.ax
        ax.text(x, y, titulo, fontsize=pt(3.0), weight="bold", va="bottom", ha="left")
        w = ancho or (len(titulo) * 2.45 + 4)
        ax.plot([x, x + w], [y - 1.2, y - 1.2], color="k", lw=LW["mgrueso"])
        ax.plot([x, x + w], [y - 2.2, y - 2.2], color="k", lw=LW["fino"])
        ax.text(x, y - 3.4, escala_txt, fontsize=pt(1.8), va="top", ha="left")

    def notas(self, y_top, titulo, lineas, h=1.65, ancho_chars=58):
        """Bloque de notas en la franja derecha. Devuelve la y inferior."""
        import textwrap
        x = self.x_franja + 2.5
        ax = self.ax
        ax.text(x, y_top, titulo, fontsize=pt(2.1), weight="bold", va="top")
        y = y_top - 4.6
        for l in lineas:
            partes = textwrap.wrap(l, ancho_chars, subsequent_indent="   ")
            for p in partes:
                ax.text(x, y, p, fontsize=pt(h), va="top")
                y -= h * 1.75
            y -= 0.5
        return y - 2

    def tabla(self, x, y_top, columnas, filas, anchos, h_fila=4.0, h_txt=1.6, titulo=None, alinear=None,
              negrita_ultima=False):
        ax = self.ax
        if titulo:
            ax.text(x, y_top + 1.0, titulo, fontsize=pt(2.0), weight="bold", va="bottom")
        w_tot = sum(anchos)
        y = y_top
        alinear = alinear or ["l"] * len(columnas)

        def fila(vals, yy, bold=False, fondo=None):
            if fondo:
                ax.add_patch(Rectangle((x, yy - h_fila), w_tot, h_fila, fc=fondo, ec="none"))
            xx = x
            for v, w, al in zip(vals, anchos, alinear):
                if al == "r":
                    ax.text(xx + w - 1.0, yy - h_fila / 2, str(v), fontsize=pt(h_txt), va="center", ha="right",
                            weight="bold" if bold else "normal")
                elif al == "c":
                    ax.text(xx + w / 2, yy - h_fila / 2, str(v), fontsize=pt(h_txt), va="center", ha="center",
                            weight="bold" if bold else "normal")
                else:
                    ax.text(xx + 1.0, yy - h_fila / 2, str(v), fontsize=pt(h_txt), va="center", ha="left",
                            weight="bold" if bold else "normal")
                xx += w

        fila(columnas, y, bold=True, fondo="#e6e6e6")
        y -= h_fila
        for i, f in enumerate(filas):
            fila(f, y, bold=negrita_ultima and i == len(filas) - 1)
            y -= h_fila
        # rejilla
        alto = h_fila * (len(filas) + 1)
        ax.add_patch(Rectangle((x, y_top - alto), w_tot, alto, fill=False, lw=LW["medio"]))
        for k in range(1, len(filas) + 1):
            ax.plot([x, x + w_tot], [y_top - k * h_fila] * 2, color="k", lw=LW["fino"])
        xx = x
        for w in anchos[:-1]:
            xx += w
            ax.plot([xx, xx], [y_top, y_top - alto], color="k", lw=LW["fino"])
        return y_top - alto

    def guardar(self, pdf=None, png=None, dpi=110):
        if pdf is not None:
            pdf.savefig(self.fig)
        if png:
            self.fig.savefig(png, dpi=dpi)
        plt.close(self.fig)


class Vista:
    def __init__(self, hoja: Hoja, x0, y0, escala, origen_m=(0.0, 0.0)):
        self.h = hoja
        self.ax = hoja.ax
        self.x0, self.y0 = x0, y0
        self.k = 1000.0 / escala
        self.o = np.asarray(origen_m, dtype=float)

    # transformación
    def T(self, p):
        p = np.asarray(p, dtype=float)
        return np.array([self.x0, self.y0]) + (p - self.o) * self.k

    def TT(self, pts):
        return np.array([self.T(p) for p in pts])

    # primitivas
    def linea(self, pts, lw="medio", color="k", ls="-", z=3, **kw):
        q = self.TT(pts)
        self.ax.plot(q[:, 0], q[:, 1], color=color, lw=LW.get(lw, lw) if isinstance(lw, str) else lw,
                     ls=ls, zorder=z, solid_capstyle="butt", **kw)

    def poly(self, geom, fc="none", ec="k", lw="medio", ls="-", z=2, hatch=None, alpha=1.0, hatch_color=None):
        if geom is None or geom.is_empty:
            return
        geoms = geom.geoms if hasattr(geom, "geoms") else [geom]
        for gg in geoms:
            if gg.geom_type != "Polygon" or gg.is_empty:
                continue
            if hatch:
                matplotlib.rcParams["hatch.linewidth"] = LW["fino"]
                matplotlib.rcParams["hatch.color"] = hatch_color or GRIS
            lw_ = LW.get(lw, lw) if isinstance(lw, str) else lw
            if len(gg.interiors) == 0:
                q = self.TT(np.asarray(gg.exterior.coords))
                patch = MplPolygon(q, closed=True, fc=fc, ec=ec, lw=lw_, ls=ls, zorder=z, hatch=hatch,
                                   alpha=alpha)
            else:
                verts, codes = [], []
                for ring in [gg.exterior, *gg.interiors]:
                    q = self.TT(np.asarray(ring.coords))
                    verts += list(q)
                    codes += [MplPath.MOVETO] + [MplPath.LINETO] * (len(q) - 2) + [MplPath.CLOSEPOLY]
                patch = PathPatch(MplPath(verts, codes), fc=fc, ec=ec, lw=lw_, ls=ls, zorder=z, hatch=hatch,
                                  alpha=alpha)
            self.ax.add_patch(patch)

    def rect_pts(self, pts, **kw):
        self.poly(Polygon(pts), **kw)

    def texto(self, p, t, h=2.0, ang=0.0, color="k", z=6, **kw):
        q = self.T(p)
        kw.setdefault("ha", "center")
        kw.setdefault("va", "center")
        self.ax.text(q[0], q[1], t, fontsize=pt(h), rotation=ang, rotation_mode="anchor", color=color,
                     zorder=z, **kw)

    def texto_a_lo_largo(self, p0, p1, t, h=2.0, offset_mm=0.0, color="k", **kw):
        a, b = self.T(p0), self.T(p1)
        d = b - a
        ang = math.degrees(math.atan2(d[1], d[0]))
        if ang > 90:
            ang -= 180
        elif ang <= -90:
            ang += 180
        m = (a + b) / 2
        n = np.array([-math.sin(math.radians(ang)), math.cos(math.radians(ang))])
        m = m + n * offset_mm
        kw.setdefault("ha", "center")
        kw.setdefault("va", "center")
        self.ax.text(m[0], m[1], t, fontsize=pt(h), rotation=ang, rotation_mode="anchor", color=color, zorder=6,
                     **kw)

    def cota(self, p1, p2, offset_mm=6.0, texto=None, h=1.8, lado=1, color="k", ext=True, decimales=2):
        """Cota alineada entre p1 y p2 (m). offset en mm de papel, lado +1/-1 respecto a p1->p2."""
        a, b = self.T(p1), self.T(p2)
        d = b - a
        L = np.linalg.norm(d)
        if L < 1e-6:
            return
        u = d / L
        n = np.array([-u[1], u[0]]) * lado
        a2, b2 = a + n * offset_mm, b + n * offset_mm
        if ext:
            for p, q in ((a, a2), (b, b2)):
                self.ax.plot([p[0] + n[0] * 1.0, q[0] + n[0] * 1.2], [p[1] + n[1] * 1.0, q[1] + n[1] * 1.2],
                             color=color, lw=LW["fino"], zorder=5)
        self.ax.plot([a2[0] - u[0] * 1.2, b2[0] + u[0] * 1.2], [a2[1] - u[1] * 1.2, b2[1] + u[1] * 1.2],
                     color=color, lw=LW["fino"], zorder=5)
        tick = (u + n * lado) / np.linalg.norm(u + n * lado) * 0.9 if lado else u
        t45 = np.array([u[0] * math.cos(math.radians(45)) - u[1] * math.sin(math.radians(45)),
                        u[0] * math.sin(math.radians(45)) + u[1] * math.cos(math.radians(45))]) * 0.9
        for p in (a2, b2):
            self.ax.plot([p[0] - t45[0], p[0] + t45[0]], [p[1] - t45[1], p[1] + t45[1]], color=color,
                         lw=LW["medio"], zorder=5)
        if texto is None:
            dist_m = L / self.k
            texto = f"{dist_m:.{decimales}f}"
        ang = math.degrees(math.atan2(u[1], u[0]))
        if ang > 90.01:
            ang -= 180
        elif ang <= -89.99:
            ang += 180
        m = (a2 + b2) / 2
        nn = np.array([-math.sin(math.radians(ang)), math.cos(math.radians(ang))])
        m = m + nn * 1.1
        self.ax.text(m[0], m[1], texto, fontsize=pt(h), rotation=ang, rotation_mode="anchor", ha="center",
                     va="bottom", color=color, zorder=6)

    def flecha(self, p_desde, p_hasta, ancho_mm=3.0, color="k", fc="white", lw="medio", z=5):
        a, b = self.T(p_desde), self.T(p_hasta)
        d = b - a
        L = np.linalg.norm(d)
        u = d / L
        n = np.array([-u[1], u[0]])
        hw = ancho_mm / 2
        cab = min(ancho_mm * 1.6, L * 0.5)
        pts = [a + n * hw * 0.5, b - u * cab + n * hw * 0.5, b - u * cab + n * hw, b, b - u * cab - n * hw,
               b - u * cab - n * hw * 0.5, a - n * hw * 0.5]
        self.ax.add_patch(MplPolygon(pts, closed=True, fc=fc, ec=color, lw=LW[lw], zorder=z))

    def flecha_simple(self, p_desde, p_hasta, color="k", lw="medio", cab=1.6, z=6):
        a, b = self.T(p_desde), self.T(p_hasta)
        self.ax.annotate("", xy=b, xytext=a, arrowprops=dict(arrowstyle=f"-|>,head_length={cab * 0.25},head_width={cab * 0.12}",
                                                          color=color, lw=LW[lw]), zorder=z)

    def circulo(self, p, r_mm, fc="white", ec="k", lw="medio", z=6):
        q = self.T(p)
        self.ax.add_patch(Circle(q, r_mm, fc=fc, ec=ec, lw=LW[lw], zorder=z))

    def marca_eje(self, p, etiqueta, r_mm=2.4, h=1.7):
        self.circulo(p, r_mm)
        q = self.T(p)
        self.ax.text(q[0], q[1], etiqueta, fontsize=pt(h), ha="center", va="center", zorder=7, weight="bold")

    def norte(self, p_mm, vector, largo=14.0):
        """Flecha de norte en coordenadas de hoja (mm)."""
        ax = self.ax
        v = np.asarray(vector) / np.linalg.norm(vector)
        n = np.array([-v[1], v[0]])
        base = np.asarray(p_mm)
        tip = base + v * largo / 2
        tail = base - v * largo / 2
        ax.add_patch(Circle(base, largo * 0.42, fill=False, lw=LW["medio"], zorder=6))
        izq = [tip, tail + n * largo * 0.18, base - v * largo * 0.15]
        der = [tip, tail - n * largo * 0.18, base - v * largo * 0.15]
        ax.add_patch(MplPolygon(izq, closed=True, fc="k", ec="k", lw=LW["fino"], zorder=7))
        ax.add_patch(MplPolygon(der, closed=True, fc="white", ec="k", lw=LW["fino"], zorder=7))
        lab = tip + v * 3.2
        ax.text(lab[0], lab[1], "N", fontsize=pt(3.0), ha="center", va="center", weight="bold", zorder=7)

    def escala_grafica(self, p_mm, metros=10, paso=2, alto=1.6):
        ax = self.ax
        x, y = p_mm
        L = metros * self.k
        for i in range(int(metros / paso)):
            ax.add_patch(Rectangle((x + i * paso * self.k, y), paso * self.k, alto,
                                   fc="k" if i % 2 == 0 else "white", ec="k", lw=LW["fino"], zorder=6))
        for i in range(int(metros / paso) + 1):
            ax.text(x + i * paso * self.k, y - 1.2, f"{i * paso}", fontsize=pt(1.5), ha="center", va="top")
        ax.text(x + L + 2, y + alto / 2, "m", fontsize=pt(1.6), va="center")


def corte_marca(v: Vista, p0, p1, etiqueta, lado=1, h=2.6):
    """Línea de corte con flechas de dirección de vista."""
    v.linea([p0, p1], lw="fino", color="k", ls=(0, (8, 2, 1, 2)), z=7)
    a, b = np.asarray(p0, float), np.asarray(p1, float)
    u = (b - a) / np.linalg.norm(b - a)
    n = np.array([-u[1], u[0]]) * lado
    for p in (a, b):
        v.linea([p - u * 0.0, p + u * 0.0], lw="mgrueso")
        q = v.T(p)
        tip = v.T(p + n * 1.6)
        v.ax.annotate("", xy=tip, xytext=q, arrowprops=dict(arrowstyle="-|>,head_length=0.5,head_width=0.25",
                                                            lw=LW["grueso"], color="k"), zorder=8)
        lab = v.T(p - u * 0.9)
        v.ax.text(lab[0], lab[1], etiqueta, fontsize=pt(h), ha="center", va="center", weight="bold", zorder=8)
