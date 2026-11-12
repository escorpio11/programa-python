"""
Presupuesto referencial por etapas de la pollería campestre (soles, con IGV, puesto en Mendoza).

Los metrados salen de la geometría del proyecto (`diseno.py`, `edificio.py`,
`estructura_pol.py`); los precios unitarios son referenciales (sondeo de mercado
de noviembre de 2026: proveedores de Lima, Chiclayo y Chachapoyas con flete a
Mendoza) y deben validarse con cotizaciones locales antes de contratar.

Salida: salida/Presupuesto_Polleria_Campestre.xlsx (con fórmulas) y un resumen
que usa la memoria descriptiva.
"""
from __future__ import annotations

import math
import os

import numpy as np
from shapely.geometry import LineString

import diseno as dz
import edificio as ed
import estructura_pol as es
import exportar_3d as ex

GG_UTILIDAD = 0.12        # gastos generales y utilidad del contratista (solo obra civil y estructura)
IMPREVISTOS = 0.08


def _largo(segs, tipos):
    return sum(np.hypot(s["b"][0] - s["a"][0], s["b"][1] - s["a"][1]) for s in segs if s["tipo"] in tipos)


def _largo_tab(piso, tipos=("tabique",)):
    return sum(math.hypot(s1 - s0, d1 - d0) for s0, d0, s1, d1, t in ed.TABIQUES[piso] if t in tipos)


def metrados():
    m1, m2 = ex.muros()
    H1 = dz.NPT2 - 0.45
    H2 = dz.H_ALERO - dz.NPT2 - 0.15
    area_1 = {a.nombre: a.poly.area for a in ed.AMB if a.piso == 1}
    area_2 = {a.nombre: a.poly.area for a in ed.AMB if a.piso == 2}
    sshh1 = sum(v for k, v in area_1.items() if "SS.HH." in k or k == "Lavatorios")
    sshh2 = sum(v for k, v in area_2.items() if "SS.HH." in k)
    cocina = sum(area_1[k] for k in ("Cocina: horno pollero, parrilla y freidoras", "Lavado de vajilla",
                                    "Preparación fría y maceración", "Cámara y bebidas"))
    publico1 = area_1["Hall de ingreso"] + area_1["Despacho, caja y mesas"] + area_1["Ingreso de servicio"]
    deposito = area_1["Almacén de insumos"] + area_2["Depósito del bar"] + area_2["Pasillo de servicio y evacuación"]
    bar = area_2["Bar y bebidas"]
    terraza = ed.TERRAZA.area
    escenario = ed.ESCENARIO.area
    zap = es.ZAPATAS
    n_zap = {"interior": 1, "borde": 4, "esquina": 4}
    exc = sum(n_zap[t] * zap[t]["lado"] ** 2 * zap[t]["Df"] for t in n_zap)
    conc_zap = sum(n_zap[t] * zap[t]["lado"] ** 2 * zap[t]["h"] for t in n_zap)
    conc_ped = 9 * 0.5 * 0.5 * 1.0
    largo_vc = 3 * (dz.EJES_D[-1] - dz.EJES_D[0]) + 3 * (dz.EJES_S[-1] - dz.EJES_S[0])
    conc_vc = largo_vc * 0.25 * 0.40
    kg_hss = sum(f[3] for f in es.METRADO if "HSS" in f[0])
    kg_esc = sum(f[3] for f in es.METRADO if "Escalera" in f[0])
    kg_w = es.ACERO_TOTAL_KG - kg_hss - kg_esc
    techo = (ed.TECHO_BAR.area + ed.TECHO_ESC.area) * 1.06
    muros_lad = (_largo(m1, ("muro", "muro_ventana_alta")) * H1)
    muros_ext2 = (_largo(m2, ("muro", "muro_ventana", "muro_acustico")) * H2)
    tab1 = _largo_tab(1) * H1           # los tabiques de m1/m2 (exportar_3d) repiten los de TABIQUES
    tab2 = _largo_tab(2) * H2
    vidrio1 = _largo(m1, ("vidrio", "vidrio_plegable", "puerta_vidrio")) * H1
    vidrio2 = _largo(m2, ("vidrio_plegable",)) * 2.7
    baranda = sum(math.hypot(b["b"][0] - b["a"][0], b["b"][1] - b["a"][1]) for b in ex.barandas())
    caminos = dz.caminos_poly(1).difference(dz.PORCHE).area
    cerco_frentes = 30.0 + 20.0 - (6.0 + 1.8 + 1.6 + 3.0 + 1.2)
    seto = dz.SETO and sum(p.length / 2 for p in getattr(_seto(), "geoms", [_seto()]))
    return dict(
        terreno=dz.LOTE.area, exc=exc, conc_zap=conc_zap, conc_ped=conc_ped, conc_vc=conc_vc,
        kg_hss=kg_hss, kg_w=kg_w, losa=dz.LOSA2.area, techo=techo,
        muros_lad=muros_lad, muros_ext2=muros_ext2, tab1=tab1, tab2=tab2, vidrio1=vidrio1, vidrio2=vidrio2,
        baranda=baranda, sshh1=sshh1, sshh2=sshh2, cocina=cocina, publico1=publico1, deposito=deposito, bar=bar,
        terraza=terraza, escenario=escenario, porche=dz.PORCHE.area, vereda=dz.VEREDA.area, caminos=caminos,
        calzada=dz.CALZADA.area + sum(p["poly"].area for p in dz.PLAZAS) + dz.MOTOS.area,
        cesped=_cesped(1), cerco=cerco_frentes, seto=seto,
        cielo1=dz.EDIFICIO.area - cocina, enchape=(cocina ** 0.5 * 4 + 30) * 2.1,
        construida=dz.EDIFICIO.area + dz.LOSA2.area,
        anden=dz.ANDEN.area - dz.PISCINA.area - dz.PATERA.area,
        cerco_piscina=LineString(ex.cerco_piscina()).length,
        vestidores=dz.VESTIDORES.area,
    )


def _seto():
    import laminas  # noqa: F401  (solo para reutilizar la geometría del seto)
    return laminas.seto(1)


def _cesped(etapa):
    import laminas
    return laminas.jardines(etapa).difference(dz.caminos_poly(etapa)).area - laminas.seto(etapa).area


def partidas():
    """Lista de capítulos: (etapa, capítulo, [(descripción, unidad, metrado, precio, tipo)])."""
    m = metrados()
    obra, eqp = "obra", "equipo"          # 'obra' lleva gastos generales y utilidad; 'equipo' es compra directa
    e1 = [
        ("01 OBRAS PRELIMINARES Y CIMENTACIÓN", [
            ("Limpieza, trazo y nivelación del terreno", "m²", m["terreno"], 3.5, obra),
            ("Excavación de zapatas y vigas de cimentación (Df = 1.50 m)", "m³", m["exc"] + m["conc_vc"] * 1.2, 45, obra),
            ("Relleno compactado y eliminación de excedentes", "m³", m["exc"] * 0.8, 38, obra),
            ("Concreto armado f'c 210 en zapatas (incl. acero y encofrado)", "m³", m["conc_zap"], 1150, obra),
            ("Concreto armado en pedestales y vigas de cimentación", "m³", m["conc_ped"] + m["conc_vc"], 1350, obra),
            ("Falso piso y contrapiso del 1.er piso y porches", "m²", dz.EDIFICIO.area + m["porche"], 55, obra),
        ]),
        ("02 ESTRUCTURA METÁLICA Y ENTREPISO", [
            ("Columnas y arriostres HSS (fabricados, pintados y montados)", "kg", m["kg_hss"], 12.5, obra),
            ("Vigas, viguetas, techo y correas W/C (fabricados, pintados y montados)", "kg", m["kg_w"], 11.5, obra),
            ("Losa colaborante: steel deck AD-600 + concreto e = 12 cm", "m²", m["losa"], 230, obra),
            ("Escaleras metálicas: principal en U y exterior (4 tramos)", "tramo", 4, 11000, obra),
            ("Pintura intumescente en columnas y vigas principales (RF 30 min)", "m²", 190, 45, obra),
        ]),
        ("03 CUBIERTAS", [
            ("Cobertura de panel sándwich termoacústico (bar y escenario)", "m²", m["techo"], 210, obra),
            ("Canaletas, bajadas pluviales y cumbreras", "ml", 46, 85, obra),
        ]),
        ("04 MUROS, TABIQUES Y MAMPARAS", [
            ("Muro de ladrillo tarrajeado (fachadas de servicio, posterior y SS.HH.)", "m²", m["muros_lad"] * 0.85, 160, obra),
            ("Cerramiento liviano exterior del 2.º piso (fibrocemento con aislamiento)", "m²", m["muros_ext2"] * 0.85, 120, obra),
            ("Tabiques interiores de drywall (RH en zonas húmedas)", "m²", m["tab1"] + m["tab2"], 85, obra),
            ("Mamparas de vidrio templado y puertas plegables", "m²", m["vidrio1"] + m["vidrio2"], 350, obra),
        ]),
        ("05 PISOS, ENCHAPES Y CIELOS RASOS", [
            ("Porcelanato antideslizante en cocina, SS.HH., hall, despacho y bar", "m²",
             m["cocina"] + m["sshh1"] + m["sshh2"] + m["publico1"] + m["bar"], 150, obra),
            ("Porcelanato exterior en terraza y escenario", "m²", m["terraza"] + m["escenario"], 150, obra),
            ("Cemento pulido en almacenes, depósito y pasillo", "m²", m["deposito"], 60, obra),
            ("Piso de piedra o laja en porches y vereda", "m²", m["porche"] + m["vereda"], 120, obra),
            ("Enchape de muros de cocina y SS.HH. (h = 2.10 m)", "m²", m["enchape"], 95, obra),
            ("Cielo raso de drywall en el 1.er piso (excepto cocina)", "m²", m["cielo1"], 85, obra),
            ("Cielo raso de fibrocemento lavable en cocina", "m²", m["cocina"], 110, obra),
        ]),
        ("06 CARPINTERÍA, BARANDAS Y PORTONES", [
            ("Barandas de vidrio laminado y pasamanos inox. (terraza)", "ml", m["baranda"], 950, obra),
            ("Puertas interiores de madera y contraplacadas", "und", 16, 650, obra),
            ("Portón vehicular V-1 de 2 hojas (6.00 × 2.00 m)", "m²", 12.0, 600, obra),
            ("Portada principal P-1 de madera con techo de teja", "glb", 1, 6500, obra),
            ("Puertas P-2, P-3 (antipánico) y P-4 (GLP)", "und", 3, 1500, obra),
        ]),
        ("07 INSTALACIONES", [
            ("Instalaciones eléctricas del edificio (tableros, circuitos, luminarias)", "m²", m["construida"], 120, obra),
            ("Iluminación exterior de jardines, caminos y estacionamiento", "glb", 1, 9000, obra),
            ("Instalaciones sanitarias (agua, desagüe, trampa de grasas, pluviales)", "m²", m["construida"], 95, obra),
            ("Red de GLP con caseta, regulador, válvulas y detector", "glb", 1, 9000, obra),
            ("Seguridad: extintores PQS y K, luces de emergencia, señalización, detectores", "glb", 1, 5000, obra),
            ("Sistema de sonido base del escenario y bar", "glb", 1, 7000, eqp),
        ]),
        ("08 ASCENSOR", [
            ("Ascensor panorámico de 2 paradas (cabina 1.20 × 1.40 m) con caja de vidrio", "und", 1, 70000, eqp),
        ]),
        ("09 EQUIPAMIENTO DE COCINA Y BAR", [
            ("Horno pollero a leña de 40-48 pollos", "und", 2, 13000, eqp),
            ("Chimenea de acero de los hornos (hasta 1.00 m sobre la cumbrera)", "und", 2, 4000, eqp),
            ("Parrilla a carbón con estructura de acero", "und", 1, 3000, eqp),
            ("Campana extractora de 5.00 m con filtros, ducto y extractor", "glb", 1, 13000, eqp),
            ("Freidora industrial a gas", "und", 2, 3500, eqp),
            ("Cámara de conservación y conservadoras", "glb", 1, 22000, eqp),
            ("Mesas de trabajo de acero inoxidable", "und", 3, 1900, eqp),
            ("Lavaderos de acero inoxidable de 2 pozas", "und", 2, 2000, eqp),
            ("Barra de atención del bar (4.60 m) y contrabarra", "ml", 4.6, 2200, eqp),
            ("Mostrador de despacho y caja", "glb", 1, 3500, eqp),
        ]),
        ("10 SOMBRILLAS Y MOBILIARIO", [
            ("Sombrilla profesional 3.00 × 3.00 m de mástil central", "und", 10, 2500, eqp),
            ("Camisa empotrada con dado de concreto y tapa al ras (anclaje removible)", "und", 12, 350, obra),
            ("Base móvil lastrada para sombrilla (posiciones eventuales)", "und", 4, 700, eqp),
            ("Juego de mesa de 6 con sillas de exterior", "jgo", 9, 1500, eqp),
            ("Juego de mesa de 4 con sillas", "jgo", 1 + len(ed.MESAS_1) - 2 + len(ed.MESAS_2), 1000, eqp),
            ("Juego de mesa de 2 con sillas (despacho)", "jgo", 2, 600, eqp),
            ("Taburetes de barra", "und", len(ed.TABURETES), 250, eqp),
        ]),
        ("11 OBRAS EXTERIORES", [
            ("Calzada, estacionamientos y motos en adoquín de concreto", "m²", m["calzada"], 95, obra),
            ("Caminos peatonales de piedra o laja", "m²", m["caminos"], 95, obra),
            ("Césped (tierra de chacra, nivelación y siembra)", "m²", m["cesped"], 22, obra),
            ("Cerco de los frentes: murete de piedra + reja de madera (h = 1.80 m)", "ml", m["cerco"], 380, obra),
            ("Seto vivo en los frentes", "ml", m["seto"], 25, obra),
            ("Árboles y palmeras", "und", 5, 350, obra),
            ("Caseta de GLP y residuos", "glb", 1, 3500, obra),
            ("Señalización vial, topes y numeración de plazas", "glb", 1, 1500, obra),
        ]),
    ]
    e2 = [
        ("12 PISCINA Y PATERA (2.ª ETAPA)", [
            ("Piscina de adultos 6.00 × 3.50 m y patera 2.40 × 2.40 m, con filtración y recirculación", "glb", 1, 80000, obra),
            ("Andén perimetral antideslizante de 1.50 m", "m²", m["anden"], 150, obra),
            ("Cerco de vidrio templado h = 1.20 m con puerta de cierre automático", "ml", m["cerco_piscina"], 950, obra),
        ]),
        ("13 VESTIDORES, DUCHA Y PEDILUVIO (2.ª ETAPA)", [
            ("Módulo de vestidores damas/varones y cuarto de máquinas (albañilería, techo, acabados, aparatos)", "m²",
             m["vestidores"], 2000, obra),
            ("Ducha exterior", "und", 1, 1500, obra),
            ("Pediluvio de 3.00 × 1.20 m", "und", 1, 3000, obra),
        ]),
        ("14 ZONA DE RELAJO (2.ª ETAPA)", [
            ("Camillas (tumbonas) de exterior", "und", len(dz.CAMILLAS), 650, eqp),
            ("Hamacas con soporte", "und", len(dz.HAMACAS), 1300, eqp),
            ("Piso de deck o piedra en la zona de relajo", "m²", dz.RELAJO.area, 120, obra),
        ]),
    ]
    return e1, e2


def resumen():
    e1, e2 = partidas()
    out = {}
    for nombre, caps in (("etapa1", e1), ("etapa2", e2)):
        obra = sum(q * pu for _, items in caps for _, _, q, pu, t in items if t == "obra")
        eqp = sum(q * pu for _, items in caps for _, _, q, pu, t in items if t == "equipo")
        gg = obra * GG_UTILIDAD
        sub = obra + eqp + gg
        exp = 18000 if nombre == "etapa1" else 6000         # expediente técnico, licencia, ITSE/DIRESA
        imp = (sub + exp) * IMPREVISTOS
        out[nombre] = dict(obra=obra, equipo=eqp, gg=gg, expediente=exp, imprevistos=imp,
                           total=sub + exp + imp,
                           capitulos=[(c, sum(q * pu for _, _, q, pu, _ in items)) for c, items in caps])
    return out


def exportar_xlsx(ruta):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter

    e1, e2 = partidas()
    wb = Workbook()
    fino = Side(style="thin", color="999999")
    borde = Border(left=fino, right=fino, top=fino, bottom=fino)
    neg = Font(bold=True)
    gris = PatternFill("solid", fgColor="E6E6E6")
    azul = PatternFill("solid", fgColor="DCE6F1")
    soles = '#,##0.00'

    def hoja(ws, titulo, caps, gastos_exp):
        ws.append([titulo])
        ws["A1"].font = Font(bold=True, size=13)
        ws.append(["Precios referenciales con IGV, puesto en Mendoza (Amazonas), noviembre de 2026. "
                   "Metrados del anteproyecto; validar con cotizaciones locales."])
        ws.append([])
        ws.append(["Ítem", "Descripción", "Und.", "Metrado", "P.U. (S/)", "Parcial (S/)", "Tipo"])
        for c in ws[4]:
            c.font = neg
            c.fill = gris
            c.border = borde
        fila = 5
        filas_cap = []
        filas_obra, filas_eq = [], []
        for cap, items in caps:
            ws.cell(row=fila, column=1, value=cap.split(" ")[0]).font = neg
            ws.cell(row=fila, column=2, value=cap[3:]).font = neg
            fila_cap = fila
            fila += 1
            ini = fila
            for i, (desc, und, q, pu, tipo) in enumerate(items, start=1):
                ws.cell(row=fila, column=1, value=f"{cap.split(' ')[0]}.{i:02d}")
                ws.cell(row=fila, column=2, value=desc)
                ws.cell(row=fila, column=3, value=und)
                ws.cell(row=fila, column=4, value=round(q, 2)).number_format = '#,##0.00'
                ws.cell(row=fila, column=5, value=pu).number_format = soles
                ws.cell(row=fila, column=6, value=f"=D{fila}*E{fila}").number_format = soles
                ws.cell(row=fila, column=7, value="obra" if tipo == "obra" else "compra directa")
                (filas_obra if tipo == "obra" else filas_eq).append(fila)
                fila += 1
            c = ws.cell(row=fila_cap, column=6, value=f"=SUM(F{ini}:F{fila - 1})")
            c.number_format = soles
            c.font = neg
            for col in range(1, 8):
                ws.cell(row=fila_cap, column=col).fill = azul
            filas_cap.append(fila_cap)
        fila += 1

        def total(etq, formula, bold=False):
            nonlocal fila
            ws.cell(row=fila, column=2, value=etq).font = Font(bold=bold)
            c = ws.cell(row=fila, column=6, value=formula)
            c.number_format = soles
            c.font = Font(bold=bold)
            fila += 1
            return fila - 1

        f_obra = total("Costo directo de obra (construcción e instalaciones)",
                       "=" + "+".join(f"F{r}" for r in filas_obra))
        f_eq = total("Equipos y mobiliario (compra directa)", "=" + "+".join(f"F{r}" for r in filas_eq))
        f_gg = total(f"Gastos generales y utilidad del contratista ({GG_UTILIDAD:.0%} de la obra)",
                     f"=F{f_obra}*{GG_UTILIDAD}")
        f_exp = total("Expediente técnico, licencia de edificación, ITSE / autorización sanitaria", f"={gastos_exp}")
        f_imp = total(f"Imprevistos ({IMPREVISTOS:.0%})", f"=(F{f_obra}+F{f_eq}+F{f_gg}+F{f_exp})*{IMPREVISTOS}")
        f_tot = total("TOTAL REFERENCIAL (S/ con IGV)", f"=F{f_obra}+F{f_eq}+F{f_gg}+F{f_exp}+F{f_imp}", True)
        for r in range(4, fila):
            for col in range(1, 8):
                ws.cell(row=r, column=col).border = borde
                ws.cell(row=r, column=col).alignment = Alignment(vertical="center", wrap_text=col == 2)
        widths = [8, 78, 7, 11, 12, 15, 15]
        for i, w in enumerate(widths, start=1):
            ws.column_dimensions[get_column_letter(i)].width = w
        ws.freeze_panes = "A5"
        return f_tot

    ws1 = wb.active
    ws1.title = "Etapa 1"
    t1 = hoja(ws1, "PRESUPUESTO REFERENCIAL - 1.ª ETAPA: POLLERÍA, EDIFICIO Y JARDINES", e1, 18000)
    ws2 = wb.create_sheet("Etapa 2")
    t2 = hoja(ws2, "PRESUPUESTO REFERENCIAL - 2.ª ETAPA: PISCINA, VESTIDORES Y RELAJO", e2, 6000)

    ws = wb.create_sheet("Resumen", 0)
    r = resumen()
    ws.append(["POLLERÍA CAMPESTRE - RESUMEN DEL PRESUPUESTO REFERENCIAL"])
    ws["A1"].font = Font(bold=True, size=13)
    ws.append(["Jr. Rodríguez de Mendoza esq. calle lateral, Mendoza (Amazonas). Soles con IGV, noviembre de 2026."])
    ws.append([])
    ws.append(["Concepto", "1.ª etapa (S/)", "2.ª etapa (S/)", "Total (S/)"])
    for c in ws[4]:
        c.font = neg
        c.fill = gris
    ws.append(["Total referencial (de las hojas de cada etapa)", f"='Etapa 1'!F{t1}", f"='Etapa 2'!F{t2}", "=B5+C5"])
    area_t = dz.EDIFICIO.area + dz.LOSA2.area
    ws.append(["Área techada del edificio (m²)", round(area_t, 1), None, None])
    ws.append(["Costo total de la 1.ª etapa por m² techado (S/ / m²)", f"=B5/B6", None, None])
    ws.append([])
    ws.append(["Capítulo", "Parcial (S/)"])
    for c in ws[9]:
        c.font = neg
        c.fill = gris
    for etapa in ("etapa1", "etapa2"):
        for cap, val in r[etapa]["capitulos"]:
            ws.append([cap, round(val, 2)])
    for row in ws.iter_rows(min_row=5, max_row=ws.max_row):
        for c in row[1:]:
            c.number_format = soles
    ws.column_dimensions["A"].width = 70
    for col in "BCD":
        ws.column_dimensions[col].width = 18

    ws3 = wb.create_sheet("Supuestos")
    sup = [
        "Precios unitarios referenciales con IGV y flete a Mendoza (sondeo de noviembre de 2026); validar con 3 cotizaciones.",
        "Estructura metálica: acero W a S/ 11.5/kg y HSS a S/ 12.5/kg fabricados, con pintura anticorrosiva y montaje.",
        "Metrado de acero del predimensionamiento (estructura_pol.py); las escaleras se presupuestan por tramo.",
        "Cimentación con capacidad portante supuesta de 1.0 kg/cm²: confirmar con estudio de mecánica de suelos.",
        f"Gastos generales y utilidad ({GG_UTILIDAD:.0%}) solo sobre obra; equipos y mobiliario se compran directamente.",
        f"Imprevistos {IMPREVISTOS:.0%}. Expediente técnico, licencia (modalidad C), ITSE y autorización sanitaria como monto global.",
        "No incluye: terreno, conexiones domiciliarias (agua, desagüe, energía trifásica), capital de trabajo ni menaje.",
        "El almacén de leña y el garaje existentes se conservan sin intervención.",
    ]
    ws3.append(["SUPUESTOS Y EXCLUSIONES"])
    ws3["A1"].font = Font(bold=True, size=13)
    for t in sup:
        ws3.append([t])
    ws3.column_dimensions["A"].width = 120
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    wb.save(ruta)
    return ruta


if __name__ == "__main__":
    r = resumen()
    for etapa in ("etapa1", "etapa2"):
        d = r[etapa]
        print(etapa, f"obra {d['obra']:,.0f}  equipo {d['equipo']:,.0f}  GG {d['gg']:,.0f}  imp {d['imprevistos']:,.0f}"
                     f"  TOTAL {d['total']:,.0f}")
        for c, v in d["capitulos"]:
            print(f"   {c:60s} {v:12,.0f}")
    print(exportar_xlsx(os.path.join(dz.AQUI, "salida", "Presupuesto_Polleria_Campestre.xlsx")))
