"""
Memoria descriptiva + análisis de rentabilidad (PDF A4) del estacionamiento.
"""
from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

import estructura as est
import geometria as g
import rentabilidad as rt

FONT_DIR = "/usr/share/fonts/truetype/liberation"
pdfmetrics.registerFont(TTFont("Lib", os.path.join(FONT_DIR, "LiberationSans-Regular.ttf")))
pdfmetrics.registerFont(TTFont("Lib-B", os.path.join(FONT_DIR, "LiberationSans-Bold.ttf")))
pdfmetrics.registerFont(TTFont("Lib-I", os.path.join(FONT_DIR, "LiberationSans-Italic.ttf")))
from reportlab.pdfbase.pdfmetrics import registerFontFamily

registerFontFamily("Lib", normal="Lib", bold="Lib-B", italic="Lib-I", boldItalic="Lib-B")

AZUL = colors.HexColor("#1f4e79")
GRIS = colors.HexColor("#52514e")
FONDO = colors.HexColor("#eef3f8")
S1, S2, S3 = "#2a78d6", "#eb6834", "#1baf7a"     # paleta categórica validada (3 primeras posiciones)
TINTA, TINTA2, REJILLA = "#0b0b0b", "#52514e", "#e4e3df"

ss = getSampleStyleSheet()
st = {
    "h1": ParagraphStyle("h1", fontName="Lib-B", fontSize=15, leading=19, textColor=AZUL, spaceBefore=10,
                         spaceAfter=6),
    "h2": ParagraphStyle("h2", fontName="Lib-B", fontSize=11.5, leading=15, textColor=AZUL, spaceBefore=8,
                         spaceAfter=4),
    "p": ParagraphStyle("p", fontName="Lib", fontSize=9.5, leading=13.2, spaceAfter=5),
    "li": ParagraphStyle("li", fontName="Lib", fontSize=9.5, leading=13, leftIndent=12, bulletIndent=2,
                         spaceAfter=2.5),
    "small": ParagraphStyle("small", fontName="Lib", fontSize=8, leading=10.5, textColor=GRIS),
    "cell": ParagraphStyle("cell", fontName="Lib", fontSize=8.3, leading=10.4),
    "cellb": ParagraphStyle("cellb", fontName="Lib-B", fontSize=8.3, leading=10.4),
    "title": ParagraphStyle("title", fontName="Lib-B", fontSize=24, leading=29, textColor=AZUL, alignment=TA_CENTER),
    "subtitle": ParagraphStyle("subtitle", fontName="Lib", fontSize=12.5, leading=17, alignment=TA_CENTER,
                               textColor=GRIS),
    "kpi_v": ParagraphStyle("kpi_v", fontName="Lib-B", fontSize=17, leading=20, alignment=TA_CENTER, textColor=AZUL),
    "kpi_l": ParagraphStyle("kpi_l", fontName="Lib", fontSize=8.2, leading=10, alignment=TA_CENTER, textColor=GRIS),
    "caption": ParagraphStyle("caption", fontName="Lib-I", fontSize=8, leading=10, textColor=GRIS,
                              alignment=TA_CENTER, spaceAfter=6),
}


def S(x, d=0):
    return f"S/ {x:,.{d}f}"


def P(t, s="p"):
    return Paragraph(t, st[s])


def bullets(items):
    return [Paragraph(t, st["li"], bulletText="•") for t in items]


def tabla(data, anchos, cabecera=True, negrita_ultima=False, alinear_der=()):
    filas = []
    for i, f in enumerate(data):
        estilo = "cellb" if (cabecera and i == 0) or (negrita_ultima and i == len(data) - 1) else "cell"
        filas.append([c if not isinstance(c, str) else Paragraph(c, st[estilo]) for c in f])
    t = Table(filas, colWidths=[a * mm for a in anchos], repeatRows=1 if cabecera else 0)
    sty = [("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#b5b5b5")),
           ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
           ("TOPPADDING", (0, 0), (-1, -1), 2.2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.2)]
    if cabecera:
        sty.append(("BACKGROUND", (0, 0), (-1, 0), FONDO))
    if negrita_ultima:
        sty.append(("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f4f4f4")))
    t.setStyle(TableStyle(sty))
    return t


# --------------------------------------------------------------------------
# Gráficos
# --------------------------------------------------------------------------
def _estilo_ejes(ax):
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.spines["bottom"].set_color("#9a9994")
    ax.tick_params(colors=TINTA2, labelsize=8.5, length=0)
    ax.grid(axis="y", color=REJILLA, lw=0.8)
    ax.set_axisbelow(True)


def grafico_capex(ruta):
    grupos, tot = rt.capex_por_grupo()
    items = sorted(grupos.items(), key=lambda kv: kv[1])
    fig, ax = plt.subplots(figsize=(7.2, 3.6), dpi=200)
    ys = np.arange(len(items))
    vals = [v / 1000 for _, v in items]
    ax.barh(ys, vals, height=0.62, color=S1, edgecolor="white", linewidth=2)
    ax.set_yticks(ys, [k for k, _ in items], fontsize=8.5, color=TINTA)
    for y, v in zip(ys, vals):
        ax.text(v + max(vals) * 0.01, y, f"S/ {v:,.1f} mil", va="center", fontsize=8, color=TINTA2)
    ax.set_xlim(0, max(vals) * 1.22)
    ax.set_xlabel("miles de soles", fontsize=8.5, color=TINTA2)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.spines["bottom"].set_color("#9a9994")
    ax.tick_params(axis="x", colors=TINTA2, labelsize=8.5)
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", color=REJILLA, lw=0.8)
    ax.set_axisbelow(True)
    ax.set_title(f"Inversión por rubro (total {S(tot)})", fontsize=10, color=TINTA, loc="left", weight="bold")
    fig.tight_layout()
    fig.savefig(ruta)
    plt.close(fig)


def grafico_flujos(ruta):
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.5), dpi=200, sharey=True)
    titulos = ("Con guardián contratado", "Operado por el propietario")
    colores = (S1, S2, S3)
    for ax, cp, tit in zip(axes, (True, False), titulos):
        res = rt.evaluar("afirmado", cp)
        for r, c in zip(res, colores):
            anios = [f["anio"] for f in r["flujo"]]
            acum = [f["acum"] / 1000 for f in r["flujo"]]
            ax.plot(anios, acum, color=c, lw=2, label=r["escenario"].nombre)
            ax.text(anios[-1] + 0.3, acum[-1], r["escenario"].nombre, color=TINTA2, fontsize=7.5, va="center")
        ax.axhline(0, color="#6f6e69", lw=1)
        ax.set_title(tit, fontsize=9.5, color=TINTA, loc="left")
        ax.set_xlabel("año de operación", fontsize=8.5, color=TINTA2)
        ax.set_xlim(0, rt.HORIZONTE + 4.5)
        ax.set_xticks(range(0, rt.HORIZONTE + 1, 5))
        _estilo_ejes(ax)
    axes[0].set_ylabel("flujo acumulado (miles de S/)", fontsize=8.5, color=TINTA2)
    axes[1].legend(loc="upper left", fontsize=7.5, frameon=False)
    fig.suptitle("Flujo de caja acumulado a 20 años (inversión S/ %.0f mil, piso de afirmado)" % (rt.capex()[-1] / 1000),
                 fontsize=10, x=0.02, ha="left", weight="bold", color=TINTA)
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
    canvas.drawString(18 * mm, 10 * mm, "Estacionamiento techado - Jr. Rodríguez de Mendoza, Mendoza (Amazonas) - Anteproyecto")
    canvas.drawRightString(192 * mm, 10 * mm, f"Pág. {doc.page}")
    canvas.restoreState()


def generar(ruta_pdf, png_dir, graf_dir):
    os.makedirs(graf_dir, exist_ok=True)
    g_capex = os.path.join(graf_dir, "capex.png")
    g_flujo = os.path.join(graf_dir, "flujos.png")
    grafico_capex(g_capex)
    grafico_flujos(g_flujo)

    R = g.resumen()
    ps, sub, gg, imp, total = rt.capex("afirmado")
    total_losa = rt.capex("losa")[-1]
    capex_st = rt.capex_sin_techo()
    costo_techo = total - capex_st
    res_g = rt.evaluar("afirmado", True)
    res_p = rt.evaluar("afirmado", False)
    base_g, base_p = res_g[1], res_p[1]
    eq_g = rt.punto_equilibrio(total, True)
    eq_p = rt.punto_equilibrio(total, False)
    fl_st_p = rt.flujo(rt.ESCENARIO_SIN_TECHO, capex_st, False)
    tir_st_p = rt.tir([f["neto"] for f in fl_st_p])
    pb_st_p = rt.recuperacion(fl_st_p)
    opex = rt.opex_anual(total, True)

    doc = SimpleDocTemplate(ruta_pdf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm,
                            bottomMargin=16 * mm, title="Estacionamiento techado Rodríguez de Mendoza",
                            author="Anteproyecto")
    W = 174
    E = []

    # ---------------- Portada
    E += [Spacer(1, 18 * mm), P("ESTACIONAMIENTO VEHICULAR TECHADO", "title"), Spacer(1, 3 * mm),
          P("Memoria descriptiva, estructura metálica ligera y análisis de rentabilidad", "subtitle"),
          P("Jr. Rodríguez de Mendoza esquina calle lateral - Mendoza (San Nicolás), Rodríguez de Mendoza, Amazonas",
            "subtitle"),
          P("Anteproyecto - octubre 2026", "subtitle"), Spacer(1, 8 * mm)]
    kpis = [
        (f"{R['area_lote']:,.0f} m²", "terreno"),
        (f"{R['plazas_total']}", "plazas techadas<br/>(2 accesibles)"),
        (f"{R['motos'] + R['mototaxis']}", "motos y mototaxis"),
        (f"{len(g.COLUMNAS)}", "columnas<br/>(1 cada 3 plazas)"),
        (f"S/ {total / 1000:,.0f} mil", "inversión estimada"),
    ]
    t = Table([[P(v, "kpi_v") for v, _ in kpis], [P(l, "kpi_l") for _, l in kpis]], colWidths=[W / 5 * mm] * 5)
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), FONDO), ("BOX", (0, 0), (-1, -1), 0.6, AZUL),
                           ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    E += [t, Spacer(1, 6 * mm)]
    E.append(Image(os.path.join(png_dir, "A-01.png"), width=W * mm, height=W * mm * 297 / 420))
    E.append(P("Lámina A-01: distribución general, circulación de sentido único y plazas techadas.", "caption"))
    E.append(PageBreak())

    # ---------------- 1. Resumen ejecutivo
    E.append(P("1. Resumen ejecutivo", "h1"))
    E.append(P(
        f"El terreno (≈ {R['area_lote']:,.0f} m², esquina de Jr. Rodríguez de Mendoza con una calle lateral) admite "
        f"<b>{R['plazas_total']} plazas para autos, todas techadas</b> ({R['plazas_estandar']} estándar de 2.50 × 5.00 m y "
        f"{R['plazas_accesibles']} accesibles de 3.80 × 5.00 m), más {R['motos']} motos y {R['mototaxis']} mototaxis. "
        "Los dos portones de 3.00 m que indicaste se usan como <b>ingreso (calle lateral)</b> y <b>salida "
        "(Jr. Rodríguez de Mendoza)</b>, con una circulación en L de sentido único y pasillos de 6.50 m."))
    E.append(P(
        f"La estructura es un <b>voladizo metálico ligero</b>: una sola línea de columnas detrás de las plazas, "
        f"a 1.00 m del fondo, <b>una columna cada 3 plazas</b> ({len(g.COLUMNAS)} columnas en total), vigas "
        f"reticuladas en voladizo de {est.BRAZO_FRONTAL:.2f} m y correas de 7.50 m. No hay ninguna columna en los "
        f"pasillos ni entre autos. Peso estimado {est.ACERO_TOTAL_KG / 1000:,.1f} t de acero "
        f"({est.ACERO_TOTAL_KG / est.AREA_TECHADA:.1f} kg/m² de techo)."))
    E.append(P(
        f"La inversión estimada es <b>{S(total)}</b> con piso de afirmado ({S(total_losa)} con losa de concreto). "
        f"Solo los techos cuestan ≈ {S(costo_techo)} (≈ {S(costo_techo / R['plazas_total'])} por plaza). "
        "La rentabilidad depende sobre todo de cuántos autos se abonen y de quién opere la cochera:"))
    data = [["Escenario", "Ingreso mensual", "Con guardián: TIR / recuperación", "Operado por el propietario: TIR / recuperación"]]
    for a, b in zip(res_g, res_p):
        def fmt(r):
            tirs = f"{100 * r['tir']:.1f} %" if r["tir"] is not None and r["tir"] >= 0 else "negativa"
            pb = f"{r['payback']:.1f} años" if r["payback"] else "no recupera"
            return f"{tirs} / {pb}"
        data.append([a["escenario"].nombre, S(a["ingreso_mes"]), fmt(a), fmt(b)])
    E.append(tabla(data, [28, 30, 56, 60]))
    E.append(Spacer(1, 2 * mm))
    E.append(P(
        f"<b>Conclusión:</b> el proyecto completo es rentable si se alcanzan unos <b>{eq_p[1]:.0f} autos abonados</b> a "
        f"S/ 120/mes operándolo tú o tu familia (≈ {eq_g[1]:.0f} si se contrata un guardián), además de la rotación "
        "diaria. Con demanda menor conviene <b>construir por etapas</b>: primero cerco, portones, afirmado, garita e "
        "iluminación, y techar fila por fila a medida que se llenan los abonos (ver sección 8)."))
    E.append(P(
        "Funciona para <b>autos, station wagon, SUV, camionetas pick-up 4×4 y minivans/combis tipo Hiace</b> "
        "(gálibo libre 2.80 m). No es apto para camiones, buses ni combis largas tipo Sprinter."))

    # ---------------- 2. Terreno
    E.append(P("2. El terreno", "h1"))
    E.append(P(
        "Se reconstruyó a partir de tus 4 capturas de Google Maps: frente a Jr. Rodríguez de Mendoza 30 m, lado "
        "colindante con edificaciones 40 m, fondo 30 m y frente a la calle lateral 20 m. El ángulo en la esquina de "
        "calles (≈ 130°) se midió sobre la imagen satelital; con él los demás ángulos resultan ≈ 60°, 80° y 90°, que "
        "coinciden con lo que se ve en las fotos."))
    data = [["Vértice", "Lado", "Longitud", "Ángulo interior"]]
    for k, sig in zip("ABCD", "BCDA"):
        data.append([k, f"{k}-{sig}", f"{np.linalg.norm(g.VERT[sig] - g.VERT[k]):.2f} m", f"{g.ANGULOS[k]:.1f}°"])
    E.append(tabla(data, [25, 25, 30, 35]))
    E.append(Spacer(1, 2 * mm))
    E.append(P(
        f"Área ≈ <b>{R['area_lote']:,.2f} m²</b>, perímetro 120 m. Para confirmar la forma antes de construir, mide "
        f"en campo las diagonales: <b>A-C ≈ {R['diagonal_AC']:.2f} m</b> (esquina de calles a esquina posterior) y "
        f"<b>B-D ≈ {R['diagonal_BD']:.2f} m</b>. Si difieren en más de 0.50 m hay que ajustar la distribución. Las "
        "medidas de Google Maps tienen un error típico de ±0.5 a ±1 m; el expediente municipal exige levantamiento "
        "topográfico."))

    # ---------------- 3. Distribución
    E.append(P("3. Propuesta de distribución", "h1"))
    E += bullets([
        "<b>Circulación en L de sentido único:</b> se entra por P-1 (calle lateral), se recorre el pasillo paralelo "
        "al fondo, se gira en la esquina posterior y se sale por P-2 hacia Jr. Rodríguez de Mendoza. Así la cola de "
        "ingreso queda en la calle de menor tránsito y la salida no cruza a los que entran.",
        "<b>Cuatro filas de plazas a 90°</b>: fila A (11) junto al fondo, fila B (8, con las 2 accesibles) junto a "
        "las edificaciones vecinas, y en la isla central la fila C (6) y la fila D (3).",
        "<b>Pasillos de 6.50 m</b> entre plazas opuestas (el RNE A.010 pide 6.00 a 6.50 m según la versión; se usó el "
        "mayor para que las camionetas maniobren cómodas).",
        "<b>Plazas accesibles</b> (RNE A.120: 2 para 21-50 plazas de uso público) junto a la puerta peatonal PP-1 y "
        "la salida.",
        "<b>Garita de control</b> en la esquina B, al lado de la salida (el cobro y la vigilancia se hacen donde sale "
        "el auto). <b>SS.HH. accesible y depósito</b> en la zona interior, con puerta peatonal PP-2 a la esquina.",
        f"<b>Motos y mototaxis</b> en la zona interior de la isla, con un paso de 2.00 m protegido con bolardos "
        "para que no entren autos.",
        "Señalización: flechas, numeración, PARE y espejo convexo en la salida, velocidad máxima 10 km/h, "
        "topellantas a 1.10 m del fondo de cada plaza.",
    ])
    data = [["Concepto", "Cantidad / área"],
            ["Plazas autos estándar (2.50 × 5.00 m)", f"{R['plazas_estandar']}"],
            ["Plazas accesibles (3.80 × 5.00 m)", f"{R['plazas_accesibles']}"],
            ["Motos / mototaxis", f"{R['motos']} / {R['mototaxis']}"],
            ["Área techada", f"{R['area_techada']:.1f} m²"],
            ["Circulación vehicular", f"{R['area_circulacion']:.1f} m²"],
            ["Área por plaza (terreno / plazas)", f"{R['area_lote'] / R['plazas_total']:.1f} m²"]]
    E.append(tabla(data, [90, 40]))

    # ---------------- 4. Vehículos
    E.append(P("4. ¿Para qué tipo de vehículos debe funcionar?", "h1"))
    E.append(P(
        "En Mendoza predominan los autos colectivos (Toyota Corolla/Yaris, Hyundai Accent), las camionetas 4×4 "
        "de productores de café y ganaderos, minivans interprovinciales y una gran cantidad de mototaxis. El diseño "
        "toma como <b>vehículo de diseño la camioneta pick-up</b> (5.30 × 1.85 × 1.82 m), la más exigente de las "
        "habituales:"))
    data = [["Vehículo", "Medidas aprox. (L × A × H)", "¿Funciona?", "Comentario"],
            ["Auto sedán / hatchback / station wagon", "4.3-4.7 × 1.7 × 1.5 m", "Sí", "Ideal: maniobra holgada"],
            ["SUV / camioneta cerrada", "4.6-4.9 × 1.85 × 1.75 m", "Sí", "Ideal"],
            ["Pick-up doble cabina 4×4 (Hilux, Frontier)", "5.30 × 1.85 × 1.82 m", "Sí",
             "Vehículo de diseño; sobresale ≈ 0.30 m al pasillo"],
            ["Minivan / combi tipo Hiace (techo alto)", "5.3 × 1.9 × 2.3-2.5 m", "Sí", "Gálibo libre 2.80 m"],
            ["Motos y mototaxis", "2.0-3.0 × 0.8-1.4 m", "Sí (zona propia)", "5 motos + 2 mototaxis; ampliable"],
            ["Combi larga tipo Sprinter / coaster", "6-7 × 2.0 × 2.7-2.9 m", "No", "Excede largo de plaza y gálibo"],
            ["Camión, volquete, bus", "> 7 m", "No", "Portones de 3 m y giros no lo permiten"]]
    E.append(tabla(data, [52, 40, 24, 58]))
    E.append(Spacer(1, 2 * mm))
    E.append(P(
        "Los portones de 3.00 m son suficientes para menos de 40 vehículos (RNE A.010), pero para camionetas que "
        "giran 90° desde una calle angosta se recomienda <b>ochavar o abocinar 1.00 m los costados de cada portón</b> "
        "o ampliarlos a 3.50 m si la municipalidad lo permite."))

    # ---------------- 5. Estructura
    E.append(P("5. Estructura metálica ligera con mínimas columnas", "h1"))
    E.append(P(
        "Se descartó un techo apoyado en columnas al frente de las plazas (estorban la apertura de puertas y las "
        "maniobras) y también el voladizo puro desde el cerco (necesita columnas y zapatas mucho más grandes y la "
        "zapata invadiría el terreno vecino). La solución es una <b>“T” desbalanceada</b>: la columna está a 1.00 m "
        f"del fondo de la plaza, sobre la línea divisoria; el brazo posterior de {est.BRAZO_POSTERIOR:.2f} m equilibra "
        f"parcialmente al brazo frontal de {est.BRAZO_FRONTAL:.2f} m y reduce ≈ 36 % el momento en la base respecto de "
        "un voladizo desde el cerco."))
    E.append(Image(os.path.join(png_dir, "E-03.png"), width=W * mm, height=W * mm * 297 / 420))
    E.append(P("Lámina E-03: pórtico típico en voladizo, placa base y verificaciones.", "caption"))
    filas = [["Elemento", "Perfil propuesto", "Cantidad"],
             ["Columna", est.COLUMNA.nombre + " (ASTM A500)", f"{len(g.COLUMNAS)} und"],
             ["Viga en voladizo VV-1 (reticulada, peralte 0.54 → 0.17 m)",
              f"Cordones {est.CORDON.nombre}; diagonales {est.DIAGONAL.nombre}", f"{len(g.COLUMNAS)} und"],
             ["Correas (luz 7.50 m, @ 1.10 m)", est.CORREA.nombre + " galvanizada", f"{est.N_CORREAS} líneas por techo"],
             ["Cobertura", "TR-4 aluzinc prepintada e = 0.40 mm, pendiente 10 %", f"{est.AREA_TECHADA:.0f} m²"],
             ["Placa base / anclaje", f"PL {est.PLACA['placa']:.0f}×{est.PLACA['placa_l']:.0f}×25 mm + 4 pernos ø 1\"",
              f"{len(g.COLUMNAS)} und"],
             ["Zapata Z-1", f"{est.ZAP_L:.2f} × {est.ZAP_B:.2f} × {est.H_ZAPATA:.2f} m, Df = {est.DF_ZAPATA:.2f} m",
              f"{len(g.COLUMNAS)} und"],
             ["Acero total", f"{est.ACERO_TOTAL_KG:,.0f} kg ({est.ACERO_TOTAL_KG / est.AREA_TECHADA:.1f} kg/m²)", ""]]
    E.append(tabla(filas, [58, 86, 30]))
    E.append(Spacer(1, 2 * mm))
    v_, c_ = est.VIGA, est.COLUMNA_SEL
    E.append(P(
        f"<b>Predimensionamiento</b> (RNE E.020, E.030, E.090, E.060; LRFD): carga muerta {est.D_KPA:.2f} kPa, carga "
        f"viva de techo {est.LR_KPA:.2f} kPa, viento {est.V_VIENTO:.0f} km/h (succión {est.W_KPA:.2f} kPa). Momento en "
        f"la raíz del voladizo {v_['mu_raiz']:.0f} kN·m; columna con interacción {c_['inter']:.2f}; flecha de la punta "
        f"{c_['flecha_total']:.0f} mm (límite {c_['flecha_lim']:.0f} mm); zapata con presión máxima "
        f"{est.ZAPATA['qmax'] / 98.07:.2f} kg/cm² y factor de seguridad al volteo {est.ZAPATA['fs_volteo']:.1f}. La "
        "columna se eligió por rigidez (limitar la flecha), no por resistencia. Por su peso propio tan bajo, en "
        "cubiertas livianas gobierna la gravedad/viento y no el sismo."))
    E.append(P(
        "<b>Importante:</b> estos cálculos sirven para anteproyecto y presupuesto. La licencia de edificación requiere "
        "el expediente firmado por un ingeniero civil colegiado y un estudio de mecánica de suelos (la zapata asume "
        "q<sub>adm</sub> ≥ 1.0 kg/cm²).", "small"))

    # ---------------- 6. Presupuesto
    grupos, _ = rt.capex_por_grupo()
    E.append(PageBreak())
    E.append(P("6. Presupuesto referencial de inversión", "h1"))
    E.append(Image(g_capex, width=W * mm, height=W * mm * 3.6 / 7.2))
    data = [["Partida", "Cant.", "P. unit.", "Parcial"]]
    for p in ps:
        data.append([p.descripcion, f"{p.cantidad:,.1f} {p.unidad}" if p.cantidad != int(p.cantidad) else f"{int(p.cantidad)} {p.unidad}",
                     S(p.precio, 2 if p.precio < 100 else 0), S(p.parcial)])
    data += [["Subtotal", "", "", S(sub)],
             [f"Gastos generales y dirección técnica ({rt.GASTOS_GENERALES:.0%})", "", "", S(gg)],
             [f"Imprevistos ({rt.IMPREVISTOS:.0%})", "", "", S(imp)],
             ["TOTAL (piso de afirmado)", "", "", S(total)]]
    E.append(tabla(data, [104, 24, 22, 24], negrita_ultima=True))
    E.append(Spacer(1, 2 * mm))
    E.append(P(
        f"Con losa de concreto en lugar de afirmado el total sube a <b>{S(total_losa)}</b>. Precios referenciales "
        "con IGV para Mendoza a octubre de 2026 (incluyen flete desde Chiclayo/Chachapoyas); pide al menos 3 "
        "cotizaciones locales, en especial de la estructura metálica, que es el rubro mayor.", "small"))

    # ---------------- 7. Rentabilidad
    E.append(P("7. Análisis de rentabilidad", "h1"))
    E.append(P(
        "El modelo de negocio típico de una cochera en una ciudad como Mendoza combina <b>abonos mensuales "
        "nocturnos</b> (vecinos sin cochera, colectivos y camionetas que duermen en la ciudad) con <b>rotación "
        "diurna</b> por horas (usuarios del mercado, bancos, municipalidad, hospital) en las plazas que los abonados "
        "dejan libres de día. Supuestos de demanda en operación estable:"))
    data = [["Supuesto", "Pesimista", "Base", "Optimista"]]
    campos = [("Autos abonados (mensual)", "abonados", "{:.0f}"), ("Tarifa mensual por auto", "tarifa_mensual", "S/ {:.0f}"),
              ("Autos de rotación por día", "tickets_dia", "{:.0f}"), ("Ticket promedio de rotación", "ticket_prom", "S/ {:.2f}"),
              ("Motos / mototaxis abonados", "motos", "{:.0f}"), ("Tarifa mensual moto", "tarifa_moto", "S/ {:.0f}")]
    for et, at, fm in campos:
        data.append([et] + [fm.format(getattr(e, at)) for e in rt.ESCENARIOS])
    data.append(["Ingreso mensual"] + [S(rt.ingreso_mensual(e)) for e in rt.ESCENARIOS])
    E.append(tabla(data, [62, 37, 37, 38], negrita_ultima=True))
    E.append(Spacer(1, 2 * mm))
    data = [["Costo de operación anual (año estable)", "Monto"]]
    for k, v in opex.items():
        data.append([k, S(v)])
    data.append(["Total con guardián contratado", S(sum(opex.values()))])
    E.append(tabla(data, [110, 40], negrita_ultima=True))
    E.append(P(
        f"El guardián-cobrador (remuneración mínima S/ {rt.SUELDO_RMV:,.0f} + EsSalud y vacaciones) es "
        f"≈ {sum(opex.values()) and opex['Personal (1 guardián-cobrador)'] / sum(opex.values()):.0%} del costo de "
        "operación. Ingresos por debajo de S/ 8,000 al mes permiten acogerse al Nuevo RUS (cuota fija).", "small"))
    E.append(Spacer(1, 2 * mm))
    E.append(Image(g_flujo, width=W * mm, height=W * mm * 3.5 / 7.4))
    data = [["Indicador (20 años, tasa 10 %)", "Pesimista", "Base", "Optimista"]]
    for et, cp in (("Con guardián contratado", True), ("Operado por el propietario", False)):
        res = rt.evaluar("afirmado", cp)
        data.append([f"<b>{et}</b>", "", "", ""])
        data.append(["   Utilidad operativa anual"] + [S(r["ebitda"]) for r in res])
        data.append(["   VAN"] + [S(r["van"]) for r in res])
        data.append(["   TIR"] + [(f"{100 * r['tir']:.1f} %" if r["tir"] is not None and r["tir"] >= 0 else "negativa") for r in res])
        data.append(["   Recuperación de la inversión"] + [(f"{r['payback']:.1f} años" if r["payback"] else "no recupera") for r in res])
    E.append(KeepTogether([tabla(data, [62, 37, 37, 38])]))
    E.append(P(
        "Incluye rampa de ocupación (60 % el año 1 y 85 % el año 2), reajuste anual de 3 % en tarifas y costos y un "
        "mantenimiento mayor en el año 10 (6 % del CAPEX). Sin valor residual del terreno ni de la estructura "
        "(criterio conservador).", "small"))
    E.append(P("Punto de equilibrio", "h2"))
    E += bullets([
        (f"Para <b>cubrir los costos de operación</b> bastan ≈ {eq_g[0]:.0f} autos abonados con guardián contratado; "
         "si lo operas tú, la rotación diaria y las motos del escenario base ya cubren esos costos."
         if eq_p[0] < 1 else
         f"Para <b>cubrir los costos de operación</b> bastan ≈ {eq_g[0]:.0f} autos abonados con guardián (≈ "
         f"{eq_p[0]:.0f} si lo operas tú), sumando la rotación y motos del escenario base."),
        f"Para <b>recuperar la inversión en 10 años</b> hacen falta ≈ <b>{eq_p[1]:.0f} abonados</b> a S/ 120 "
        f"operándolo tú, o ≈ <b>{eq_g[1]:.0f}</b> con guardián contratado (prácticamente lleno).",
    ])
    E.append(P("¿Conviene techar desde el inicio?", "h2"))
    E.append(P(
        f"El techo cuesta ≈ {S(costo_techo)}, la mitad de la inversión. Si se construye primero <b>sin techo</b> "
        f"({S(capex_st)}) y con tarifas menores (S/ 95/mes, 15 abonados), operado por el propietario, la TIR sería "
        f"≈ {100 * tir_st_p:.0f} % con recuperación en ≈ {pb_st_p:.1f} años. El techo se justifica cuando permite "
        "cobrar ≈ S/ 25-30 más por mes y llenar la cochera: en una zona tan lluviosa como Mendoza es un diferencial "
        "real frente a cocheras descubiertas, pero conviene comprobarlo con demanda."))

    E.append(P("Tabla de sensibilidad - años de recuperación simple", "h2"))
    tarifas = [80, 100, 120, 140, 160]
    abon = [8, 12, 16, 20, 24, 28]
    b = rt.ESCENARIOS[1]
    otros = (b.tickets_dia * b.ticket_prom * 30 + b.motos * b.tarifa_moto) * 12
    for cp, et in ((False, "operado por el propietario"), (True, "con guardián contratado")):
        op = sum(rt.opex_anual(total, cp).values())
        data = [[f"Abonados \\ tarifa ({et})"] + [f"S/ {t}" for t in tarifas]]
        for a in abon:
            fila = [f"{a}"]
            for tf in tarifas:
                u = a * tf * 12 + otros - op
                fila.append("no recupera" if u <= 0 else ("> 30" if total / u > 30 else f"{total / u:.1f}"))
            data.append(fila)
        tt = tabla(data, [54, 24, 24, 24, 24, 24])
        E.append(KeepTogether([tt, Spacer(1, 3 * mm)]))
    E.append(P("Recuperación simple = inversión ÷ utilidad operativa anual (sin crecimiento ni rampa). Rotación diaria "
               "y motos del escenario base.", "small"))

    # ---------------- 8. Recomendaciones
    E.append(P("8. Recomendaciones y próximos pasos", "h1"))
    E += bullets([
        "<b>Valida la demanda antes de techar todo</b>: cuenta durante 2-3 noches los autos estacionados en la calle "
        "en 300 m a la redonda, habla con las empresas de colectivos Mendoza-Chachapoyas, con instituciones cercanas "
        "y con hoteles sin cochera. Busca reservas de abono antes de construir.",
        "<b>Construye por etapas</b>: (1) cerco, portones, afirmado con drenaje, garita, SS.HH., iluminación y "
        f"señalización; (2) techos T-1 y T-2 (19 plazas, las de mayor demanda); (3) techos T-3 y T-4. Cada techo es "
        "independiente, así que se puede techar fila por fila sin rehacer nada.",
        "<b>Tarifas diferenciadas</b>: plaza techada más cara que descubierta, abono nocturno, abono 24 h y tarifa "
        "por hora/día. Contratos con empresas o instituciones (5-10 plazas fijas) dan estabilidad.",
        "<b>Opéralo tú o con un familiar</b> al inicio: es la palanca que más mueve la rentabilidad.",
        "<b>Ingresos complementarios</b> en la zona interior o en la esquina: lavado de autos, guardianía de "
        "mototaxis, alquiler de un pequeño local comercial frente a la esquina (verificar zonificación).",
        "<b>Trámites</b>: certificado de parámetros urbanísticos (retiro y ochavo en la esquina A), levantamiento "
        "topográfico, estudio de mecánica de suelos, expediente técnico firmado (arquitectura, estructuras, "
        "eléctricas, sanitarias), licencia de edificación, licencia de funcionamiento e ITSE de Defensa Civil.",
        "<b>Antes del concreto</b>: cotiza el acero estructural en Chiclayo o Tarapoto y compara con talleres locales; "
        "exige pintura anticorrosiva epóxica por la humedad de la zona.",
    ])

    # ---------------- 9. Limitaciones
    E.append(P("9. Alcance y limitaciones", "h1"))
    E += bullets([
        "La geometría proviene de mediciones en Google Maps y de la imagen satelital; no reemplaza un levantamiento "
        "topográfico.",
        "La normativa citada (RNE A.010, A.120, E.020, E.030, E.050, E.060, E.090) debe verificarse en su versión "
        "vigente; los valores de pasillo y plazas se tomaron del lado conservador.",
        "La zona sísmica de Rodríguez de Mendoza debe confirmarse en el Anexo de la E.030 (se usó Z = 0.35, "
        "conservador). El viento usa la velocidad mínima de la E.020 (75 km/h).",
        "Precios, tarifas y demanda son estimaciones razonadas sin cotizaciones locales ni estudio de mercado: el "
        "archivo Excel adjunto permite reemplazarlos y recalcula todo automáticamente.",
        "Los planos son de anteproyecto: deben ser revisados y firmados por un arquitecto e ingeniero civil colegiados.",
    ])
    E.append(P("Archivos entregados", "h2"))
    data = [["Archivo", "Contenido"],
            ["Planos_Estacionamiento_Rodriguez_de_Mendoza.pdf", "7 láminas A3: L-01, A-01, A-02, E-01, E-02, E-03, E-04"],
            ["Estacionamiento_planta.dxf", "Planta en AutoCAD (capas de arquitectura y estructura, en metros)"],
            ["Modelo_Rentabilidad_Estacionamiento.xlsx", "Supuestos editables, presupuesto, escenarios, flujo 20 años, sensibilidad"],
            ["Memoria_y_Rentabilidad.pdf", "Este documento"]]
    E.append(tabla(data, [80, 94]))

    doc.build(E, onFirstPage=_pie, onLaterPages=_pie)
    return ruta_pdf


if __name__ == "__main__":
    import sys
    print(generar(sys.argv[1], sys.argv[2], sys.argv[3]))
