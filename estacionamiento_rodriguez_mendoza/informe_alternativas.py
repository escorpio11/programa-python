"""
Informe PDF (A4): «¿Qué hacer con el terreno?» - alternativas de uso para maximizar la
ganancia presente y futura, a partir del modelo de `alternativas.py`.
"""
from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon as MPoly
from matplotlib.patches import Rectangle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import Image, KeepTogether, PageBreak, Spacer, SimpleDocTemplate, Table, TableStyle
from shapely.ops import unary_union

import alternativas as al
import geometria as g
from informe import AZUL, FONDO, GRIS, REJILLA, S1, S2, S3, TINTA, TINTA2, P, S, _estilo_ejes, bullets, st, tabla

S4 = "#eda100"                       # 4.º color categórico (paleta validada)
ESC = 1                              # escenario base
F_LOCAL, F_COCHERA, F_TECHO, F_CANCHA, F_FUTURO = "#f7cfb9", "#e9e8e4", "#cfe0f5", "#bfe6d4", "#fbe7c2"
LINEA = "#6f6e69"


def pct(x, d=1):
    return "—" if x is None else f"{x * 100:.{d}f} %"


def miles(x):
    return f"S/ {x / 1000:,.0f} mil"


# --------------------------------------------------------------------------
# Planos esquemáticos
# --------------------------------------------------------------------------
PROF = 8.0
D_PAS = g.D_PASILLO


def _franjas():
    L = g.LOTE
    esq = unary_union([g.BA.rect(23.5, 40, 0, PROF), g.DA.rect(D_PAS[1], 30, 0, PROF)]).intersection(L)
    locales = [g.BA.rect(s0, s1, 0, PROF).intersection(L).difference(esq) for s0, s1 in ((17.5, 23.5), (11.5, 17.5), (5.5, 11.5))]
    nucleo = g.BA.rect(-5, 5.5, 0, PROF).intersection(L).difference(esq)
    comercial = unary_union([esq, nucleo] + locales)
    return esq, locales, nucleo, comercial


def _poly(ax, poly, fc, ec=LINEA, lw=0.8, ls="-", alpha=1.0, z=2, hatch=None):
    polys = getattr(poly, "geoms", [poly])
    for p in polys:
        if p.is_empty:
            continue
        ax.add_patch(MPoly(np.array(p.exterior.coords), closed=True, fc=fc, ec=ec, lw=lw, ls=ls, alpha=alpha, zorder=z,
                           hatch=hatch))


def _lote(ax, titulo):
    _poly(ax, g.LOTE, "white", ec=TINTA, lw=1.6, z=1)
    # calles
    for borde, nombre, ext in ((g.BA, "Jr. Rodríguez de Mendoza", 4.3), (g.DA, "Calle lateral", 4.0)):
        m = (borde.p0 + borde.p1) / 2 - borde.n * ext
        ang = np.degrees(np.arctan2(borde.t[1], borde.t[0]))
        if ang > 90:
            ang -= 180
        if ang < -90:
            ang += 180
        ax.text(m[0], m[1], nombre, rotation=ang, ha="center", va="center", fontsize=7.2, color=TINTA2, style="italic")
    ax.set_title(titulo, fontsize=8.6, color=TINTA, loc="left", weight="bold")
    ax.set_aspect("equal")
    ax.set_xlim(-5.5, 44.5)
    ax.set_ylim(-4.5, 33.5)
    ax.axis("off")


def _texto(ax, xy, t, fs=6.6, color=TINTA, **kw):
    ax.text(xy[0], xy[1], t, ha="center", va="center", fontsize=fs, color=color, zorder=6, **kw)


def plano_actual(ax):
    _lote(ax, "A · Estacionamiento techado (anteproyecto)")
    for c in g.COBERTURAS:
        _poly(ax, c.poly, F_TECHO, ec="#7fa6d6", lw=0.6, z=2)
    for p in g.PLAZAS:
        _poly(ax, p.poly, "none", ec=LINEA, lw=0.45, z=3)
    for seg, txt in ((g.PORTON_INGRESO, "ingreso"), (g.PORTON_SALIDA, "salida")):
        xs, ys = seg.xy
        ax.plot(xs, ys, color=S2, lw=3, zorder=5, solid_capstyle="butt")
    _texto(ax, (20, -2.6), "28 plazas techadas · 13 columnas · 2 portones", fs=6.6, color=TINTA2)


def plano_locales(ax, titulo="C · Locales en la esquina y el jirón + cochera de abonados"):
    _lote(ax, titulo)
    esq, locales, nucleo, comercial = _franjas()
    _poly(ax, esq, F_LOCAL, z=3)
    for lc in locales:
        _poly(ax, lc, F_LOCAL, z=3)
    _poly(ax, nucleo, "#f1e6dc", z=3, hatch="///")
    libres = [p for p in g.PLAZAS if not p.poly.intersects(comercial.buffer(0.3))]
    _poly(ax, unary_union([g.CIRCULACION]).difference(comercial), F_COCHERA, ec="none", z=2)
    for p in libres:
        _poly(ax, p.poly, "white", ec=LINEA, lw=0.45, z=3)
    # portón de 6 m en la calle lateral, alineado con el pasillo
    a, b = g.DA.punto(D_PAS[0], 0), g.DA.punto(D_PAS[1], 0)
    ax.plot([a[0], b[0]], [a[1], b[1]], color=S2, lw=3, zorder=5, solid_capstyle="butt")
    ce = esq.centroid
    _texto(ax, (ce.x, ce.y), "Local ancla\n100 m²", fs=6.6)
    for lc, area in zip(locales, ("39 m²", "48 m²", "48 m²")):
        cc = lc.centroid
        _texto(ax, (cc.x, cc.y), area, fs=6.3)
    cn = nucleo.centroid
    _texto(ax, ((a[0] + b[0]) / 2 + g.DA.n[0] * 1.6, (a[1] + b[1]) / 2 + g.DA.n[1] * 1.6), "portón 6 m", fs=5.6, color=S2)
    _texto(ax, (25.0, 8.6), "cochera", fs=6.2, color=TINTA2)
    _texto(ax, (20, -2.6), f"261 m² comerciales · núcleo de escalera en B · {len(libres)} plazas de abonados", fs=6.6,
           color=TINTA2)


def plano_cancha(ax):
    _lote(ax, "F · Cancha sintética techada (fútbol 5)")
    cancha = Rectangle((9.9, 1.0), 25, 15, fc=F_CANCHA, ec="#3d8f6b", lw=1.0, zorder=3)
    ax.add_patch(cancha)
    techo = Rectangle((8.6, 0.4), 27.6, 16.8, fc="none", ec="#7fa6d6", lw=0.8, ls="--", zorder=4)
    ax.add_patch(techo)
    ax.plot([22.4, 22.4], [1.0, 16.0], color="white", lw=1.2, zorder=4)
    ax.add_patch(plt.Circle((22.4, 8.5), 2.2, fc="none", ec="white", lw=1.2, zorder=4))
    _texto(ax, (22.4, 12.6), "25 × 15 m\n(la mayor que cabe)", fs=6.6)
    vest = g.DA.rect(2, 8, 0.4, 6.5).intersection(g.LOTE)
    _poly(ax, vest, "#f1e6dc", z=3)
    cv = vest.centroid
    _texto(ax, (cv.x, cv.y), "vestuarios", fs=5.8, color=TINTA2)
    _texto(ax, (20, -2.6), "el frente al jirón queda como cerco: se pierde el valor comercial", fs=6.6, color=TINTA2)


def elevacion(ax, u_cons=760, u_dep=1150):
    ax.set_title("C → E / D · Crecer en altura solo cuando la renta lo pague", fontsize=9, color=TINTA, loc="left",
                 weight="bold")
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_xlim(-0.5, 30.5)
    ax.set_ylim(-3.0, 9.6)
    ax.plot([-1, 31], [0, 0], color=TINTA, lw=1.2)
    h1, h = 3.4, 2.8
    anchos = [(0, 5.5, "núcleo"), (5.5, 11.5, "local"), (11.5, 17.5, "local"), (17.5, 23.5, "local"), (23.5, 30, "esquina")]
    for x0, x1, t in anchos:
        ax.add_patch(Rectangle((x0, 0), x1 - x0, h1, fc=F_LOCAL if t != "núcleo" else "#f1e6dc", ec=LINEA, lw=0.8,
                               hatch="///" if t == "núcleo" else None))
        if t != "núcleo":
            ax.add_patch(Rectangle((x0 + 0.6, 0), x1 - x0 - 1.2, 2.4, fc="#d9d7d0", ec=LINEA, lw=0.5))
        _texto(ax, ((x0 + x1) / 2, 2.9), t, fs=6.6)
    ax.add_patch(Rectangle((0, h1), 30, h, fc=F_FUTURO, ec="#c98500", lw=0.8, ls="--"))
    _texto(ax, (15, h1 + h / 2), f"2.º piso · 7 consultorios (E): solo si se alquilan a ≥ S/ {u_cons:,.0f} al mes", fs=7)
    ax.add_patch(Rectangle((0, h1 + h), 30, h, fc=F_FUTURO, ec="#c98500", lw=0.8, ls="--", alpha=0.75))
    _texto(ax, (15, h1 + 1.5 * h), f"3.er piso · minidepartamentos (D): solo si se alquilan a ≥ S/ {u_dep:,.0f} al mes", fs=7)
    _texto(ax, (15, -1.1), "Fachada al Jr. Rodríguez de Mendoza (30 m). Hoy solo el 1.er piso; zapatas y columnas listas "
                           "para 2 pisos más. Línea discontinua = etapa futura condicionada a la demanda.", fs=6.4,
           color=TINTA2)


def figura_planos(rutas, u_cons, u_dep):
    """Un PNG por esquema (recortado al contenido) para componerlos en una tabla del PDF."""
    for clave, fn in (("pA", plano_actual), ("pC", plano_locales), ("pF", plano_cancha)):
        fig, ax = plt.subplots(figsize=(3.7, 3.0), dpi=220)
        fn(ax)
        fig.savefig(rutas[clave], bbox_inches="tight", pad_inches=0.04)
        plt.close(fig)
    fig, ax = plt.subplots(figsize=(7.4, 2.4), dpi=220)
    elevacion(ax, u_cons, u_dep)
    fig.savefig(rutas["pE"], bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)


# --------------------------------------------------------------------------
# Gráficos
# --------------------------------------------------------------------------
def grafico_tir_terreno(ruta, tabla_m):
    filas = sorted(tabla_m, key=lambda m: m["tir_terreno"])
    fig, ax = plt.subplots(figsize=(7.4, 3.6), dpi=200)
    ys = np.arange(len(filas))
    vals = [m["tir_terreno"] * 100 for m in filas]
    cols = [S1 if m["clave"] != "C" else "#174f96" for m in filas]
    ax.barh(ys, vals, height=0.62, color=cols, edgecolor="white", linewidth=2)
    ax.set_yticks(ys, [f"{m['clave']} · {m['corto']}" for m in filas], fontsize=8, color=TINTA)
    for y, v in zip(ys, vals):
        ax.text(max(v, 0) + 0.12, y, f"{v:.1f} %", va="center", fontsize=7.6, color=TINTA2)
    dep = al.DEPOSITO * (1 - al.IMP_ALQUILER) * 100
    ax.axvline(dep, color=S2, lw=1.4, ls="--")
    ax.text(dep + 0.1, -0.95, f"vender y depositar: {dep:.1f} %", color=TINTA2, fontsize=7.4, va="center")
    ax.axvline(al.PLUSVALIA * 100, color=LINEA, lw=1.0, ls=":")
    ax.text(al.PLUSVALIA * 100 - 0.1, -0.95, f"terreno sin uso: {al.PLUSVALIA * 100:.1f} %", color=TINTA2, fontsize=7.4,
            va="center", ha="right")
    ax.set_ylim(-1.4, len(filas) - 0.4)
    ax.set_xlim(min(-1, min(vals) - 0.5), max(vals) + 1.6)
    ax.set_xlabel("rentabilidad anual para el propietario, contando el valor del terreno (%)", fontsize=8, color=TINTA2)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.spines["bottom"].set_color("#9a9994")
    ax.tick_params(axis="x", colors=TINTA2, labelsize=8)
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", color=REJILLA, lw=0.8)
    ax.set_axisbelow(True)
    ax.set_title("¿Cuánto rinde cada alternativa contando el terreno? (escenario base, 20 años)", fontsize=9.5,
                 color=TINTA, loc="left", weight="bold")
    fig.tight_layout()
    fig.savefig(ruta)
    plt.close(fig)


def grafico_inversion_utilidad(ruta, tabla_m):
    fig, ax = plt.subplots(figsize=(7.4, 3.9), dpi=200)
    xs = np.linspace(0, 1650, 50)
    for r, txt in ((0.10, "rinde 10 % al año"), (0.05, "rinde 5 % al año")):
        ax.plot(xs, xs * 1000 * r / 12 / 1000, color=LINEA, lw=0.9, ls="--" if r == 0.10 else ":")
        xt = 1180 if r == 0.10 else 1640
        ax.text(xt, xt * r / 12 - 0.75, txt, fontsize=7.2, color=TINTA2, ha="right")
    desp = {"C": (16, 0.35), "E": (16, 0.35), "D": (-16, 0.45), "A": (16, -0.6), "B": (16, -0.5), "F": (16, 0.3),
            "G": (16, 0.3), "K": (16, 0.3), "H": (-16, 0.45), "J": (16, 0.3)}
    for m in tabla_m:
        x, y = m["capex"] / 1000, m["neto_mes"] / 1000
        destaca = m["clave"] in ("C", "J", "B")
        ax.scatter([x], [y], s=46 if destaca else 30, color=S1 if destaca else "#9a9994", edgecolor="white",
                   linewidth=1.5, zorder=4)
        dx, dy = desp.get(m["clave"], (12, 0.2))
        ax.text(x + dx, y + dy, f"{m['clave']} {m['corto']}", fontsize=7.2, color=TINTA if destaca else TINTA2,
                ha="left" if dx > 0 else "right", zorder=5)
    ax.axhline(0, color="#9a9994", lw=0.8)
    ax.set_xlim(-40, 1700)
    ax.set_xlabel("inversión total (miles de S/)", fontsize=8, color=TINTA2)
    ax.set_ylabel("utilidad neta en régimen\n(miles de S/ al mes)", fontsize=8, color=TINTA2)
    _estilo_ejes(ax)
    ax.set_title("Ganancia mensual frente al dinero que hay que poner (escenario base)", fontsize=9.5, color=TINTA,
                 loc="left", weight="bold")
    fig.tight_layout()
    fig.savefig(ruta)
    plt.close(fig)


def grafico_rangos(ruta):
    orden = [k for k in al.ORDEN if k != "J"]
    fig, ax = plt.subplots(figsize=(7.4, 3.5), dpi=200)
    for i, k in enumerate(orden):
        crudo = [al.metricas(al.OPC[k], e)["tir"] for e in (0, 1, 2)]
        ts = [(-8 if t is None else max(t * 100, -8)) for t in crudo]
        ax.plot([ts[0], ts[2]], [i, i], color="#b9cfee", lw=5, solid_capstyle="round", zorder=2)
        ax.scatter([ts[1]], [i], s=40, color=S1, zorder=3, edgecolor="white", linewidth=1.5)
        lo = "pérdida" if crudo[0] is None else f"{crudo[0] * 100:.0f}"
        ax.text(ts[2] + 0.6, i, f"{lo} a {crudo[2] * 100:.0f} %", va="center", fontsize=7.2, color=TINTA2)
    ax.set_yticks(range(len(orden)), [f"{k} · {al.OPC[k].corto}" for k in orden], fontsize=8, color=TINTA)
    ax.axvline(al.TASA * 100, color=S2, lw=1.2, ls="--")
    ax.text(al.TASA * 100 + 0.3, -0.75, "meta 10 %", color=TINTA2, fontsize=7.2, va="center")
    ax.set_ylim(len(orden) - 0.5, -1.1)
    ax.set_xlabel("TIR del proyecto (%): barra = pesimista a optimista; punto = base", fontsize=8, color=TINTA2)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.tick_params(axis="x", colors=TINTA2, labelsize=8)
    ax.grid(axis="x", color=REJILLA, lw=0.8)
    ax.set_axisbelow(True)
    ax.set_xlim(-9, 40)
    ax.set_title("Qué tan incierto es cada resultado", fontsize=9.5, color=TINTA, loc="left", weight="bold")
    fig.tight_layout()
    fig.savefig(ruta)
    plt.close(fig)


def grafico_sensibilidad(ruta):
    sens = al.sensibilidad_locales(rentas=tuple(range(10, 31, 1)))
    xs = [r for r, _, _ in sens]
    ys = [v / 1000 for _, v, _ in sens]
    fig, ax = plt.subplots(figsize=(7.4, 3.0), dpi=200)
    ax.axvspan(12, 30, color="#eef3f8", zorder=0)
    ax.text(12.2, max(ys) * 0.92, "rango estimado para el jirón\n(S/ 12-30 por m², sin avisos publicados)", fontsize=7,
            color=TINTA2, va="top")
    ax.plot(xs, ys, color=S1, lw=2, zorder=3)
    ax.axhline(0, color=LINEA, lw=1)
    cero = al.umbral_ingreso(al.OPC["C"], 0) / al.AREA_LOCALES
    base = al.OPC["C"].fases[0].ingreso[1] / al.AREA_LOCALES
    ax.scatter([base], [np.interp(base, xs, ys)], s=40, color=S1, edgecolor="white", linewidth=1.5, zorder=4)
    ax.text(base + 0.3, np.interp(base, xs, ys) - 30, f"base: S/ {base:.1f} por m²", fontsize=7.2, color=TINTA)
    ax.set_xlabel("renta promedio de los locales (S/ por m² al mes)", fontsize=8, color=TINTA2)
    ax.set_ylabel("VAN de C al 10 %\n(miles de S/)", fontsize=8, color=TINTA2)
    _estilo_ejes(ax)
    ax.set_title(f"La decisión depende de la renta de los locales (con la cochera, C rinde 10 % desde ≈ S/ "
                 f"{_renta_equilibrio_c():.0f} por m²)", fontsize=9, color=TINTA, loc="left", weight="bold")
    fig.tight_layout()
    fig.savefig(ruta)
    plt.close(fig)
    return cero


def _renta_equilibrio_c():
    sens = al.sensibilidad_locales(rentas=tuple(np.arange(10, 31, 0.25)))
    for (r0, v0, _), (r1, v1, _) in zip(sens, sens[1:]):
        if v0 < 0 <= v1:
            return r0 + (r1 - r0) * (-v0) / (v1 - v0)
    return float("nan")


def grafico_acumulado(ruta):
    fig, ax = plt.subplots(figsize=(7.4, 3.3), dpi=200)
    series = [("C", S1), ("B", S2), ("A", S3), ("J", S4)]
    for k, c in series:
        fl = al.flujo(al.OPC[k], ESC)
        anios = [f["anio"] for f in fl]
        acum = [(f["acum"] - (f["residual"] if f["anio"] == al.HORIZONTE else 0)) / 1000 for f in fl]
        ax.plot(anios, acum, color=c, lw=2)
        ax.text(anios[-1] + 0.3, acum[-1], f"{k} {al.OPC[k].corto}", color=TINTA2, fontsize=7.2, va="center")
    ax.axhline(0, color=LINEA, lw=1)
    ax.set_xlim(0, al.HORIZONTE + 5.5)
    ax.set_xticks(range(0, al.HORIZONTE + 1, 5))
    ax.set_xlabel("año", fontsize=8, color=TINTA2)
    ax.set_ylabel("caja acumulada\n(miles de S/ nominales)", fontsize=8, color=TINTA2)
    _estilo_ejes(ax)
    ax.set_title("Caja acumulada: cuándo se recupera lo invertido (escenario base, sin valor residual)", fontsize=9.2,
                 color=TINTA, loc="left", weight="bold")
    fig.tight_layout()
    fig.savefig(ruta)
    plt.close(fig)


# --------------------------------------------------------------------------
# Documento
# --------------------------------------------------------------------------
def _pie(canvas, doc):
    canvas.saveState()
    canvas.setFont("Lib", 7.5)
    canvas.setFillColor(GRIS)
    canvas.drawString(18 * mm, 10 * mm, "Alternativas de uso del terreno - Jr. Rodríguez de Mendoza, Mendoza (Amazonas) - oct-2026")
    canvas.drawRightString(192 * mm, 10 * mm, f"Pág. {doc.page}")
    canvas.restoreState()


def _kpis(items, W):
    celdas = [[P(v, "kpi_v") for v, _ in items], [P(l, "kpi_l") for _, l in items]]
    t = Table(celdas, colWidths=[W / len(items) * mm] * len(items))
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), FONDO), ("BOX", (0, 0), (-1, -1), 0.6, colors.white),
                           ("INNERGRID", (0, 0), (-1, -1), 2, colors.white), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                           ("TOPPADDING", (0, 0), (-1, 0), 7), ("BOTTOMPADDING", (0, 1), (-1, 1), 7)]))
    return t


def generar(ruta_pdf, graf_dir):
    os.makedirs(graf_dir, exist_ok=True)
    tab = al.tabla_comparativa(ESC)
    M = {m["clave"]: m for m in tab}
    rutas = {k: os.path.join(graf_dir, f"alt_{k}.png") for k in ("pA", "pC", "pF", "pE", "tir_t", "inv", "rangos", "sens",
                                                                  "acum")}
    figura_planos(rutas, al.umbral_ingreso(al.OPC["E"], 2) / 7, al.umbral_ingreso(al.OPC["D"], 2) / 8)
    grafico_tir_terreno(rutas["tir_t"], tab)
    grafico_inversion_utilidad(rutas["inv"], tab)
    grafico_rangos(rutas["rangos"])
    grafico_sensibilidad(rutas["sens"])
    grafico_acumulado(rutas["acum"])

    venta = al.venta_terreno(ESC)
    terreno = venta["precio"]
    c, b, j, a = M["C"], M["B"], M["J"], M["A"]
    eq_c = _renta_equilibrio_c()
    u_cons = al.umbral_ingreso(al.OPC["E"], 2) / 7
    u_dep = al.umbral_ingreso(al.OPC["D"], 2) / 8
    u_cancha = al.umbral_ingreso(al.OPC["F"], 0) / 30 / 55
    e_rb = al.rb.ESCENARIOS[1]
    u_abon = (al.umbral_ingreso(al.OPC["A"], 0) - e_rb.tickets_dia * e_rb.ticket_prom * 30 - e_rb.motos * e_rb.tarifa_moto) / e_rb.tarifa_mensual
    loc = al.OPC["C"].fases[0]
    renta_base_m2 = loc.ingreso[1] / al.AREA_LOCALES
    dep_neto = al.DEPOSITO * (1 - al.IMP_ALQUILER)

    doc = SimpleDocTemplate(ruta_pdf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=15 * mm,
                            bottomMargin=16 * mm, title="Alternativas de uso del terreno - Mendoza",
                            author="Anteproyecto")
    W = 174
    E = []

    # ---------------- 1. Respuesta corta
    E += [P("¿QUÉ HACER CON EL TERRENO?", "title"), Spacer(1, 1.5 * mm),
          P("Alternativas para maximizar la ganancia presente y futura del lote esquinero de 820 m² en el "
            "Jr. Rodríguez de Mendoza, Mendoza (Amazonas)", "subtitle"), Spacer(1, 4 * mm),
          P("La respuesta corta", "h1")]
    E += bullets([
        f"<b>El activo valioso no son los 820 m², es la esquina con 30 m de frente al jirón.</b> Un local a la calle "
        f"rinde 3 a 4 veces más por m² que una plaza de estacionamiento (≈ S/ 18 frente a ≈ S/ 5 por m² al mes).",
        f"<b>Recomendación: alternativa C.</b> Construya una franja de locales de 1 piso en la esquina y el jirón "
        f"(local ancla de 100 m² + 3 locales) con zapatas y columnas listas para 2 pisos más, y deje el fondo como "
        f"cochera de abonados sin personal con ingreso por la calle lateral. Inversión ≈ {miles(c['capex'])}, "
        f"utilidad neta ≈ {S(c['neto_mes'])} al mes en régimen, TIR {pct(c['tir'])}.",
        f"<b>Condición:</b> C solo conviene si en el jirón los locales se alquilan a <b>≥ S/ {eq_c:.0f} por m² al "
        f"mes</b> (≈ S/ {eq_c * 45:,.0f} por un local de 45 m²). Es el dato que más mueve el resultado y no hay avisos "
        f"publicados de Mendoza: hay que verificarlo en la calle antes de invertir.",
        f"<b>No construya todavía los pisos superiores:</b> los consultorios pagarían la obra desde ≈ S/ {u_cons:,.0f} "
        f"al mes cada uno y los minidepartamentos desde ≈ S/ {u_dep:,.0f}, por encima de lo que hoy se paga en la zona. "
        f"Revíselo cuando el nuevo hospital esté funcionando.",
        f"<b>El estacionamiento techado del anteproyecto (A) rinde poco</b> con guardián (TIR {pct(a['tir'])}): "
        f"solo tiene sentido si lo opera la familia. Hostal, local de eventos y terminal de vans no pagan la inversión "
        f"en el escenario base.",
        f"<b>Mientras valida (3-6 meses):</b> un estacionamiento descubierto barato (B, ≈ {miles(b['capex'])}) o "
        f"alquilar el terreno a un operador (J) generan caja sin cerrar ninguna opción. Dejar el terreno sin uso "
        f"solo rinde su valorización (≈ {al.PLUSVALIA * 100:.0f} % al año)."])
    E.append(Spacer(1, 3 * mm))
    E.append(_kpis([(miles(c["capex"]), "inversión de C"), (S(c["neto_mes"]), "utilidad neta al mes (régimen)"),
                    (pct(c["tir"]), "TIR del proyecto C"), (f"{c['payback']:.1f} años", "recuperación de la inversión"),
                    (pct(c["tir_terreno"]), f"rinde contando el terreno (vender y depositar: {pct(dep_neto)})")], W))
    E.append(Spacer(1, 3 * mm))
    E.append(Image(rutas["tir_t"], width=W * mm, height=W * mm * 3.6 / 7.4))
    E.append(P("Rentabilidad para el propietario si el terreno se «aporta» hoy a valor de mercado (S/ "
               f"{terreno:,.0f}, a confirmar con tasación) y se recupera valorizado en el año 20. Por debajo de la línea "
               "naranja conviene más vender el terreno y depositar el dinero; J supone que aparece un inquilino para "
               "el lote completo.", "caption"))
    E.append(PageBreak())

    # ---------------- 2. Mercado y terreno
    E.append(P("1. Lo que dice el mercado de Mendoza", "h1"))
    E += bullets([
        "<b>Ciudad pequeña pero en crecimiento:</b> ≈ 5,100 habitantes en 2017 (3,356 en 2007) y un estimado de "
        "6,400-7,300 en 2026; la provincia tiene ≈ 33,000 y creció 1.3 % anual entre 2017 y 2025.",
        "<b>El jirón es el eje comercial e institucional:</b> la agencia del Banco de la Nación está en el "
        "Jr. Toribio Rodríguez de Mendoza N.º 309. No se encontraron agencias de cajas municipales ni de Mibanco: "
        "posible inquilino ancla para la esquina.",
        "<b>El gran motor de demanda es el nuevo Hospital María Auxiliadora</b> (II-1, más de S/ 100 MM, 90 % de avance "
        "en abril de 2026): traerá personal de salud, pacientes y familiares (consultorios, farmacias, comida, "
        "vivienda temporal y estacionamiento). Su apertura todavía tiene riesgos de energización y personal.",
        "<b>Turismo débil:</b> el 94 % de los visitantes son de la provincia y el 91 % se aloja con familiares; la "
        "ocupación de hospedajes en Amazonas ronda el 20-23 %. Un hostal es una apuesta de alto riesgo.",
        "<b>Transporte:</b> 4 empresas autorizadas en la ruta a Chachapoyas y sin terminal formal; la carretera "
        "Chachapoyas–Mendoza (≈ S/ 369 MM) sigue en estudio: valorización a mediano plazo.",
        "<b>Precios:</b> casi no hay avisos de Mendoza en internet. Locales en el Jr. Amazonas de Chachapoyas: "
        "S/ 54-98 por m² al mes (25-55 m²); Moyobamba S/ 29-40. Para el jirón de Mendoza se estima S/ 12-30.",
        "<b>Impuestos y crédito:</b> alquilar como persona natural paga 5 % de lo cobrado, sin IGV (favorece el "
        "alquiler pasivo). El crédito en cajas cuesta 13-14 % (hipotecario) y más de 45 % (microempresa): "
        "financiar con caja una obra que rinde 11 % destruye valor."])
    E.append(P("2. Qué cabe en el terreno", "h1"))
    from PIL import Image as PImg

    def img(ruta, ancho):
        w, h = PImg.open(ruta).size
        return Image(ruta, width=ancho * mm, height=ancho * mm * h / w)

    cw = (W - 4) / 3
    grilla = Table([[img(rutas["pA"], cw), img(rutas["pC"], cw), img(rutas["pF"], cw)]], colWidths=[(cw + 1.3) * mm] * 3)
    grilla.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                                ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
    E.append(KeepTogether([grilla, Spacer(1, 2 * mm), img(rutas["pE"], W * 0.92),
                           P("Esquemas a escala sobre la geometría del anteproyecto. En C la franja comercial de 8 m de "
                             "fondo ocupa 261 m² y en el fondo quedan 18 plazas del diseño actual, con un solo portón de "
                             "6 m en la calle lateral. Por el ángulo de 60° en el vértice B solo cabe una cancha de "
                             "25 × 15 m.", "caption")]))
    E.append(PageBreak())

    # ---------------- 3. Comparación
    E.append(P("3. Comparación de las 10 alternativas (escenario base)", "h1"))
    filas = [["Alt.", "Alternativa", "Inversión", "Utilidad neta al mes", "TIR", "Recupera en", "Contando terreno",
              "Riesgo"]]
    for m in tab:
        op = al.OPC[m["clave"]]
        filas.append([f"<b>{m['clave']}</b>", op.nombre, miles(m["capex"]), S(m["neto_mes"]), pct(m["tir"]),
                      "—" if m["capex"] == 0 else ("no" if m["payback"] is None else f"{m['payback']:.1f} años"),
                      pct(m["tir_terreno"]), op.riesgo])
    filas.append(["", "<i>Vender el terreno y depositar al 6 %</i>", "—", S(venta["renta_mes"]), "—", "—",
                  pct(dep_neto), "bajo"])
    E.append(tabla(filas, (8, 60, 19, 19, 14, 17, 17, 20), alinear_der=(2, 3, 4, 5, 6)))
    E.append(P("Utilidad neta al mes: en régimen (año 3 en adelante), a precios de hoy, después de gastos, personal e "
               "impuestos. TIR y VAN a 20 años con 3 % de crecimiento anual y valor residual de lo construido. "
               "«Contando terreno»: rentabilidad anual del propietario incluyendo el valor del lote.", "small"))
    E.append(Spacer(1, 3 * mm))
    E.append(Image(rutas["inv"], width=W * mm, height=W * mm * 3.9 / 7.4))
    E.append(P("Cada punto es una alternativa. Por encima de la línea discontinua la utilidad mensual rinde más de 10 % "
               "al año sobre la inversión.", "caption"))
    E.append(PageBreak())

    # ---------------- 4. Incertidumbre y umbrales
    E.append(P("4. Qué tan seguro es cada resultado", "h1"))
    E.append(P("Cada alternativa se evaluó en tres escenarios. El pesimista combina rentas o demanda bajas con 15 % de "
               "sobrecosto de obra; el optimista, rentas altas con 8 % de ahorro. Las barras muestran el rango de la "
               "TIR."))
    E.append(Image(rutas["rangos"], width=W * mm, height=W * mm * 3.5 / 7.4))
    E.append(Spacer(1, 2 * mm))
    E.append(Image(rutas["sens"], width=W * mm, height=W * mm * 3.0 / 7.4))
    E.append(P("Umbrales: el ingreso a partir del cual cada inversión paga el 10 % anual", "h2"))
    E.append(tabla([
        ["Decisión", "Umbral para que convenga", "Supuesto base", "Cómo comprobarlo"],
        ["Construir los locales (C)", f"≥ S/ {eq_c:.0f} por m² al mes en promedio (≈ S/ {eq_c * 45:,.0f} por local de 45 m²)",
         f"S/ {renta_base_m2:.1f} por m²", "Preguntar el alquiler a 8-10 locales del jirón"],
        ["2.º piso de consultorios (E)", f"≥ S/ {u_cons:,.0f} al mes por consultorio", "S/ 550",
         "Médicos y odontólogos del nuevo hospital"],
        ["Pisos de minidepartamentos (D)", f"≥ S/ {u_dep:,.0f} al mes por minidepartamento", "S/ 600",
         "Personal de salud y del Estado que llega de fuera"],
        ["Cancha techada (F)", f"≥ {u_cancha:.1f} horas vendidas por día a S/ 55", "3.5 h por día",
         "Contar reservas en las canchas existentes"],
        ["Estacionamiento techado (A)", f"≥ {u_abon:.0f} abonados a S/ 120 con la rotación base (con guardián)",
         "18 abonados", "Lista de interesados con adelanto"],
    ], (38, 56, 26, 54)))
    E.append(PageBreak())

    # ---------------- 5. Estrategia
    E.append(P("5. Estrategia recomendada por etapas", "h1"))
    E.append(P("La estrategia gana hoy con lo que el mercado ya paga (locales a la calle) y deja la estructura "
               "preparada para crecer cuando la demanda lo confirme. Así no se apuesta todo a supuestos que todavía no "
               "se pueden verificar."))
    E.append(tabla([
        ["Etapa", "Cuándo", "Qué hacer", "Inversión aprox.", "Para pasar a la siguiente"],
        ["0. Validar", "Meses 0-4",
         "Sondeo de alquileres en el jirón; certificado de parámetros; tasación; buscar inquilino ancla con carta de "
         "intención. Opcional: estacionamiento descubierto (B) o alquilar el lote (J) para generar caja.",
         f"S/ 3-5 mil (trámites) · B: {miles(b['capex'])}", f"Renta validada ≥ S/ {eq_c:.0f} por m² y ancla interesado"],
        ["1. Locales + cochera (C)", "Meses 4-12",
         "Franja comercial de 1 piso con zapatas y columnas para 3 pisos; cochera de 18 abonados con portón "
         "automático. Construir por tramos si hace falta: primero la esquina y el local contiguo.",
         miles(c["capex"]), "Locales ≥ 80 % ocupados y hospital en funcionamiento"],
        ["2. Crecer en altura (E o D)", "Año 2-5",
         "Un piso de consultorios (E) o minidepartamentos (D) solo si se superan los umbrales de la sección 4.",
         f"{miles(al.OPC['E'].fases[2].capex())} (E) · {miles(al.OPC['D'].fases[2].capex())} (D)",
         "Contratos firmados o lista de espera"],
        ["3. Techar la cochera", "Cuando haya demanda",
         "Reutilizar el diseño metálico del anteproyecto (pórticos en T) solo sobre las filas del fondo.",
         "≈ S/ 90-120 mil", "≥ 15 abonados que paguen la diferencia"],
    ], (26, 18, 70, 28, 32)))
    E.append(Spacer(1, 3 * mm))
    E.append(Image(rutas["acum"], width=W * mm, height=W * mm * 3.3 / 7.4))
    E.append(P("¿Y si vendo el terreno?", "h2"))
    E.append(P(f"A S/ {al.VALOR_M2[1]:,.0f} por m² el lote valdría ≈ {S(terreno)} (entre {S(al.AREA_LOTE * al.VALOR_M2[0])} y "
               f"{S(al.AREA_LOTE * al.VALOR_M2[2])}; no hay compraventas publicadas). Depositado al {al.DEPOSITO * 100:.0f} % "
               f"rendiría ≈ {S(venta['renta_mes'])} al mes, sin trabajo, pero se pierde la valorización por el hospital y la "
               f"carretera y la opción de construir. Contando el terreno, C rinde {pct(c['tir_terreno'])} anual frente a "
               f"{pct(dep_neto)} de vender y depositar: conviene quedarse con el lote y desarrollarlo, siempre que la renta "
               f"de los locales se confirme. Dejarlo sin uso es la peor opción ({al.PLUSVALIA * 100:.0f} % al año)."))
    E.append(PageBreak())

    # ---------------- 6. Fichas
    E.append(P("6. Supuestos de cada alternativa", "h1"))
    filas = [["Alt.", "Qué es", "Ingresos supuestos (base)", "Gastos e impuestos", "Notas"]]
    det = {
        "C": ("Locales: esquina 100 m² a S/ 20 por m² y 3 locales (135 m²) a S/ 18; 85 % ocupados. Cochera: 18 plazas a "
              "S/ 90, 75 % ocupadas.", "Mantenimiento, predial y seguro ≈ S/ 6 mil al año; 5 % de impuesto al alquiler; "
              "cochera sin personal."),
        "E": ("C + 7 consultorios a S/ 550 desde el año 3 (80 % ocupados).", "Gastos del piso ≈ S/ 8.6 mil al año; 5 %."),
        "D": ("C + 8 minidepartamentos a S/ 600 desde el año 4 (85 % ocupados).", "Gastos ≈ S/ 15.6 mil al año; 5 %."),
        "A": ("Igual que rentabilidad.py: 18 abonados a S/ 120, 12 tickets al día a S/ 4.50 y 6 motos a S/ 40.",
              "Guardián con cargas, energía, mantenimiento 1 %, predial, seguro y Nuevo RUS ≈ S/ 27 mil al año."),
        "B": ("15 abonados a S/ 95, 11 tickets al día a S/ 4 y 6 motos a S/ 40 (menos que techado por la lluvia).",
              "Guardián ≈ S/ 15.3 mil y otros ≈ S/ 7 mil al año; reafirmado en el año 6."),
        "F": ("3.5 horas vendidas al día a S/ 55.", "Encargado, energía de 8 kW, mantenimiento; cambio de grass en los "
              "años 9 y 18."),
        "G": ("4 eventos al mes a S/ 1,500.", "20 % del ingreso en personal por evento; ≈ S/ 22 mil fijos; 10 % de impuestos."),
        "K": ("4 boleterías a S/ 600 y 20 salidas al día a S/ 4.", "Un encargado, limpieza, energía, mantenimiento ≈ S/ 33 mil al año."),
        "H": ("16 habitaciones a S/ 75 por noche, 35 % de ocupación.", "3 trabajadores, 25 % variable, ≈ S/ 94 mil fijos; "
              "IGV reducido de hospedaje."),
        "J": ("Alquiler del lote completo a S/ 2,400 al mes (≈ S/ 2.9 por m²).", "Predial; 5 % de impuesto al alquiler."),
    }
    for k in al.ORDEN:
        op = al.OPC[k]
        ing, gas = det[k]
        filas.append([f"<b>{k}</b>", f"<b>{op.nombre}.</b> {op.resumen}", ing, gas, " ".join(op.notas)])
    E.append(tabla(filas, (8, 46, 38, 38, 44)))
    E.append(PageBreak())

    # ---------------- 7. Validación y fuentes
    E.append(P("7. Qué validar antes de invertir", "h1"))
    E += bullets([f"<b>{q}.</b> {como}" for q, como in al.VALIDAR])
    E.append(P("Supuestos y limitaciones", "h2"))
    E += bullets([
        "Montos en soles de octubre de 2026 con IGV; tasa de descuento 10 % anual; crecimiento de rentas y gastos 3 %; "
        "horizonte 20 años; valor residual lineal de lo construido (50 años en albañilería, 30 en estructura metálica).",
        "Los costos de obra son estimaciones por m² (no hay costos publicados de Mendoza) más 10 % de supervisión e "
        "imprevistos; deben reemplazarse por cotizaciones locales.",
        "Las rentas y tarifas de Mendoza son estimaciones por comparables (Chachapoyas, Moyobamba, Lima) con confianza "
        "baja. El modelo en Excel permite cambiarlas y recalcula todo.",
        "Los usos, alturas y estacionamientos exigidos dependen del certificado de parámetros urbanísticos; la zona "
        "sísmica (2 o 3) y el suelo pueden cambiar el costo de la estructura para 3 pisos.",
        "No se modela el financiamiento: con crédito de caja (13-14 %) la rentabilidad del propietario sería menor."])
    E.append(P("Fuentes principales (investigación de octubre de 2026)", "h2"))
    filas = [["Tema", "Dato", "Fuente", "Confianza"]]
    for tema, dato, fuente, fecha, conf in al.FUENTES:
        filas.append([tema, dato, f"{fuente} ({fecha})", conf])
    E.append(tabla(filas, (26, 88, 44, 16)))

    doc.build(E, onFirstPage=_pie, onLaterPages=_pie)
    return ruta_pdf


if __name__ == "__main__":
    import sys
    salida = sys.argv[1] if len(sys.argv) > 1 else "salida/Alternativas_Uso_Terreno.pdf"
    generar(salida, os.path.join(os.path.dirname(salida) or ".", "graficos"))
    print("PDF:", salida)
