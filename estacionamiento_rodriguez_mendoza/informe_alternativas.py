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
from shapely.geometry import box
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
    for seg in (g.PORTON_INGRESO, g.PORTON_SALIDA):
        xs, ys = seg.xy
        ax.plot(xs, ys, color=S2, lw=3, zorder=5, solid_capstyle="butt")
    _texto(ax, (20, -2.6), "28 plazas techadas · 13 columnas · 2 portones", fs=6.6, color=TINTA2)


def plano_locales(ax, titulo="C · Esquina + 3 locales + cochera (C1: solo la esquina)"):
    _lote(ax, titulo)
    esq, locales, nucleo, comercial = _franjas()
    _poly(ax, esq, F_LOCAL, z=3)
    for lc in locales:
        _poly(ax, lc, F_LOCAL, z=3, ls="--")
    _poly(ax, nucleo, "#f1e6dc", z=3, hatch="///", ls="--")
    libres = [p for p in g.PLAZAS if not p.poly.intersects(comercial.buffer(0.3))]
    _poly(ax, unary_union([g.CIRCULACION]).difference(comercial), F_COCHERA, ec="none", z=2)
    for p in libres:
        _poly(ax, p.poly, "white", ec=LINEA, lw=0.45, z=3)
    a, b = g.DA.punto(D_PAS[0], 0), g.DA.punto(D_PAS[1], 0)
    ax.plot([a[0], b[0]], [a[1], b[1]], color=S2, lw=3, zorder=5, solid_capstyle="butt")
    ce = esq.centroid
    _texto(ax, (ce.x, ce.y), "Esquina\n100 m²", fs=6.6)
    for lc, area in zip(locales, ("39 m²", "48 m²", "48 m²")):
        cc = lc.centroid
        _texto(ax, (cc.x, cc.y), area, fs=6.3)
    _texto(ax, ((a[0] + b[0]) / 2 + g.DA.n[0] * 1.6, (a[1] + b[1]) / 2 + g.DA.n[1] * 1.6), "portón 6.5 m", fs=5.6,
           color=S2)
    _texto(ax, (25.0, 8.6), "cochera", fs=6.2, color=TINTA2)
    _texto(ax, (20, -2.6), f"{len(libres)} plazas: 6 para los locales y 12 de abonados · discontinuo = etapa posterior",
           fs=6.4, color=TINTA2)


def plano_cancha(ax):
    _lote(ax, "F · Cancha techada (fulbito recreativo)")
    cancha = Rectangle((9.9, 1.0), 25, 15, fc=F_CANCHA, ec="#3d8f6b", lw=1.0, zorder=3)
    ax.add_patch(cancha)
    techo = box(9.4, 0.5, 35.4, 16.5).intersection(g.LOTE.buffer(-0.2))
    _poly(ax, techo, "none", ec="#7fa6d6", lw=0.8, ls="--", z=4)
    ax.plot([22.4, 22.4], [1.0, 16.0], color="white", lw=1.2, zorder=4)
    ax.add_patch(plt.Circle((22.4, 8.5), 2.2, fc="none", ec="white", lw=1.2, zorder=4))
    _texto(ax, (22.4, 12.6), "25 × 15 m sin franja\n(futsal pide 16 m de ancho)", fs=6.3)
    vest = g.DA.rect(2, 8, 0.4, 6.5).intersection(g.LOTE)
    _poly(ax, vest, "#f1e6dc", z=3)
    cv = vest.centroid
    _texto(ax, (cv.x, cv.y), "vestuarios", fs=5.8, color=TINTA2)
    _texto(ax, (20, -2.6), "el frente al jirón queda como cerco: se pierde el valor comercial", fs=6.6, color=TINTA2)


def elevacion(ax, u_cons, u_dep):
    ax.set_title("Crecer en altura: solo cuando la renta de los pisos altos pague la obra", fontsize=9, color=TINTA,
                 loc="left", weight="bold")
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_xlim(-0.5, 30.5)
    ax.set_ylim(-3.0, 6.9)
    ax.plot([-1, 31], [0, 0], color=TINTA, lw=1.2)
    h1, h = 3.4, 2.8
    anchos = [(0, 5.5, "núcleo"), (5.5, 11.5, "local"), (11.5, 17.5, "local"), (17.5, 23.5, "local"), (23.5, 30, "esquina")]
    for x0, x1, t in anchos:
        ls = "-" if t == "esquina" else "--"
        ax.add_patch(Rectangle((x0, 0), x1 - x0, h1, fc=F_LOCAL if t != "núcleo" else "#f1e6dc", ec=LINEA, lw=0.8,
                               ls=ls, hatch="///" if t == "núcleo" else None))
        if t != "núcleo":
            ax.add_patch(Rectangle((x0 + 0.6, 0), x1 - x0 - 1.2, 2.4, fc="#d9d7d0", ec=LINEA, lw=0.5))
        _texto(ax, ((x0 + x1) / 2, 2.9), t, fs=6.6)
    ax.add_patch(Rectangle((0, h1), 30, h, fc=F_FUTURO, ec="#c98500", lw=0.8, ls="--"))
    _texto(ax, (15, h1 + h / 2), f"2.º piso: consultorios (E) si se alquilan a ≥ S/ {u_cons:,.0f} al mes\n"
                                 f"o minidepartamentos (D) a ≥ S/ {u_dep:,.0f} al mes · hoy fuera de alcance", fs=6.6)
    _texto(ax, (15, -1.1), "Fachada al Jr. Rodríguez de Mendoza (30 m). Línea continua = construir solo con contrato firmado; "
                           "discontinua = etapas condicionadas a umbrales de renta.", fs=6.3, color=TINTA2)


def figura_planos(rutas, u_cons, u_dep):
    """Un PNG por esquema (recortado al contenido) para componerlos en una tabla del PDF."""
    for clave, fn in (("pA", plano_actual), ("pC", plano_locales), ("pF", plano_cancha)):
        fig, ax = plt.subplots(figsize=(3.7, 3.0), dpi=220)
        fn(ax)
        fig.savefig(rutas[clave], bbox_inches="tight", pad_inches=0.04)
        plt.close(fig)
    fig, ax = plt.subplots(figsize=(7.4, 1.9), dpi=220)
    elevacion(ax, u_cons, u_dep)
    fig.savefig(rutas["pE"], bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)


# --------------------------------------------------------------------------
# Gráficos
# --------------------------------------------------------------------------
def _ejes_horizontales(ax):
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.spines["bottom"].set_color("#9a9994")
    ax.tick_params(axis="x", colors=TINTA2, labelsize=8)
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", color=REJILLA, lw=0.8)
    ax.set_axisbelow(True)


def grafico_van(ruta):
    """VAN al 10 % por alternativa: punto = base, barra = pesimista a optimista."""
    claves = list(al.ORDEN)
    fig, ax = plt.subplots(figsize=(7.4, 3.9), dpi=200)
    for i, k in enumerate(claves):
        v = [al.metricas(al.OPC[k], e)["van"] / 1000 for e in (0, 1, 2)]
        sin_cap = al.OPC[k].capital == "sin capital"
        c_barra, c_punto = ("#9cc0ec", "#174f96") if sin_cap else ("#d6d5d0", "#6f6e69")
        ax.plot([v[0], v[2]], [i, i], color=c_barra, lw=6, solid_capstyle="round", zorder=2)
        ax.scatter([v[1]], [i], s=42, color=c_punto, zorder=3, edgecolor="white", linewidth=1.5)
        x_txt = max(v[2], -400) + 18
        ax.text(x_txt, i, f"{v[1]:+,.0f} mil", va="center", fontsize=7.2, color=TINTA if sin_cap else TINTA2)
    ax.set_yticks(range(len(claves)), [f"{k} · {al.OPC[k].corto}" for k in claves], fontsize=8, color=TINTA)
    ax.set_ylim(len(claves) - 0.5, -0.8)
    ax.axvline(0, color=S2, lw=1.2, ls="--")
    ax.text(-12, -0.62, "← destruye valor", fontsize=7.2, color=TINTA2, va="center", ha="right")
    ax.text(12, -0.62, "crea valor →", fontsize=7.2, color=TINTA2, va="center", ha="left")
    ax.set_xlim(-560, 300)
    ax.set_xlabel("VAN al 10 % anual en 20 años (miles de S/): punto = base; barra = pesimista a optimista "
                  "(las de la izquierda continúan)", fontsize=7.6, color=TINTA2)
    _ejes_horizontales(ax)
    ax.set_title("Solo las alternativas sin inversión crean valor en el escenario base", fontsize=9.5, color=TINTA,
                 loc="left", weight="bold")
    fig.tight_layout()
    fig.savefig(ruta)
    plt.close(fig)


def grafico_tir_terreno(ruta, tabla_m):
    filas = sorted(tabla_m, key=lambda m: m["tir_terreno"] if m["tir_terreno"] is not None else -1)
    fig, ax = plt.subplots(figsize=(7.4, 3.6), dpi=200)
    ys = np.arange(len(filas))
    vals = [(m["tir_terreno"] or 0) * 100 for m in filas]
    cols = ["#174f96" if al.OPC[m["clave"]].capital == "sin capital" else S1 for m in filas]
    ax.barh(ys, vals, height=0.62, color=cols, edgecolor="white", linewidth=2)
    ax.set_yticks(ys, [f"{m['clave']} · {m['corto']}" for m in filas], fontsize=8, color=TINTA)
    for y, v in zip(ys, vals):
        ax.text(max(v, 0) + 0.12, y, f"{v:.1f} %", va="center", fontsize=7.6, color=TINTA2)
    dep = al.deposito_neto() * 100
    ax.axvline(dep, color=S2, lw=1.4, ls="--")
    ax.text(dep + 0.1, -1.0, f"vender y depositar: {dep:.1f} %", color=TINTA2, fontsize=7.4, va="center")
    pl = al.PLUSVALIA[ESC] * 100
    ax.axvline(pl, color=LINEA, lw=1.0, ls=":")
    ax.text(pl - 0.1, -1.0, f"dejarlo sin uso: {pl:.1f} %", color=TINTA2, fontsize=7.4, va="center", ha="right")
    ax.set_ylim(-1.5, len(filas) - 0.4)
    ax.set_xlim(min(-1, min(vals) - 0.5), max(vals) + 2.2)
    ax.set_xlabel("rentabilidad anual para el propietario, contando el valor del terreno (%)", fontsize=8, color=TINTA2)
    _ejes_horizontales(ax)
    ax.set_title("¿Rinde más usar el terreno o venderlo? (escenario base, 20 años)", fontsize=9.5, color=TINTA,
                 loc="left", weight="bold")
    fig.tight_layout()
    fig.savefig(ruta)
    plt.close(fig)


def grafico_sensibilidad(ruta, u):
    sens = al.sensibilidad_locales(rentas=tuple(range(10, 33)))
    xs = [r for r, _, _ in sens]
    ys = [vl / 1000 for _, _, vl in sens]
    fig, ax = plt.subplots(figsize=(7.4, 2.9), dpi=200)
    ax.axvspan(12, 18, color="#eef3f8", zorder=0)
    ax.text(12.2, max(ys) * 0.88, "renta estimada hoy en el jirón\n(S/ 12-18 por m²)", fontsize=7, color=TINTA2, va="top")
    ax.plot(xs, ys, color=S1, lw=2, zorder=3)
    ax.axhline(0, color=LINEA, lw=1)
    for x, txt in ((u["locales_m2_contrato"], "con contratos firmados"), (u["locales_m2"], "sin contrato (80 % ocupado)")):
        ax.axvline(x, color=S2, lw=1, ls="--")
        ax.text(x + 0.2, min(ys) * 0.75, f"{txt}:\nS/ {x:.1f} por m²", fontsize=7, color=TINTA2)
    ax.set_xlabel("renta de los 3 locales del jirón (S/ por m² al mes)", fontsize=8, color=TINTA2)
    ax.set_ylabel("VAN de los 3 locales\n(miles de S/)", fontsize=8, color=TINTA2)
    _estilo_ejes(ax)
    ax.set_title("Los 3 locales del jirón empiezan a crear valor desde S/ 19-24 por m²", fontsize=9.5, color=TINTA,
                 loc="left", weight="bold")
    fig.tight_layout()
    fig.savefig(ruta)
    plt.close(fig)


def grafico_acumulado(ruta):
    fig, ax = plt.subplots(figsize=(7.4, 3.0), dpi=200)
    ult = {}
    for k, c in (("L", S1), ("J", S2), ("C1", S3), ("C", S4)):
        fl = al.flujo(al.OPC[k], ESC)
        anios = [f["anio"] for f in fl]
        acum = [f["acum_sr"] / 1000 for f in fl]
        ax.plot(anios, acum, color=c, lw=2)
        ult[k] = acum[-1]
    # etiquetas al final de cada línea, separadas para que no se encimen
    ys = sorted(ult.items(), key=lambda kv: kv[1])
    pos, prev = {}, -1e9
    for k, y in ys:
        y = max(y, prev + 42)
        pos[k] = prev = y
    for k, y in pos.items():
        ax.text(al.HORIZONTE + 0.3, y, f"{k} {al.OPC[k].corto}", color=TINTA2, fontsize=7.2, va="center")
    ax.axhline(0, color=LINEA, lw=1)
    ax.set_xlim(0, al.HORIZONTE + 6)
    ax.set_xticks(range(0, al.HORIZONTE + 1, 5))
    ax.set_xlabel("año", fontsize=8, color=TINTA2)
    ax.set_ylabel("caja acumulada\n(miles de S/ nominales)", fontsize=8, color=TINTA2)
    _estilo_ejes(ax)
    ax.set_title("Caja acumulada (escenario base, sin valor residual): arrendar gana desde el primer año", fontsize=9.2,
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


def _cuota(monto, tasa_anual, anios):
    i = (1 + tasa_anual) ** (1 / 12) - 1
    n = anios * 12
    return monto * i / (1 - (1 + i) ** -n)


def generar(ruta_pdf, graf_dir):
    os.makedirs(graf_dir, exist_ok=True)
    tab = al.tabla_comparativa(ESC)
    M = {m["clave"]: m for m in tab}
    u = al.umbrales(ESC)
    rutas = {k: os.path.join(graf_dir, f"alt_{k}.png") for k in ("pA", "pC", "pF", "pE", "van", "tir_t", "sens", "acum")}
    figura_planos(rutas, u["consultorio"], u["minidepto"])
    grafico_van(rutas["van"])
    grafico_tir_terreno(rutas["tir_t"], tab)
    grafico_sensibilidad(rutas["sens"], u)
    grafico_acumulado(rutas["acum"])

    venta = al.venta_terreno(ESC)
    terreno = venta["precio"]
    dep = al.deposito_neto()
    pl = al.PLUSVALIA[ESC]
    J, L, C1, C, A = M["J"], M["L"], M["C1"], M["C"], M["A"]
    m_pes = {k: al.metricas(al.OPC[k], 0) for k in ("J", "L")}
    m_opt = {k: al.metricas(al.OPC[k], 2) for k in ("J", "L")}
    t_venta = al.tasacion_equilibrio("J")
    cap_esq, cap_loc, cap_coch = (f.capex() for f in al.OPC["C"].fases)
    abon = u["cochera_abonados"] * 0.7

    doc = SimpleDocTemplate(ruta_pdf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=15 * mm,
                            bottomMargin=16 * mm, title="Alternativas de uso del terreno - Mendoza",
                            author="Anteproyecto")
    W = 174
    E = []

    # ---------------- 1. Respuesta corta
    E += [P("¿QUÉ HACER CON EL TERRENO?", "title"), Spacer(1, 1.5 * mm),
          P("Alternativas para maximizar la ganancia presente y futura del lote esquinero de 820 m² en el "
            "Jr. Rodríguez de Mendoza, Mendoza (Amazonas)", "subtitle"), Spacer(1, 3 * mm),
          P("La respuesta corta", "h1")]
    E += bullets([
        f"<b>Hoy no conviene construir nada grande.</b> Con lo que se paga en Mendoza (≈ S/ 650 al mes por un local de "
        f"45 m² y ≈ S/ 1,300 por una esquina de 100 m² sin contrato), ninguna obra paga el 10 % anual. La mejor, "
        f"esquina + cochera (C1), rinde {pct(C1['tir'])}; la franja completa de locales (C), {pct(C['tir'])}; el "
        f"estacionamiento techado del anteproyecto (A) pierde dinero con guardián. Ninguna supera un depósito a plazo "
        f"({dep * 100:.0f} %).",
        f"<b>Ganancia presente, sin poner capital:</b> arriende el lote completo (J) o ceda la esquina en derecho de "
        f"superficie a quien construya su local (L). Dejan ≈ {S(L['neto_mes'])} al mes netos en el escenario base "
        f"(VAN ≈ {miles(L['van'])}) y siguen siendo positivas en el pesimista. Mientras aparece el inquilino: ingresos "
        f"puente sin inversión (panel publicitario, ferias, alquiler mensual a contratistas).",
        f"<b>Construya por módulos y solo con contrato firmado:</b> la esquina cuando un inquilino firme ≥ "
        f"{S(u['esquina_contrato'])} al mes a 5 años o más; los 3 locales del jirón cuando haya compromisos a ≥ "
        f"S/ {u['locales_m2_contrato']:.0f} por m² (≈ {S(u['locales_m2_contrato'] * 45)} por 45 m²); la cochera con "
        f"≥ {abon:.0f} abonados que paguen 3 meses por adelantado.",
        f"<b>Ganancia futura:</b> el lote se valoriza solo (≈ {pl * 100:.1f} % al año estimado, con la carretera "
        f"Chachapoyas–Mendoza en camino). Los pisos superiores no pagan hoy: consultorios desde ≈ "
        f"{S(u['consultorio'])} y minidepartamentos desde ≈ {S(u['minidepto'])} al mes cada uno. Revíselo en 3-5 años.",
        f"<b>¿Vender?</b> Arrendado, el lote rinde ≈ {pct(J['tir_terreno'])} al año contando su valor; vendido y "
        f"depositado, ≈ {pct(dep)}. Si le ofrecen más de ≈ S/ {t_venta:,.0f} por m² (≈ {miles(t_venta * al.AREA_LOTE)}) "
        f"y no necesita el lote, vender rinde más. Pida una tasación antes de decidir.",
        "<b>Evite:</b> hostal, local de eventos, cancha techada, minidepartamentos y endeudarse con caja municipal "
        "(13-14 %) o crédito de microempresa (más de 45 %) para cualquiera de estas obras."])
    E.append(Spacer(1, 2.5 * mm))
    E.append(_kpis([("S/ 0", "inversión para arrendar el lote o ceder la esquina"),
                    (S(L["neto_mes"]), f"renta neta al mes de L o J (base; {S(m_pes['J']['neto_mes'])}-"
                                       f"{S(m_opt['J']['neto_mes'])} según escenario)"),
                    (S(u["esquina_contrato"]), "contrato mínimo al mes para construir la esquina"),
                    (f"S/ {u['locales_m2_contrato']:.0f}-{u['locales_m2']:.0f}", "por m² al mes para construir los 3 locales"),
                    (f"S/ {t_venta:,.0f}", "por m²: oferta desde la que conviene vender")], W))
    E.append(Spacer(1, 2.5 * mm))
    E.append(Image(rutas["van"], width=W * mm, height=W * mm * 3.9 / 7.4))
    E.append(P("VAN: cuánto más vale hoy la alternativa que invertir el mismo dinero al 10 % anual. Azul = sin "
               "inversión; gris = requiere obra. Escenarios pesimista y optimista: rentas, demanda y costo de obra "
               "bajos o altos.", "caption"))
    E.append(PageBreak())

    # ---------------- 2. Mercado y terreno
    E.append(P("1. Lo que dice el mercado de Mendoza", "h1"))
    E += bullets([
        "<b>Ciudad pequeña:</b> ≈ 5,100 habitantes en 2017 (3,356 en 2007) y ≈ 6,100-6,700 estimados en 2026; la "
        "provincia tiene ≈ 33,000 y creció 1.3 % anual entre 2017 y 2025. El mercado de alquileres es chico e informal: "
        "no hay avisos publicados de locales, cuartos ni lotes.",
        "<b>El jirón es el eje comercial e institucional</b> (agencia del Banco de la Nación en el N.º 309), pero no hay "
        "cajas municipales, Mibanco ni cadenas: el inquilino ancla para la esquina no está garantizado.",
        "<b>El «nuevo hospital» reemplaza al que ya existe:</b> el Hospital María Auxiliadora II-1 se muda a un local "
        "nuevo (96 % de avance hacia ago-2026, apertura probable en 2027). Suma algo de capacidad, pero no es una "
        "demanda nueva, y si el nuevo sitio queda lejos del lote, boticas y consultorios se irán hacia allá.",
        "<b>Turismo débil:</b> el 94 % de los visitantes son de la provincia y el 91 % se aloja con familiares; la "
        "ocupación de hospedajes en Amazonas ronda el 20-23 %.",
        "<b>Valorización a mediano plazo:</b> la carretera Chachapoyas–Mendoza (≈ S/ 369 MM) sigue en estudio; cuando "
        "se asfalte, el centro debería valorizarse.",
        "<b>Rentas estimadas:</b> locales de 40-50 m² en el jirón S/ 12-18 por m² al mes; una esquina de 100 m² sin "
        "contrato ≈ S/ 1,300 (con una cadena o caja firmada, S/ 2,000-3,000). En Chachapoyas, cinco veces más grande, "
        "un local de 127 m² pide S/ 24 por m².",
        "<b>Impuestos y crédito:</b> alquilar como persona natural paga 5 % de lo cobrado, sin IGV, y los intereses de "
        "un depósito están exonerados. Un hipotecario bancario cuesta 7-8 %; las cajas, 13-14 %."])
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
                             "fondo ocupa 261 m²; en el fondo quedan 18 plazas (6 se asignan a los locales según la "
                             "A.070), con un portón de 6.5 m en la calle lateral y la isla central libre para maniobrar. "
                             "La estructura de la esquina se diseña en pórticos de concreto para 3 pisos (zona sísmica 3 "
                             "hasta verificar la E.030).", "caption")]))
    E.append(PageBreak())

    # ---------------- 3. Comparación
    E.append(P("3. Comparación de las 12 alternativas (escenario base, ordenadas por VAN)", "h1"))
    filas = [["Alt.", "Alternativa", "Inversión", "Caja neta al mes", "VAN al 10 %", "TIR", "Contando terreno",
              "Riesgo"]]
    for m in tab:
        op = al.OPC[m["clave"]]
        filas.append([f"<b>{m['clave']}</b>", op.nombre, "—" if m["capex"] == 0 else miles(m["capex"]),
                      S(m["neto_mes"]), miles(m["van"]), "—" if m["tir"] is None else pct(m["tir"]),
                      pct(m["tir_terreno"]), op.riesgo])
    filas.append(["", "<i>Vender el terreno y depositar al 6 %</i>", "—", S(venta["renta_mes"]), "—", "—", pct(dep), "bajo"])
    E.append(tabla(filas, (9, 56, 21, 18, 21, 13, 16, 20), alinear_der=(2, 3, 4, 5, 6)))
    E.append(P("Caja neta al mes: en régimen, a precios de hoy, después de gastos, personal, impuestos y reposiciones "
               "prorrateadas. VAN y TIR a 20 años con 3 % de crecimiento anual y valor residual de lo construido. "
               "«Contando terreno»: rentabilidad anual del propietario si el lote se valora a S/ "
               f"{al.VALOR_M2[ESC]:,.0f} por m² y se valoriza {pl * 100:.1f} % al año.", "small"))
    E.append(Spacer(1, 3 * mm))
    E.append(Image(rutas["tir_t"], width=W * mm, height=W * mm * 3.6 / 7.4))
    E.append(P("Barras azules oscuras: alternativas sin inversión. Por debajo de la línea naranja conviene más vender el "
               "terreno y depositar el dinero; por debajo de la punteada, ni siquiera supera dejar el lote sin uso.",
               "caption"))
    E.append(PageBreak())

    # ---------------- 4. Qué hacer según lo que encuentre
    E.append(P("4. Qué hacer según lo que encuentre", "h1"))
    E.append(P("La decisión depende de datos que solo se obtienen en Mendoza. Esta tabla convierte cada hallazgo en una "
               "acción; los umbrales salen del modelo (inversión que paga el 10 % anual)."))
    E.append(tabla([
        ["Si encuentra…", "Entonces…", "Resultado esperado"],
        [f"Alguien que arriende el lote completo por ≥ S/ 600 al mes, contrato de 3 años o más con reajuste y garantía",
         "Arriéndelo (J). Pacte salida anticipada con aviso si quiere construir después.",
         f"≈ {S(J['neto_mes'])} netos al mes sin invertir; VAN {miles(J['van'])}"],
        ["Una cadena, caja, cooperativa o comercio que quiera la esquina y construya su local",
         "Cédala en derecho de superficie o build-to-suit a 10-20 años (L). El fondo queda para arrendar o para cochera.",
         f"≈ {S(L['neto_mes'])} netos al mes; al final la edificación queda para usted"],
        [f"Un inquilino que firme la esquina por ≥ {S(u['esquina_contrato'])} al mes a 5 años o más",
         f"Construya solo la esquina ({miles(cap_esq)}), con estructura para 3 pisos.",
         "Paga el 10 % anual; sin contrato haría falta ≈ " + S(u["esquina_mercado"]) + " al mes"],
        [f"2 de los 3 locales del jirón comprometidos a ≥ S/ {u['locales_m2_contrato']:.0f} por m² "
         f"(≈ {S(u['locales_m2_contrato'] * 45)} por 45 m²)",
         f"Construya los 3 locales ({miles(cap_loc)}).",
         f"Paga el 10 % anual; sin contratos haría falta S/ {u['locales_m2']:.0f} por m²"],
        [f"≥ {abon:.0f} abonados que paguen S/ 75 al mes con 3 meses por adelantado",
         f"Habilite la cochera del fondo ({miles(cap_coch)}), sin personal, con portón automático y cámaras.",
         "Paga el 10 % anual; con menos abonados pierde dinero"],
        [f"Una oferta de compra de más de ≈ S/ {t_venta:,.0f} por m² (≈ {miles(t_venta * al.AREA_LOTE)}) y no necesita "
         "el lote", "Vender y depositar rinde más que arrendar.", f"≈ {pct(dep)} al año sin trabajo ni riesgo de inquilino"],
        ["Nada de lo anterior",
         "No construya. Ingresos puente sin inversión (panel publicitario S/ 300-800 al mes, ferias, alquiler mensual a "
         "contratistas) y vuelva a ofrecer el lote cada 6 meses.",
         f"El lote se valoriza ≈ {pl * 100:.1f} % al año"],
    ], (62, 66, 46)))
    E.append(Spacer(1, 3 * mm))
    E.append(Image(rutas["sens"], width=W * mm, height=W * mm * 2.9 / 7.4))
    E.append(P("Umbrales del modelo: ingreso a partir del cual cada inversión paga el 10 % anual", "h2"))
    E.append(tabla([
        ["Módulo", "Umbral", "Estimado hoy", "Inversión"],
        ["Esquina de 100 m² (contrato firmado, 95 % del tiempo ocupada)", f"≥ {S(u['esquina_contrato'])} al mes",
         "S/ 1,000-2,000 sin contrato", miles(cap_esq)],
        ["3 locales del jirón (con contratos / sin contratos)",
         f"≥ S/ {u['locales_m2_contrato']:.1f} / S/ {u['locales_m2']:.1f} por m²", "S/ 12-18 por m²", miles(cap_loc)],
        ["Cochera de 12 abonados", f"≥ {abon:.0f} abonados pagando S/ 75", "5-13 abonados", miles(cap_coch)],
        ["Piso de consultorios (con ascensor, Modalidad D)", f"≥ {S(u['consultorio'])} por consultorio", "S/ 300-500",
         miles(al.OPC['E'].fases[3].capex())],
        ["2 pisos de minidepartamentos", f"≥ {S(u['minidepto'])} por minidepartamento", "S/ 400-600",
         miles(al.OPC['D'].fases[3].capex())],
        ["Cancha techada", f"≥ {u['cancha_horas']:.1f} horas vendidas al día a S/ 50", "2-3.5 horas",
         miles(al.OPC['F'].fases[0].capex())],
        ["Estacionamiento techado (con guardián)", f"≥ {u['abonados_A']:.0f} abonados a S/ 120 + rotación", "8-18 abonados",
         miles(al.OPC['A'].fases[0].capex())],
    ], (66, 46, 34, 28)))
    E.append(PageBreak())

    # ---------------- 5. Estrategia y financiamiento
    E.append(P("5. Estrategia por etapas", "h1"))
    E.append(tabla([
        ["Etapa", "Cuándo", "Qué hacer", "Dinero"],
        ["0. Validar y ofrecer", "Meses 0-3",
         "Sondeo de alquileres en el jirón (8-10 locales); certificado de parámetros (usos, altura, retiros, "
         "estacionamientos exigidos); tasación; ofrecer el lote y la esquina a ferreterías, concesionarios de motos, "
         "empresas de transporte, farmacias, cajas y cooperativas cafetaleras. Sin obra.", "S/ 3-5 mil"],
        ["1. Rentabilizar sin capital", "Desde que aparezca",
         "Arriendo del lote (J) o derecho de superficie en la esquina (L); mientras tanto, ingresos puente.", "S/ 0"],
        ["2. Módulos con contrato", "Al firmar",
         f"Esquina ({miles(cap_esq)}) con contrato ≥ {S(u['esquina_contrato'])}; cochera ({miles(cap_coch)}) con "
         f"≥ {abon:.0f} abonados; 3 locales ({miles(cap_loc)}) con compromisos ≥ S/ {u['locales_m2_contrato']:.0f} por m².",
         "por módulo"],
        ["3. Crecer en altura", "Años 3-5 o más",
         f"Solo si la renta de pisos altos llega a los umbrales (consultorios ≥ {S(u['consultorio'])}, minidepartamentos "
         f"≥ {S(u['minidepto'])}) o si la familia necesita vivienda propia sobre la esquina.", "por decidir"],
    ], (32, 24, 98, 20)))
    E.append(P("Cómo financiar un módulo", "h2"))
    prest = 0.6 * cap_esq
    E += bullets([
        f"Endeudarse solo con el contrato del inquilino firmado y a tasa bancaria (≤ 8 %), con 12 meses de gracia. "
        f"Ejemplo: 60 % de la esquina ({miles(prest)}) a 10 años al 8 % = {S(_cuota(prest, 0.08, 10))} al mes, que debe "
        f"cubrir el contrato ({S(u['esquina_contrato'])}).",
        "Nunca con caja municipal al 13-14 % ni crédito de microempresa (47-59 %): la obra rinde menos que el interés.",
        "Si el propietario o un familiar es trabajador público con cuenta sueldo en el Banco de la Nación, una casa-tienda "
        "(vivienda propia sobre la esquina) puede financiarse con su crédito hipotecario o de mejora de vivienda "
        "(5.5-7.25 % TEA, verificar condiciones vigentes)."])
    E.append(P("Formas de usar el terreno sin poner capital", "h2"))
    E += bullets([
        "<b>Arriendo del lote completo</b> a un operador que hace sus propias mejoras (J).",
        "<b>Derecho de superficie o build-to-suit:</b> el inquilino construye en la esquina y paga renta por el suelo; "
        "al vencer el plazo la edificación pasa al propietario (L).",
        "<b>Asociación en participación con un constructor</b> (Ley General de Sociedades, art. 438): el propietario "
        "aporta el terreno y recibe 25-35 % de las unidades. En Mendoza hay pocos compradores de departamentos y pocos "
        "promotores: exigir carta fianza o fideicomiso.",
        "<b>Negocio propio en la esquina:</b> conviene solo si el negocio deja más que la renta que se dejaría de cobrar "
        "(≈ S/ 1,300 al mes)."])
    E.append(Spacer(1, 2 * mm))
    E.append(Image(rutas["acum"], width=W * mm, height=W * mm * 3.0 / 7.4))
    E.append(PageBreak())

    # ---------------- 6. Fichas
    E.append(P("6. Supuestos de cada alternativa (escenario base)", "h1"))
    det = {
        "J": ("S/ 1,000 al mes por el lote completo, 75 % del tiempo arrendado.", "Predial; 5 % de impuesto al alquiler."),
        "L": ("S/ 800 al mes por el suelo de la esquina, 95 % del tiempo.", "Predial; 5 %."),
        "C1": ("Esquina a S/ 1,300 al mes (80 % ocupada, sin contrato). Cochera: 12 abonados posibles a S/ 75, 70 % pagando.",
               "Mantenimiento, predial y seguro; 5 % al alquiler; cochera sin personal; reposición de equipos en el año 10."),
        "C": ("C1 + 3 locales a S/ 15 por m² (80 % ocupados).", "Igual que C1; 6 plazas de la cochera quedan para los locales."),
        "E": ("C + 7 consultorios a S/ 400 desde el año 3 (70 % ocupados).", "Ascensor, Modalidad D y mantenimiento ≈ S/ 11.6 mil al año; 5 %."),
        "D": ("C + 8 minidepartamentos a S/ 500 desde el año 4 (85 % ocupados).", "≈ S/ 15.6 mil al año; 5 %."),
        "A": ("12 abonados a S/ 120, 9 autos al día a S/ 4.50 y 5 motos a S/ 40.",
              "Guardián, energía, mantenimiento 1 %, predial, seguro y Nuevo RUS ≈ S/ 27 mil al año."),
        "B": ("10 abonados a S/ 85, 7 autos al día a S/ 3.50 y 4 motos a S/ 35.",
              "Guardián ≈ S/ 15.3 mil y otros ≈ S/ 7 mil al año; reafirmado y reposiciones."),
        "F": ("2.5 horas vendidas al día a S/ 50.", "Encargado, energía, mantenimiento; cambio de grass en los años 9 y 18."),
        "G": ("2.5 eventos al mes a S/ 1,200.", "20 % del ingreso en personal por evento; ≈ S/ 22 mil fijos; 10 % de impuestos."),
        "K": ("4 boleterías a S/ 600 y 20 salidas al día a S/ 4.", "Encargado, limpieza, energía, mantenimiento; 3 % de impuestos."),
        "H": ("16 habitaciones a S/ 75 por noche, 35 % de ocupación.", "3 trabajadores, 25 % variable, ≈ S/ 94 mil fijos; 15 % de impuestos."),
    }
    filas = [["Alt.", "Qué es", "Ingresos supuestos", "Gastos e impuestos", "Notas"]]
    for k in al.ORDEN:
        op = al.OPC[k]
        ing, gas = det[k]
        filas.append([f"<b>{k}</b>", f"<b>{op.nombre}.</b> {op.resumen}", ing, gas, " ".join(op.notas)])
    E.append(tabla(filas, (9, 50, 36, 36, 43)))
    E.append(PageBreak())

    # ---------------- 7. Validación y fuentes
    E.append(P("7. Qué validar antes de decidir", "h1"))
    E += bullets([f"<b>{q}.</b> {como}" for q, como in al.VALIDAR])
    E.append(P("Supuestos y limitaciones", "h2"))
    E += bullets([
        "Montos en soles de octubre de 2026 con IGV; tasa de descuento 10 % anual; crecimiento de rentas, gastos y "
        "costos de obra 3 %; horizonte 20 años; valor residual lineal de lo construido.",
        f"Escenarios: pesimista con rentas y demanda bajas, 15 % de sobrecosto de obra, terreno a S/ {al.VALOR_M2[0]:,.0f} "
        f"por m² y 3 % de valorización; optimista con rentas altas, 8 % de ahorro, S/ {al.VALOR_M2[2]:,.0f} por m² y 6 %.",
        "Las rentas de Mendoza son estimaciones por comparables con confianza baja y fueron ajustadas a la baja en una "
        "revisión independiente; el Excel permite cambiarlas y recalcula todo.",
        "Los costos de obra son estimaciones por m² (S/ 1,500 para un 1.er piso en pórticos diseñado para 3 pisos); deben "
        "reemplazarse por cotizaciones locales y por el diseño estructural con estudio de suelos.",
        "La probabilidad de encontrar un arrendatario o un inquilino ancla no está modelada: por eso la recomendación "
        "es una regla de decisión y no una sola alternativa."])
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
