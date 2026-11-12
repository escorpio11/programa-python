# -*- coding: utf-8 -*-
"""Memoria descriptiva del proyecto AZOTEA GYM -> PDF (reportlab)."""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether

import diseno as D
from laminas import metrados
from presupuesto import totales, SUPUESTOS_NEGOCIO, CRONOGRAMA, IMPREVISTOS

AQUI = os.path.dirname(os.path.abspath(__file__))
SALIDA = os.path.join(AQUI, "salida")
ROJO, TINTA, GRIS = colors.HexColor("#C4181F"), colors.HexColor("#17181B"), colors.HexColor("#5E626B")
E = {
    "t": ParagraphStyle("t", fontName="Helvetica-Bold", fontSize=26, leading=30, textColor=TINTA),
    "s": ParagraphStyle("s", fontName="Helvetica", fontSize=11, leading=15, textColor=GRIS),
    "h": ParagraphStyle("h", fontName="Helvetica-Bold", fontSize=13, leading=17, textColor=ROJO, spaceBefore=12, spaceAfter=5),
    "p": ParagraphStyle("p", fontName="Helvetica", fontSize=9.6, leading=13.6, textColor=TINTA, spaceAfter=5, alignment=4),
    "b": ParagraphStyle("b", fontName="Helvetica", fontSize=9.6, leading=13.4, textColor=TINTA, leftIndent=11, bulletIndent=2, spaceAfter=2),
    "n": ParagraphStyle("n", fontName="Helvetica-Oblique", fontSize=8.4, leading=11.5, textColor=GRIS, spaceAfter=4),
    "c": ParagraphStyle("c", fontName="Helvetica", fontSize=8.2, leading=10.4, textColor=TINTA),
    "cb": ParagraphStyle("cb", fontName="Helvetica-Bold", fontSize=8.2, leading=10.4, textColor=colors.white),
}
S = lambda v: "S/ {:,}".format(int(round(v)))


def tabla(filas, anchos, cab=True, der=()):
    datos = [[Paragraph(str(c), E["cb"] if (cab and i == 0) else E["c"]) for c in f] for i, f in enumerate(filas)]
    t = Table(datos, colWidths=[a * mm for a in anchos], repeatRows=1 if cab else 0)
    est = [("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#C9CBD0")), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
           ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F3F1")]), ("TOPPADDING", (0, 0), (-1, -1), 2.6), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.6)]
    if cab:
        est.append(("BACKGROUND", (0, 0), (-1, 0), TINTA))
    t.setStyle(TableStyle(est))
    return t


def pie(c, doc):
    c.saveState(); c.setFont("Helvetica", 7.5); c.setFillColor(GRIS)
    c.drawString(20 * mm, 11 * mm, "AZOTEA GYM · Memoria descriptiva · Huambo, Rodríguez de Mendoza, Amazonas · Noviembre 2026")
    c.drawRightString(190 * mm, 11 * mm, "Pág. %d" % doc.page); c.setStrokeColor(ROJO); c.setLineWidth(1.2); c.line(20 * mm, 15 * mm, 190 * mm, 15 * mm); c.restoreState()


def generar():
    ar, me, t = D.areas(), metrados(), totales()
    N = SUPUESTOS_NEGOCIO
    ruta = os.path.join(SALIDA, "Memoria_Descriptiva_Azotea_Gym.pdf")
    doc = SimpleDocTemplate(ruta, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm, topMargin=18 * mm, bottomMargin=20 * mm, title="Azotea Gym - Memoria descriptiva", author="Proyecto Azotea Gym")
    P = lambda x: Paragraph(x, E["p"]); H = lambda x: Paragraph(x, E["h"]); B = lambda x: Paragraph(x, E["b"], bulletText="•"); F = []
    F += [Paragraph("AZOTEA GYM", E["t"]), Paragraph("Memoria descriptiva del gimnasio en azotea · Jr. San Miguel, Huambo, Rodríguez de Mendoza, Amazonas · Noviembre 2026", E["s"]), Spacer(1, 6)]
    img = os.path.join(SALIDA, "vistas_3d", "01_aerea_general.jpg")
    if os.path.exists(img):
        F += [Image(img, width=170 * mm, height=95.6 * mm), Spacer(1, 4)]
    F += [H("1. Resumen"),
          P("El proyecto convierte la azotea techada de la casa (%.1f m²) en un gimnasio de fuerza con <b>13 máquinas</b> de uso comercial, <b>recepción con 12 lockers</b>, zona funcional y los "
            "<b>dos baños con ducha ya construidos</b>. No se demuele nada: se conservan el lavadero, el tanque elevado de 1 100 L y los dos tragaluces, que no se cubren. "
            "La sala útil es de %.1f m², las máquinas ocupan %.1f m² (%d %%) y el aforo simultáneo recomendado es de <b>%d personas</b>." % (ar["techada"], ar["sala"], ar["huella_maquinas"], ar["ocupacion"], ar["aforo"])),
          P("La inversión referencial es de <b>%s</b> con IGV: %s en máquinas a precio de catálogo, %s en accesorios de peso libre, %s en transporte, izaje y armado, y el resto en obras, acabados, permisos e imprevistos. "
            "Con los supuestos de partida, el punto de equilibrio es de <b>%d socios</b>." % (S(t["total"]), S(t["maquinas"]), S(t["capitulos"][1][1]), S(t["capitulos"][2][1]), t["equilibrio"])),
          H("2. Información de base y medidas"),
          B("<b>Plano de distribución de máquinas «Azotea Gym»</b> (agosto 2026): base general de 14.62 × 6.65 m, vigas y ubicación de las máquinas."),
          B("<b>A-01 modif. «SS.HH. y zona de servicio — medidas de obra»</b> (noviembre 2026): baños construidos (SS.HH. 1 + ducha, 2.83 m²; SS.HH. 2, 1.86 m²), tanque TQ-1 sobre plataforma, lavadero y tragaluces E y SO."),
          B("<b>Techo metálico Casa de Huambo</b> (julio 2024): cerchas principales en ejes 7, 5, 3 y 1; alturas de 2.80 a 2.40 m; calamina translúcida prevista sobre los tragaluces."),
          B("<b>Catálogo 2026 Fitness Extreme</b>: dimensiones y precios de los equipos."),
          P("<b>Diferencia detectada.</b> El baño construido mide 3.70 m interiores y el plano base indica 3.35 m; el plano de techo acota luces de 4.73 / 4.87 / 3.52 / 1.26 m, mayores que las del plano base. "
            "La azotea real sería entre 0.35 y 0.85 m más larga. El modelo respeta la medida de obra del baño y desplaza 0.35 m lo que queda a su derecha (largo de %.2f m): es el caso más ajustado, de modo que si la medida real es mayor sobra holgura. "
            "La lámina V-01 lista las ocho medidas y cuatro alturas a confirmar con wincha antes del replanteo." % D.L),
          H("3. Criterios de diseño"),
          B("Respetar el plano de distribución: las diez máquinas de la sala este conservan su ubicación, con los equipos pesados sobre las vigas de los ejes."),
          B("Reorganizar solo la sala oeste, afectada por los baños construidos: press plano, hip thrust y dominadas se reubican para liberar el frente de las puertas P-1 y P-2, el lavadero y el hall de llegada."),
          B("Punto de recepción junto a la llegada de la escalera, con control visual de toda la sala."),
          B("Pasos principales de 1.10 m o más; acceso lateral a máquinas de 0.55 m o más; barras olímpicas con 0.45 a 0.60 m libres en cada extremo."),
          B("Equipos de más de 2.20 m (crossover y dominadas) donde el techo tiene al menos 2.48 m libres."),
          B("Tragaluces siempre despejados, protegidos contra caídas y aprovechados como fuente de luz natural.")]
    F += [H("4. Distribución y equipamiento")]
    filas = [["N.º", "Equipo", "Alto × ancho × largo (catálogo)", "Zona", "Precio"]] + [[int(m["id"][1:]), m["nombre"], m["dim_cat"], D.ZONAS[m["zona"]]["nombre"], S(m["precio"])] for m in D.MAQUINAS]
    F += [tabla(filas, [10, 48, 58, 30, 24]), Spacer(1, 3), Paragraph("Accesorios mínimos para operar: " + "; ".join("%s (%s %s)" % (d, ("%g" % q), u) for d, u, q, pu, r in D.ACCESORIOS) + ".", E["n"])]
    F += [H("5. Recepción, lockers y vestíbulo de servicios"),
          P("El <b>mostrador</b> (1.50 × 0.50 m, alto 1.05 m) queda perpendicular al muro, pegado a la llegada de la escalera: quien sube lo tiene a su derecha y pasa frente a él. "
            "A su espalda, un <b>panel de marca</b> de 1.50 × 2.30 m con logo retroiluminado separa la recepción de los <b>12 lockers</b> (0.30 × 0.60 × 0.42 m), que abren hacia el vestíbulo de servicios junto con una banca. "
            "El hall libre frente al mostrador mide 1.53 m y el frente de los baños 2.47 m."),
          P("El <b>muro sur del tragaluz E y de la escalera</b> se completa con policarbonato opal de +1.00 a +2.40 m («muro de luz»): protege la caída, deja pasar la luz del tragaluz a la recepción y no lo tapa. "
            "El <b>tragaluz SO</b>, bajo la plataforma del tanque, recibe una malla anticaída. Una <b>celosía de listones</b> de 2.20 m oculta el tanque y el lavadero desde la sala; el lavadero conserva su acceso y sirve de estación de limpieza."),
          H("6. Pisos, cerramiento y acabados")]
    c = me["cerramiento"]
    F += [tabla([["Acabado", "Ubicación", "Metrado"],
                 ["Caucho reciclado 15 mm en losetas de 1 × 1 m", "Sala de máquinas", "%.1f m²" % me["caucho15"]], ["Caucho reciclado 25 mm", "Peso libre", "%.1f m²" % me["caucho_pl"]],
                 ["Piso vinílico SPC tono madera", "Recepción y vestíbulo", "%.1f m²" % me["vinilico"]], ["Grass sintético deportivo", "Zona funcional", "%.1f m²" % me["grass"]],
                 ["Policarbonato alveolar 8 mm con estructura de tubo", "Lado B, lado mercado y fondo", "%.1f m²" % c.get("policarbonato", 0)], ["Ventanal transparente", "Lado calle", "%.1f m²" % c.get("ventanal", 0)],
                 ["Panel de fibrocemento con espejos (4.00 × 1.80 m)", "Fondo, peso libre", "%.1f m²" % c.get("panel_espejo", 0)], ["Lamas metálicas de ventilación", "Franja superior perimetral", "%.1f m²" % c.get("lamas", 0)]], [84, 60, 26]),
          Spacer(1, 3), P("El caucho se coloca flotante sobre la losa limpia: la protege y reduce el ruido de impacto hacia el piso inferior. El cerramiento se apoya en el parapeto existente de 1.00 m; "
                          "si la azotea ya cuenta con cerramiento, esa partida se descuenta."),
          H("7. Instalaciones eléctricas, iluminación y ventilación"),
          P("%d luminarias LED lineales de 40 W colgadas de las cerchas secundarias (≈ %d lux medios; lo recomendado para gimnasios es 300 lux), %d tomacorrientes dobles con tierra, %d luces de emergencia, "
            "%d ventiladores de pared y tiras LED de acento. Cinco circuitos con interruptores termomagnéticos e interruptor diferencial de 30 mA; potencia instalada de unos 3.2 kW. "
            "Debe verificarse la capacidad del tablero existente y la puesta a tierra." % (len(D.LUMINARIAS), len(D.LUMINARIAS) * 4000 * 0.55 / ar["sala"], len(D.TOMACORRIENTES), len(D.LUCES_EMERGENCIA), len(D.VENTILADORES))),
          H("8. Estructura y cargas")]
    car = D.cargas(); tot = sum(x[2] for x in car); prom = (tot + ar["aforo"] * 80 + ar["sala"] * 20) / ar["sala"]
    F += [P("Los equipos con su carga máxima suman unos <b>{:,} kg</b> (pesos estimados, a confirmar con el fabricante). Con {} personas y el piso de caucho, la carga media sobre la sala es de unos <b>{:.0f} kg/m²</b>. "
            "Sin embargo, las máquinas concentran peso y el uso es dinámico: la Norma E.020 fija para gimnasios una sobrecarga de <b>400 kgf/m²</b>, mientras que una losa de vivienda suele diseñarse para 200 kgf/m². "
            "<b>Antes de comprar los equipos, un ingeniero civil colegiado debe evaluar la losa y las vigas del último techo</b> y, si corresponde, indicar refuerzo o restricciones.".format(tot, ar["aforo"], prom)),
          B("Los equipos más pesados (prensa, crossover, hip thrust, extensión, aductor) quedan sobre las vigas de los ejes 6, 4, 3, 2 y 1, como en el plano base."),
          B("La franja entre los ejes D y F (junto al muro del fondo) podría ser un volado: allí solo se ubican cargas livianas (mancuernero, porta barras)."),
          B("Queda prohibido soltar pesas; el peso muerto solo sobre plataforma amortiguada."),
          B("Las máquinas grandes suben a la azotea por fuera, con polea o andamio: la llegada de la escalera mide 0.97 m."),
          H("9. Seguridad"),
          P("La azotea tiene una sola salida, la escalera: el aforo máximo recomendado es de %d personas y el recorrido de evacuación más largo es de unos 17 m (menor que 45 m, RNE A.130). "
            "Se prevén %d extintores PQS de 6 kg, luces de emergencia sobre la ruta, señalética de salida, aforo y riesgo eléctrico, botiquín y una puerta-reja en la llegada de la escalera para cerrar el local fuera de horario. "
            "Corresponde tramitar la ITSE y la licencia de funcionamiento ante la municipalidad." % (ar["aforo"], len(D.EXTINTORES))),
          H("10. Presupuesto referencial")]
    filas = [["Capítulo", "Monto"]] + [[n.capitalize(), S(v)] for n, v in t["capitulos"]] + [["Imprevistos sobre obras (%d %%)" % (IMPREVISTOS * 100), S(t["imprevistos"])], ["<b>INVERSIÓN TOTAL (con IGV)</b>", "<b>%s</b>" % S(t["total"])]]
    F += [tabla(filas, [130, 40]), Spacer(1, 3),
          Paragraph("Etapa 1 (apertura): %s. Etapa 2 (mejoras: grass, sonido, celosía, mural, implementos): %s. Máquinas a precio del catálogo; el resto son precios referenciales por cotizar; el flete Lima–Huambo es un estimado." % (S(t["etapa1"]), S(t["etapa2"])), E["n"]),
          H("11. Recuperación de la inversión (modelo con supuestos)"),
          P("Supuestos de partida, <b>por validar en Huambo</b> (no son datos de mercado): mensualidad de S/ %d, S/ %d de ingreso extra por socio al mes y %s de costos fijos mensuales con una persona contratada. "
            "Con ellos, el punto de equilibrio es de <b>%d socios</b>." % (N["mensualidad"], N["extra_por_socio"], S(t["costos_fijos"]), t["equilibrio"])),
          tabla([["Escenario", "Socios", "Ingreso mensual", "Utilidad mensual", "Recuperación"]] + [[n, s, S(i), S(u), ("%.0f meses (%.1f años)" % (m, m / 12)) if m else "no se recupera"] for n, s, i, u, m in t["escenarios"]], [34, 20, 36, 36, 44]),
          Spacer(1, 3), Paragraph("La sala admite %d personas a la vez; con siete franjas útiles al día atiende a unos 150 socios que asisten cuatro veces por semana. El Excel recalcula todo al cambiar los supuestos." % ar["aforo"], E["n"]),
          H("12. Cronograma"),
          tabla([["Actividad", "Semanas"]] + [[a, ("%d" % i) if d == 1 else ("%d a %d" % (i, i + d - 1))] for a, i, d in CRONOGRAMA], [140, 30]),
          H("13. Verificaciones previas y pendientes"),
          B("Medir la azotea con wincha según la lámina V-01 y actualizar el modelo si alguna medida difiere."),
          B("Evaluación estructural de losa y vigas (numeral 8)."),
          B("Confirmar 2.35 m o más bajo la cercha del eje 2 para el crossover de 2.30 m; si no, pedirlo con altura reducida."),
          B("Confirmar si ya existe cerramiento sobre el parapeto y el estado del tablero eléctrico."),
          B("Cotizar con el proveedor el flete a Huambo, el plazo de fabricación y las dimensiones de los equipos sin dato en el catálogo (mancuernero y bancos)."),
          H("14. Documentos del proyecto"),
          P("Planos (9 láminas A3): A-01 distribución, A-02 cotas y evacuación, A-03 comparativo, A-04 recepción, A-05 cortes, A-06 acabados, IE-01 eléctricas, E-01 cargas, V-01 verificación de medidas. "
            "Planta en DXF para AutoCAD. Presupuesto en Excel con fórmulas, recuperación y cronograma. 14 vistas 3D, video de recorrido y presentación. Todo se regenera con <i>python3 generar.py</i>.")]
    doc.build(F, onFirstPage=pie, onLaterPages=pie)
    return ruta


if __name__ == "__main__":
    print(generar())
