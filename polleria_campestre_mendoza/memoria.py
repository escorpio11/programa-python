"""
Memoria descriptiva del anteproyecto de la pollería campestre (PDF A4).

Reúne el concepto, la zonificación, las circulaciones, el programa del edificio,
las sombrillas removibles, la 2.ª etapa (piscina), la estructura metálica, las
instalaciones, la normativa a cumplir y el presupuesto referencial. Las cifras
se leen de los módulos del proyecto, de modo que la memoria se actualiza sola
cuando cambia el diseño.
"""
from __future__ import annotations

import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(1, os.path.join(AQUI, "..", "estacionamiento_rodriguez_mendoza"))

from PIL import Image as PILImage  # noqa: E402
from reportlab.lib import colors  # noqa: E402
from reportlab.lib.pagesizes import A4  # noqa: E402
from reportlab.lib.units import mm  # noqa: E402
from reportlab.platypus import Image, KeepTogether, PageBreak, SimpleDocTemplate, Spacer, Table, TableStyle  # noqa: E402

import diseno as dz  # noqa: E402
import edificio as ed  # noqa: E402
import estructura_pol as es  # noqa: E402
import laminas as lm  # noqa: E402
import presupuesto as pr  # noqa: E402
from informe import AZUL, FONDO, GRIS, P, S, bullets, st, tabla  # noqa: E402

TITULO = "Pollería campestre - Jr. Rodríguez de Mendoza, Mendoza (Amazonas) - Anteproyecto"


def _pie(canvas, doc):
    canvas.saveState()
    canvas.setFont("Lib", 7.5)
    canvas.setFillColor(GRIS)
    canvas.drawString(18 * mm, 10 * mm, TITULO)
    canvas.drawRightString(192 * mm, 10 * mm, f"Pág. {doc.page}")
    canvas.restoreState()


def _recorte(png, destino, caja_mm, ancho_px=None):
    """Recorta una zona (x0, y0, x1, y1 en mm desde la esquina inferior izquierda de la hoja A3) de una lámina."""
    im = PILImage.open(png)
    W, H = im.size
    kx, ky = W / 420.0, H / 297.0
    x0, y0, x1, y1 = caja_mm
    im = im.crop((int(x0 * kx), int(H - y1 * ky), int(x1 * kx), int(H - y0 * ky)))
    if ancho_px:
        im = im.resize((ancho_px, int(im.size[1] * ancho_px / im.size[0])))
    im.save(destino)
    return destino


def _img(ruta, ancho_mm):
    im = PILImage.open(ruta)
    w, h = im.size
    return Image(ruta, width=ancho_mm * mm, height=ancho_mm * mm * h / w)


def _kpis(items, W):
    celdas = [[P(v, "kpi_v") for v, _ in items], [P(l, "kpi_l") for _, l in items]]
    t = Table(celdas, colWidths=[W / len(items) * mm] * len(items))
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), FONDO), ("BOX", (0, 0), (-1, -1), 0.6, AZUL),
                           ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.white),
                           ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    return t


def generar(ruta_pdf, previas_dir, tmp_dir):
    os.makedirs(tmp_dir, exist_ok=True)
    r = pr.resumen()
    e1, e2 = r["etapa1"], r["etapa2"]
    sj1, nm1 = lm.asientos_jardin(1)
    p1, p2 = lm.asientos_edificio()
    cap_rest = sj1 + p1 + p2
    centros, _ = lm.mesas_evento(1)
    cesped1 = lm.jardines(1).difference(dz.caminos_poly(1)).area
    area_techada = dz.EDIFICIO.area + dz.LOSA2.area
    terr = ed.TERRAZA.area
    aforo_evento = int(cesped1 / 1.0 + terr / 1.0 + dz.PORCHE.area / 1.0)

    # figuras recortadas de las láminas
    f_a01 = _recorte(os.path.join(previas_dir, "A-01.png"), os.path.join(tmp_dir, "m_a01.png"), (10, 28, 318, 287), 1500)
    f_a02 = _recorte(os.path.join(previas_dir, "A-02.png"), os.path.join(tmp_dir, "m_a02.png"), (10, 28, 318, 200), 1500)
    f_a03 = _recorte(os.path.join(previas_dir, "A-03.png"), os.path.join(tmp_dir, "m_a03.png"), (10, 28, 318, 287), 1500)
    f_a04 = _recorte(os.path.join(previas_dir, "A-04.png"), os.path.join(tmp_dir, "m_a04.png"), (10, 128, 318, 287), 1500)
    f_a05 = _recorte(os.path.join(previas_dir, "A-05.png"), os.path.join(tmp_dir, "m_a05.png"), (10, 14, 318, 287), 1400)
    f_a06 = _recorte(os.path.join(previas_dir, "A-06.png"), os.path.join(tmp_dir, "m_a06.png"), (10, 14, 318, 287), 1400)
    f_a07 = _recorte(os.path.join(previas_dir, "A-07.png"), os.path.join(tmp_dir, "m_a07.png"), (10, 14, 318, 287), 1500)
    f_a08 = _recorte(os.path.join(previas_dir, "A-08.png"), os.path.join(tmp_dir, "m_a08.png"), (10, 14, 318, 287), 1500)

    doc = SimpleDocTemplate(ruta_pdf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm,
                            bottomMargin=16 * mm, title="Pollería campestre - memoria descriptiva",
                            author="Anteproyecto")
    W = 174
    E = []

    # ---------------- Portada
    E += [Spacer(1, 10 * mm), P("POLLERÍA CAMPESTRE", "title"), Spacer(1, 3 * mm),
          P("Memoria descriptiva del anteproyecto, estructura metálica y presupuesto referencial", "subtitle"),
          P("Jr. Rodríguez de Mendoza esquina calle lateral - Mendoza (San Nicolás), Rodríguez de Mendoza, Amazonas",
            "subtitle"),
          P("Anteproyecto - noviembre 2026", "subtitle"), Spacer(1, 6 * mm)]
    E.append(_kpis([(f"{dz.LOTE.area:,.0f} m²", "terreno"), (f"{area_techada:,.0f} m²", "área techada (2 pisos)"),
                    (f"{cap_rest}", "asientos en modo restaurante"), (f"≈ {aforo_evento}", "personas en modo evento"),
                    (f"S/ {e1['total'] / 1e6:,.2f} M", "inversión 1.ª etapa")], W))
    E += [Spacer(1, 5 * mm), _img(f_a01, W),
          P("Planimetría general de la 1.ª etapa (lámina A-01).", "caption")]
    E.append(PageBreak())

    # ---------------- 1. Resumen
    E.append(P("1. Resumen del proyecto", "h1"))
    E += bullets([
        f"Pollería campestre en el lote de {dz.LOTE.area:,.0f} m² de la esquina del Jr. Rodríguez de Mendoza con la calle "
        "lateral. Se conservan el <b>almacén de leña</b> y el <b>garaje del propietario</b> existentes (zonas marcadas en rojo).",
        "Un <b>edificio central de estructura metálica de 2 pisos</b>: abajo la cocina con 2 hornos polleros a leña, parrilla, "
        "freidoras, despacho y servicios; arriba el bar, una terraza exterior en volado y un <b>escenario de 4.00 × 6.00 m</b> "
        "para grupos musicales y sus equipos.",
        f"<b>Jardines con {nm1} sombrillas profesionales de 3.00 × 3.00 m</b> ancladas en camisas empotradas: se retiran en "
        "minutos para fiestas de fin de semana o fechas especiales y el césped queda libre.",
        f"<b>Calzada de doble sentido</b> desde la calle lateral, {len(dz.PLAZAS)} estacionamientos descubiertos (1 accesible), "
        "2 de motos, zona de carga y caseta de GLP; el público peatonal entra por el Jr. Rodríguez de Mendoza, separado de los "
        "vehículos y del servicio.",
        "<b>2.ª etapa</b>: piscina de 6.00 × 3.50 m con patera para niños, vestidores, ducha exterior, pediluvio y zona de "
        "relajo con camillas y hamacas, en el jardín posterior.",
        f"Inversión referencial con IGV: <b>{S(e1['total'])}</b> en la 1.ª etapa y <b>{S(e2['total'])}</b> en la 2.ª "
        f"(total {S(e1['total'] + e2['total'])}).",
    ])

    # ---------------- 2. Terreno
    E.append(P("2. Terreno, orientación y preexistencias", "h1"))
    E.append(P(
        "El lote es un cuadrilátero de lados 30.00 m (frente al Jr. Rodríguez de Mendoza), 20.00 m (calle lateral), "
        "40.00 m y 30.00 m (colindantes), medido por el propietario sobre imagen satelital; debe confirmarse con un "
        "levantamiento topográfico. El edificio se ordena paralelo a la calle lateral, de modo que queda girado unos 65° "
        "respecto del norte: su fachada de ingreso mira al <b>ONO</b> (calle lateral), la fachada lateral al <b>SSO</b> "
        "(Jr. Rodríguez de Mendoza), la de servicio al <b>NNE</b> (calzada) y la posterior al <b>ESE</b> (piscina)."))
    E.append(P(
        f"Se conservan sin intervención el almacén de leña ({dz.LENA.area:.1f} m², junto al lindero del fondo) y el garaje "
        f"del propietario ({dz.GARAJE.area:.1f} m², en la esquina C), ambos servidos por la nueva calzada. La leña llega a la "
        "cocina cruzando la calzada hasta el ingreso de servicio."))

    # ---------------- 3. Zonificación
    E.append(P("3. Concepto y zonificación", "h1"))
    filas = [["Zona", "Uso", "Área (m²)"]]
    filas_a, techada = lm.cuadro_areas(1)
    for nombre, val in filas_a:
        filas.append([nombre, "", f"{val:,.1f}"])
    for f in filas[1:]:
        n = f[0]
        f[1] = {"Área del terreno": "", "Almacén de leña y garaje (existentes)": "se conservan",
                "Calzada, estacionamientos, motos y GLP": "vehicular y servicio",
                "Edificio: 1.er piso cerrado": "cocina, despacho y SS.HH.",
                "Porches techados (bajo el 2.º piso)": "mesas bajo techo",
                "Veredas, caminos y escalera exterior": "circulación peatonal",
                "Jardines y setos": "sombrillas / eventos",
                "2.º piso: bar, SS.HH., terraza y escenario (techado parcial)": "bar, terraza y espectáculos"}.get(n, "")
    E.append(tabla(filas, [82, 62, 30], alinear_der=(2,)))
    E.append(Spacer(1, 3 * mm))
    E.append(P(
        "El edificio ocupa el centro del lote, junto a la calzada: su franja de servicio (cocina, almacén, lavado, cámara) "
        "da a la calzada y a la zona de carga, y su franja pública (hall, despacho, SS.HH.) da a los jardines. Los volados "
        "de 2.00 m del 2.º piso forman porches techados en el ingreso y en el lado del jardín lateral. Los jardines de "
        "ingreso, lateral y posterior rodean el edificio y concentran las sombrillas."))

    # ---------------- 4. Circulaciones
    E.append(P("4. Circulaciones", "h1"))
    E += bullets([
        "<b>Vehicular</b>: portón V-1 de 6.00 m en la calle lateral; calzada de 6.00 m de doble sentido que recorre el "
        "lindero del fondo hasta el garaje; plazas a 90° (E1 accesible de 3.80 × 5.00 m, E2-E5 de 2.50 × 5.00 m), motos, "
        "zona de carga y caseta de GLP con puerta a la vía.",
        "<b>Peatonal del público</b>: portada P-1 (3.00 m) en el Jr. Rodríguez de Mendoza, camino de 1.80 m hasta el hall; "
        "caminos y porches hacia los jardines; el camino posterior une el porche lateral con la salida de emergencia P-3.",
        "<b>Servicio</b>: puerta P-2 (1.80 m) en la calle lateral y vereda interior de 1.20 m hasta el ingreso de servicio "
        "y la escalera exterior; proveedores y personal no cruzan las zonas del público.",
        "<b>Evacuación</b>: dos escaleras desde el 2.º piso (principal en U y exterior, ambas de 1.20 m) y cuatro salidas "
        "al exterior (P-1, P-2, P-3 y V-1); los recorridos más largos son menores de 45 m (lámina A-03).",
        f"<b>Estacionamiento en eventos</b>: las {len(dz.PLAZAS)} plazas internas no cubren la demanda de una fiesta; se "
        "recomienda coordinar con la municipalidad el uso de la vía y un convenio con un terreno cercano.",
    ])
    E += [Spacer(1, 2 * mm), _img(f_a03, W * 0.92), P("Circulaciones y rutas de evacuación (lámina A-03).", "caption")]

    # ---------------- 5. Edificio
    E.append(PageBreak())
    E.append(P("5. Edificio central", "h1"))
    E.append(P("5.1 Primer piso: cocina, hornos, parrilla y despacho", "h2"))
    filas = [["Ambiente", "Área (m²)"]] + [[a.nombre, f"{a.poly.area:.1f}"] for a in ed.AMB if a.piso == 1]
    filas.append(["Porches techados", f"{dz.PORCHE.area - ed.RL(*ed.ASCENSOR).area:.1f}"])
    E.append(tabla(filas, [120, 30], alinear_der=(1,)))
    E.append(Spacer(1, 2 * mm))
    E.append(P(
        "La línea de fuego (2 hornos polleros a leña de 40 pollos, parrilla a carbón y 2 freidoras) se apoya en el muro de "
        "servicio bajo una campana continua de 5.00 m; las chimeneas de los hornos suben por un ducto cortafuego hasta "
        "1.00 m sobre la cumbrera. El ingreso de servicio entra a la cocina por el pasillo frío, lejos de los hornos. "
        "El pase caliente comunica la cocina con el mostrador de despacho y caja."))
    E += [_img(f_a05, W * 0.86), P("Planta del 1.er piso (lámina A-05).", "caption")]
    E.append(P("5.2 Segundo piso: bar, terraza y escenario", "h2"))
    filas = [["Ambiente", "Área (m²)"]] + [[a.nombre, f"{a.poly.area:.1f}"] for a in ed.AMB if a.piso == 2]
    E.append(tabla(filas, [120, 30], alinear_der=(1,)))
    E.append(Spacer(1, 2 * mm))
    E.append(P(
        f"La terraza exterior ({terr:.0f} m²) rodea la escalera y se abre al escenario, ubicado al fondo de la franja "
        "pública con un muro acústico detrás y techo a dos aguas propio; el público mira hacia el escenario con la luz de la "
        "tarde a la espalda. El bar abre a la terraza con puertas plegables de vidrio y tiene depósito propio junto al "
        "pasillo de servicio, por donde también suben los equipos de sonido desde la escalera exterior. Los SS.HH. del 2.º "
        "piso (accesible, damas y varones) se entran desde el volado techado de ingreso."))
    E += [_img(f_a06, W * 0.86), P("Planta del 2.º piso (lámina A-06).", "caption")]
    E += bullets([
        "Accesibilidad (A.120): ascensor panorámico exterior de 2 paradas con cabina de 1.20 × 1.40 m junto al ingreso, "
        "SS.HH. accesible en cada piso y estacionamiento accesible.",
        "Aparatos sanitarios del público: 2 SS.HH. accesibles, damas 3 inodoros, varones 2 inodoros y 3 urinarios, "
        "lavatorios en ambos pisos; para eventos grandes se complementan con baños portátiles.",
        "Barandas de vidrio laminado de 1.10 m; NPT del 2.º piso +3.85 m; alero +7.15 m; cumbrera +8.25 m.",
    ])
    E += [_img(f_a07, W), P("Cortes y elevaciones (lámina A-07).", "caption")]

    # ---------------- 6. Sombrillas
    E.append(PageBreak())
    E.append(P("6. Sombrillas removibles: modo restaurante y modo evento", "h1"))
    E.append(P(
        f"Las {nm1} sombrillas profesionales de 3.00 × 3.00 m (mástil central de aluminio, lona acrílica) se distribuyen "
        "en los jardines de ingreso, lateral y posterior, cada una con su mesa (de 6 o de 4 personas). Cada sombrilla se "
        "inserta en una <b>camisa de acero galvanizado de Ø 3\"</b> empotrada en un dado de concreto bajo el césped, con "
        "pasador de seguridad y <b>tapa abatible al ras</b>: para un evento se retiran el pasador y el mástil, se cierra la "
        "tapa y el jardín queda libre, sin bases que estorben. Se guardan cerradas en el depósito bajo la escalera o en el "
        "garaje; 4 bases móviles lastradas permiten ubicarlas donde haga falta."))
    filas = [["1.ª etapa", "Modo restaurante", "Modo evento"],
             ["Sombrillas instaladas", f"{nm1}", "0 (retiradas)"],
             ["Asientos en jardines", f"{sj1}", f"{8 * len(centros)} (mesas redondas de 8)"],
             ["Pista de baile", "-", "7.00 × 4.50 m sobre el césped"],
             ["Césped libre", "-", f"{cesped1:.0f} m² (≈ {cesped1:.0f} personas de pie)"],
             ["Música", "ambiental", "escenario de la terraza"]]
    E.append(tabla(filas, [50, 50, 74]))
    E += [Spacer(1, 2 * mm), _img(f_a04, W), P("Modos restaurante y evento (lámina A-04).", "caption")]

    # ---------------- 7. 2.ª etapa
    E.append(P("7. Segunda etapa: piscina, vestidores y relajo", "h1"))
    vol = dz.PISCINA.area * (dz.PROF_MIN + dz.PROF_MAX) / 2 + dz.PATERA.area * 0.35
    E.append(P(
        f"En el jardín posterior: piscina de adultos de 6.00 × 3.50 m (1.20 a 1.50 m de profundidad) y patera para niños "
        f"de 2.40 × 2.40 m (0.30-0.40 m) separada del vaso, con andén perimetral de 1.50 m; volumen total ≈ {vol:.0f} m³. "
        "El acceso es obligatorio por los vestidores (damas y varones), el paso limpio, la ducha y el pediluvio de 3.00 m, "
        "según el D.S. 007-2003-SA; un cerco de vidrio de 1.20 m separa la piscina del jardín. El cuarto de máquinas se "
        "atiende desde el jardín. La zona de relajo junto al garaje reúne 3 camillas, 2 hamacas y una sombrilla."))
    E += [_img(f_a08, W * 0.95), P("Piscina, vestidores y relajo (lámina A-08).", "caption")]

    # ---------------- 8. Estructura
    E.append(PageBreak())
    E.append(P("8. Estructura metálica (predimensionamiento)", "h1"))
    E.append(P(
        "Pórticos de acero con arriostres concéntricos en X en ambas direcciones, sobre zapatas aisladas unidas por vigas "
        "de cimentación. Entrepiso de losa colaborante sobre viguetas y vigas principales con volados de 2.00 m; techos a "
        "dos aguas de panel sándwich termoacústico sobre vigas y correas. Diseño LRFD (E.090 / AISC 360) con cargas de la "
        "E.020: muerta de losa 3.55 kPa, tabiquería 0.5 kPa, viva de terraza 4.0 kPa y de <b>escenario 7.5 kPa "
        "(750 kgf/m²)</b>, aplicada del lado seguro en vigas, columnas y zapatas."))
    filas = [["Elemento", "Resultado"]] + [[k, v] for k, v in es.resumen()]
    E.append(tabla(filas, [38, 136]))
    E.append(Spacer(1, 2 * mm))
    E += bullets([
        "Sismo: Mendoza figura en la zona 2 de la E.030-2018 (Z = 0.25) y un restaurante es categoría C (U = 1.0); por la "
        "terraza con espectáculos y la reciente actualización de la norma (R.M. 183-2026-VIVIENDA) se predimensiona del "
        "lado seguro con Z = 0.35 y U = 1.3, a confirmar en el proyecto de estructuras.",
        f"Cimentación con capacidad portante supuesta de {es.Q_ADM / 100:.1f} kg/cm²: es indispensable un estudio de "
        "mecánica de suelos (E.050) antes del proyecto definitivo.",
        "El predimensionamiento no reemplaza el cálculo estructural firmado por un ingeniero civil colegiado.",
    ])

    # ---------------- 9. Instalaciones y seguridad
    E.append(P("9. Instalaciones y seguridad", "h1"))
    E += bullets([
        "<b>GLP</b>: caseta exterior ventilada junto a la calle lateral (recambio de balones sin entrar al lote), red a "
        "freidoras y cocina con válvulas de corte y detector de gas.",
        "<b>Extracción de cocina</b>: campana con filtros de grasa, ducto y extractor; chimeneas propias de los hornos a "
        "leña; trampa de grasas antes de la red pública.",
        "<b>Protección contra incendios</b>: extintor clase K a menos de 9 m de las freidoras, extintor de agua para los "
        "hornos a leña, PQS en cada nivel, luces de emergencia y señalización (NTP 399.010-1); se recomienda un sistema "
        "fijo de agente húmedo en la campana.",
        "<b>Electricidad</b>: suministro trifásico, tablero general y de distribución por piso, circuitos de cocina, bar y "
        "escenario independientes, iluminación exterior de jardines y caminos, pozo a tierra.",
        "<b>Ruido</b>: muro acústico detrás del escenario y techos termoacústicos; espectáculos hasta las 22:00 o con un "
        "estudio acústico que demuestre el cumplimiento de los ECA de ruido en la zona (60/50 dB(A) residencial).",
    ])

    # ---------------- 10. Normativa
    E.append(P("10. Normativa y trámites", "h1"))
    filas = [["Norma o trámite", "Aplicación en el proyecto"],
             ["RNE A.070 Comercio", "Aforo, SS.HH., estacionamientos y altura de ambientes del restaurante"],
             ["RNE A.120 Accesibilidad (2023)", "Ascensor, SS.HH. accesibles por piso, rampa y plaza accesible"],
             ["RNE A.130 Seguridad", "Rutas y distancias de evacuación, anchos de puertas y escaleras, señalización"],
             ["RNE E.020 / E.030 / E.050 / E.090", "Cargas, sismo, suelos y estructuras de acero"],
             ["D.S. 007-2003-SA", "Piscina: andén, pediluvio, patera, vestuarios, calidad del agua, vigilancia"],
             ["Licencia de edificación", "Modalidad C (uso comercial con concurrencia de público)"],
             ["ITSE / ECSE", "Inspección técnica de seguridad previa (riesgo alto) y de espectáculos"],
             ["Autorización sanitaria", "DIRESA Amazonas para la piscina; municipalidad para el restaurante"]]
    E.append(tabla(filas, [62, 112]))

    # ---------------- 11. Presupuesto
    E.append(PageBreak())
    E.append(P("11. Presupuesto referencial", "h1"))
    E.append(P(
        "Metrados tomados de la geometría del proyecto y precios unitarios con IGV puestos en Mendoza (sondeo de noviembre "
        "de 2026, a validar con cotizaciones locales). Incluye gastos generales y utilidad del contratista sobre la obra, "
        "expediente técnico y licencias, e imprevistos. No incluye el terreno, las conexiones domiciliarias ni el capital "
        "de trabajo. El detalle con fórmulas está en <i>Presupuesto_Polleria_Campestre.xlsx</i>."))
    filas = [["Capítulo", "S/"]]
    for cap, val in e1["capitulos"]:
        filas.append([cap[3:].capitalize(), f"{val:,.0f}"])
    filas += [["Gastos generales y utilidad (12 % de la obra)", f"{e1['gg']:,.0f}"],
              ["Expediente técnico, licencia e ITSE", f"{e1['expediente']:,.0f}"],
              ["Imprevistos (8 %)", f"{e1['imprevistos']:,.0f}"],
              ["TOTAL 1.ª ETAPA (con IGV)", f"{e1['total']:,.0f}"]]
    E.append(P("1.ª etapa: pollería, edificio y jardines", "h2"))
    E.append(tabla(filas, [130, 44], negrita_ultima=True, alinear_der=(1,)))
    filas = [["Capítulo", "S/"]]
    for cap, val in e2["capitulos"]:
        filas.append([cap[3:].capitalize(), f"{val:,.0f}"])
    filas += [["Gastos generales, autorizaciones e imprevistos", f"{e2['gg'] + e2['expediente'] + e2['imprevistos']:,.0f}"],
              ["TOTAL 2.ª ETAPA (con IGV)", f"{e2['total']:,.0f}"]]
    E.append(P("2.ª etapa: piscina, vestidores y relajo", "h2"))
    E.append(tabla(filas, [130, 44], negrita_ultima=True, alinear_der=(1,)))
    E.append(Spacer(1, 2 * mm))
    E.append(P(
        f"Costo de la 1.ª etapa por m² techado: {S(e1['total'] / area_techada)} (incluye equipamiento de cocina, ascensor, "
        "mobiliario y obras exteriores). Las partidas de mayor peso son la estructura metálica, el equipamiento de cocina y "
        "bar, las instalaciones y el ascensor; un ascensor hidráulico o una plataforma más simple, o diferir parte del "
        "mobiliario, son las palancas para ajustar la inversión inicial."))

    # ---------------- 12. Próximos pasos
    E.append(P("12. Próximos pasos", "h1"))
    E += bullets([
        "Levantamiento topográfico del lote (linderos, niveles y diagonales) y verificación de las estructuras existentes.",
        "Certificado de parámetros urbanísticos: uso permitido, retiros, altura máxima y estacionamientos exigidos.",
        "Estudio de mecánica de suelos y confirmación de la zona sísmica con la E.030 vigente.",
        "Proyecto de especialidades: arquitectura, estructuras, instalaciones eléctricas, sanitarias, GLP, seguridad y "
        "evacuación; luego licencia de edificación (modalidad C) e ITSE.",
        "Cotizaciones locales de estructura metálica, hornos, campana, ascensor y sombrillas para cerrar el presupuesto.",
    ])
    E.append(Spacer(1, 3 * mm))
    E.append(P("Láminas del anteproyecto: A-01 y A-02 planimetría por etapas; A-03 circulaciones y evacuación; A-04 "
               "sombrillas removibles; A-05 y A-06 plantas del edificio; A-07 cortes y elevaciones; A-08 piscina; E-01 "
               "cimentación; E-02 estructura metálica.", "small"))

    doc.build(E, onFirstPage=_pie, onLaterPages=_pie)
    return ruta_pdf


if __name__ == "__main__":
    salida = os.path.join(AQUI, "salida")
    print(generar(os.path.join(salida, "Memoria_Descriptiva_Polleria_Campestre.pdf"),
                  os.path.join(salida, "vistas_previas"),
                  os.path.join(AQUI, "salida", "_tmp_memoria")))
