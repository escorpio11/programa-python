# -*- coding: utf-8 -*-
"""Presupuesto referencial, modelo de recuperación y cronograma -> Excel con fórmulas."""
import os
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

import diseno as D
from laminas import metrados

AQUI = os.path.dirname(os.path.abspath(__file__))
SALIDA = D.SALIDA
B = D.VERSION == "B"
IMPREVISTOS = 0.08


def partidas():
    """[(capítulo, es_obra, [(descripción, und, metrado, P.U., etapa, nota)])]"""
    me = metrados(); c = me["cerramiento"]; ar = D.areas()
    maq = [("%s  (%s)" % (m["nombre"], m["dim_cat"]), "und", 1, m["precio"], 1, "Catálogo Fitness Extreme 2026, " + m["cat"]) for m in D.MAQUINAS]
    acc = [(d, u, q, pu, 1, "Catálogo, " + ref) for d, u, q, pu, ref in D.ACCESORIOS]
    return [
        ("MÁQUINAS (precios de catálogo)", False, maq),
        ("ACCESORIOS DE PESO LIBRE", False, acc),
        ("TRANSPORTE, IZAJE Y ARMADO", False, [
            ("Flete Lima – Huambo (camión, ≈ %s t de equipos)" % ("4.2" if B else "3.5"), "glb", 1, 5300 if B else 4500, 1, "Estimado: cotizar con el proveedor"),
            ("Izaje de equipos a la azotea (polea o andamio desde la calle)", "glb", 1, 900, 1, "La escalera mide 0.97 m: equipos grandes suben por fuera"),
            ("Armado, nivelación y prueba de máquinas", "glb", 1, 1200 if B else 1000, 1, "Gratis solo en Lima según catálogo"),
        ]),
        ("PISOS", True, [
            ("Limpieza y nivelación puntual de losa", "m²", ar["sala"], 8, 1, ""),
            ("Caucho reciclado 15 mm, losetas 1 x 1 m (sala de máquinas)", "m²", me["caucho15"], 95, 1, "Instalado"),
            ("Caucho reciclado 25 mm (peso libre)", "m²", me["caucho_pl"], 145, 1, "Instalado"),
            ("Piso vinílico SPC tono madera (recepción y vestíbulo)", "m²", me["vinilico"], 75, 1, "Instalado"),
        ] + ([("Caucho reciclado 25 mm bajo cintas de correr (base antivibratoria)", "m²", me["caucho_cardio"], 145, 1, "Instalado")] if me["caucho_cardio"] else [])
          + ([("Grass sintético deportivo 12 mm (zona funcional)", "m²", me["grass"], 55, 2, "Instalado")] if me["grass"] else [])),
        ("RECEPCIÓN Y MOBILIARIO", True, [
            ("Mostrador %.2f x 0.50 x 1.05 m, melamina y frente de listones" % (D.RECEPCION["mostrador"][3] - D.RECEPCION["mostrador"][1]), "und", 1, 1600 if B else 1800, 1, "Carpintería local"),
            ("Panel de marca %.2f x 2.30 m con logo retroiluminado" % (D.RECEPCION["panel_marca"][3] - D.RECEPCION["panel_marca"][1]), "und", 1, 1450 if B else 1600, 1, "Bastidor metálico + MDF + vinil + LED"),
            ("Lockers metálicos de 12 casilleros (0.30 x 0.60 x 0.42 m)", "jgo", 1, 1900, 1, ""),
            ("Estante de productos 0.83 x 0.28 x 1.90 m", "und", 1, 450, 1, ""),
            ("Banca de listones 0.80 x 0.38 m", "und", 1, 350, 1, ""),
            ("Taburete alto para recepción", "und", 1, 180, 1, ""),
            ("Dispensador de agua con bidón", "und", 1, 450, 2, ""),
            ("Felpudo de ingreso", "und", 1, 120, 1, ""),
        ]),
        ("CERRAMIENTO Y CARPINTERÍA METÁLICA", True, [
            ("Policarbonato alveolar 8 mm con estructura de tubo 50 x 50", "m²", c.get("policarbonato", 0), 165, 1, "Lado B, mercado y fondo. Descontar si ya existe"),
            ("Ventanal transparente %s (policarbonato compacto 4 mm)" % ("lado calle y esquina de cardio" if B else "lado calle"), "m²", c.get("ventanal", 0), 290, 1, "Con vidrio templado 6 mm: ≈ S/ 420/m²"),
            ("Panel de fibrocemento 8 mm con estructura (pared de espejos)", "m²", c.get("panel_espejo", 0), 140, 1, ""),
            ("Lamas metálicas de ventilación (franja superior)", "m²", c.get("lamas", 0), 150, 1, ""),
            ("Muro de luz: policarbonato opal 8 mm sobre muro del tragaluz E", "m²", c.get("muro_luz", 0), 175, 1, "De +1.00 a +2.40"),
            ("Panel con mural en muro este de la escalera", "m²", c.get("panel", 0), 140, 1, ""),
            ("Puerta-reja con chapa en la llegada de la escalera", "und", 1, 950, 1, "Cierre del gimnasio fuera de horario"),
            ("Malla anticaída del tragaluz SO y protección del tragaluz E", "glb", 1, 650, 1, "Seguridad: no se cubren los tragaluces"),
            ("Celosía de listones de madera (tanque, tragaluz SO y lavadero)", "m²", me["celosia"], 160, 2, ""),
        ]),
        ("ESPEJOS", True, [
            ("Espejo 4 mm con lámina de seguridad, 4.00 x 1.80 m", "m²", me["espejos"], 150, 1, "En 4 paños de 1.00 m"),
            ("Tablero de respaldo MDF 18 mm", "m²", round(me["espejos"] + 0.4, 1), 60, 1, ""),
        ]),
        ("INSTALACIONES ELÉCTRICAS, VENTILACIÓN Y SONIDO", True, [
            ("Luminaria LED lineal 40 W, 4000 K, con suspensión", "und", len(D.LUMINARIAS), 75, 1, ""),
            ("Tablero, cableado, tubería y mano de obra (5 circuitos)", "glb", 1, 2400, 1, "Con interruptor diferencial 30 mA"),
        ] + ([("Circuito independiente para cinta de correr (4 mm², ITM 20 A, toma dedicada)", "und", 2, 450, 1, "Uno por cinta"),
              ("Refuerzo del alimentador y del tablero general (10 mm²)", "glb", 1, 700, 1, "Confirmar potencia contratada con la concesionaria")] if B else []) + [
            ("Tomacorriente doble con línea a tierra", "und", len(D.TOMACORRIENTES), 85, 1, ""),
            ("Luz de emergencia LED", "und", len(D.LUCES_EMERGENCIA), 95, 1, ""),
            ("Tiras LED de acento con fuentes (≈ 30 m)", "glb", 1, 600, 2, ""),
            ("Ventilador industrial de pared 20\"", "und", len(D.VENTILADORES), 320, 1, ""),
            ("Equipo de sonido: amplificador y 3 parlantes", "glb", 1, 1300, 2, ""),
        ]),
        ("SEGURIDAD Y SEÑALÉTICA", True, [
            ("Extintor PQS 6 kg con soporte y señal", "und", len(D.EXTINTORES), 130, 1, ""),
            ("Botiquín de primeros auxilios", "und", 1, 150, 1, ""),
            ("Señalética de seguridad (salida, aforo, riesgo eléctrico, extintor)", "glb", 1, 350, 1, ""),
            ("Letreros colgantes de zona", "und", 5, 90, 2, ""),
        ]),
        ("PINTURA Y MARCA", True, [
            ("Pintura de parapetos, columnas y carpintería", "m²", me["pintura"], 18, 1, "Látex gris oscuro / esmalte negro"),
            ("Mural y rotulación de marca (vinil)", "glb", 1, 700, 2, ""),
            ("Plantas y decoración", "glb", 1, 250, 2, ""),
        ]),
        (("ESTIRAMIENTO (implementos)", True, [
            ("Colchonetas 1.75 x 0.60 m con soporte de pared", "und", 4, 75, 2, "Se usan frente al crossover fuera de la hora punta"),
            ("Rodillo y bandas elásticas", "jgo", 1, 180, 2, ""),
        ]) if B else ("ZONA FUNCIONAL (implementos)", True, [
            ("Colchonetas 1.75 x 0.60 m", "und", 4, 60, 2, ""),
            ("Juego de 3 pesas rusas (8, 12 y 16 kg)", "jgo", 1, 350, 2, ""),
            ("Cajón pliométrico de madera", "und", 1, 280, 2, ""),
            ("Pelota, rodillo y bandas elásticas", "jgo", 1, 260, 2, ""),
        ])),
        ("ESTUDIOS Y PERMISOS", False, [
            ("Evaluación estructural de losa y vigas (ingeniero civil colegiado)", "glb", 1, 1500, 1, "Obligatoria antes de comprar"),
            ("ITSE y licencia de funcionamiento municipal", "glb", 1, 600, 1, "Estimado: confirmar en la municipalidad"),
        ]),
    ]


SUPUESTOS_NEGOCIO = {
    "mensualidad": 70, "extra_por_socio": 6,
    "escenarios": [("Conservador", 45), ("Base", 80), ("Optimista", 110)],
    "costos": [("Personal (recepción / instructor)", 1300), ("Electricidad", 400 if B else 280), ("Agua", 90), ("Limpieza e insumos", 150),
               ("Mantenimiento de equipos", 260 if B else 200), ("Internet y sistema de control", 90), ("Publicidad local", 120), ("Varios", 150)],
}


def totales():
    P = partidas(); caps = []; e1 = e2 = obra = 0.0
    for nombre, es_obra, items in P:
        t = sum(q * pu for _, _, q, pu, _, _ in items); caps.append((nombre, round(t)))
        e1 += sum(q * pu for _, _, q, pu, e, _ in items if e == 1); e2 += sum(q * pu for _, _, q, pu, e, _ in items if e == 2)
        if es_obra:
            obra += t
    imp = obra * IMPREVISTOS; sub = sum(t for _, t in caps)
    N = SUPUESTOS_NEGOCIO; cf = sum(v for _, v in N["costos"]); ing = N["mensualidad"] + N["extra_por_socio"]
    total = sub + imp
    esc = [(n, s, s * ing, s * ing - cf, (total / (s * ing - cf)) if s * ing > cf else None) for n, s in N["escenarios"]]
    return {"capitulos": caps, "subtotal": round(sub), "imprevistos": round(imp), "total": round(total), "etapa1": round(e1 + imp * e1 / (e1 + e2)), "etapa2": round(e2 + imp * e2 / (e1 + e2)),
            "maquinas": caps[0][1], "equipamiento": caps[0][1] + caps[1][1] + caps[2][1], "obras": round(obra + imp),
            "costos_fijos": cf, "ingreso_por_socio": ing, "equilibrio": int(-(-cf // ing)), "escenarios": esc}


CRONOGRAMA = [  # (actividad, semana inicio, duración en semanas)
    ("Verificación de medidas (V-01) y evaluación estructural", 1, 1),
    ("Pedido de máquinas (fabricación)", 1, 4),
    ("Cerramiento metálico, puerta-reja y protección de tragaluces", 2, 2),
    ("Instalaciones eléctricas, luminarias y ventiladores", 2, 2),
    ("Pintura, panel de espejos y muro de luz", 3, 1),
    ("Pisos de caucho, vinílico y grass", 4, 1),
    ("Recepción, lockers, celosías y rotulación", 4, 1),
    ("Flete, izaje y armado de máquinas", 5, 1),
    ("Señalética, pruebas, ITSE y apertura", 6, 1),
]


def generar():
    os.makedirs(SALIDA, exist_ok=True)
    wb = Workbook()
    negro, rojo, gris = "17181B", "D81F26", "F3F3F1"
    b = Side(style="thin", color="C9CBD0"); borde = Border(left=b, right=b, top=b, bottom=b)
    f_tit = Font(name="Arial", bold=True, size=14); f_cab = Font(name="Arial", bold=True, color="FFFFFF", size=10); f_n = Font(name="Arial", size=10)
    f_b = Font(name="Arial", bold=True, size=10); f_in = Font(name="Arial", size=10, color="0000FF")
    soles = '"S/" #,##0'; soles2 = '"S/" #,##0.00'

    # ---------------- Presupuesto
    ws = wb.active; ws.title = "Presupuesto"
    ws["A1"] = "AZOTEA GYM%s — Presupuesto referencial (precios con IGV, noviembre 2026)" % (" · VERSIÓN B (con cardio)" if B else ""); ws["A1"].font = f_tit
    ws["A2"] = "Huambo, Rodríguez de Mendoza, Amazonas. Máquinas con precios del Catálogo 2026 Fitness Extreme; el resto son precios referenciales a cotizar."; ws["A2"].font = Font(name="Arial", italic=True, size=9)
    cab = ["Ítem", "Descripción", "Und.", "Metrado", "P. unitario", "Parcial", "Etapa", "Referencia / nota"]
    for i, c in enumerate(cab, 1):
        x = ws.cell(row=4, column=i, value=c); x.font = f_cab; x.fill = PatternFill("solid", fgColor=negro); x.alignment = Alignment(horizontal="center", vertical="center"); x.border = borde
    r = 5; filas_cap = []; filas_obra = []; ini_datos = 5
    for k, (nombre, es_obra, items) in enumerate(partidas(), 1):
        ws.cell(row=r, column=1, value=k).font = f_b; ws.cell(row=r, column=2, value=nombre).font = f_b
        for cc in range(1, 9):
            ws.cell(row=r, column=cc).fill = PatternFill("solid", fgColor=gris); ws.cell(row=r, column=cc).border = borde
        fila_cap = r; r += 1; r0 = r
        for j, (d, u, q, pu, et, nota) in enumerate(items, 1):
            vals = ["%d.%02d" % (k, j), d, u, q, pu, "=D%d*E%d" % (r, r), et, nota]
            for cc, v in enumerate(vals, 1):
                x = ws.cell(row=r, column=cc, value=v); x.font = f_in if cc in (4, 5) else f_n; x.border = borde
                if cc == 5:
                    x.number_format = soles2
                if cc == 6:
                    x.number_format = soles
                if cc in (1, 3, 7):
                    x.alignment = Alignment(horizontal="center")
                if cc in (2, 8):
                    x.alignment = Alignment(wrap_text=True, vertical="top")
            r += 1
        x = ws.cell(row=fila_cap, column=6, value="=SUM(F%d:F%d)" % (r0, r - 1)); x.font = f_b; x.number_format = soles
        filas_cap.append((nombre, fila_cap));
        if es_obra:
            filas_obra.append(fila_cap)
    fin_datos = r - 1
    r += 1
    ws.cell(row=r, column=2, value="SUBTOTAL").font = f_b; x = ws.cell(row=r, column=6, value="=" + "+".join("F%d" % f for _, f in filas_cap)); x.font = f_b; x.number_format = soles; f_sub = r; r += 1
    ws.cell(row=r, column=2, value="Imprevistos sobre obras y acabados").font = f_n; x = ws.cell(row=r, column=5, value=IMPREVISTOS); x.number_format = "0%"; x.font = f_in
    x = ws.cell(row=r, column=6, value="=E%d*(%s)" % (r, "+".join("F%d" % f for f in filas_obra))); x.number_format = soles; f_imp = r; r += 1
    ws.cell(row=r, column=2, value="INVERSIÓN TOTAL").font = Font(name="Arial", bold=True, size=12, color=rojo)
    x = ws.cell(row=r, column=6, value="=F%d+F%d" % (f_sub, f_imp)); x.font = Font(name="Arial", bold=True, size=12, color=rojo); x.number_format = soles; f_tot = r; r += 2
    ws.cell(row=r, column=2, value="Etapa 1 — apertura (sin imprevistos)").font = f_n
    ws.cell(row=r, column=6, value='=SUMIF(G%d:G%d,1,F%d:F%d)' % (ini_datos, fin_datos, ini_datos, fin_datos)).number_format = soles; f_e1 = r; r += 1
    ws.cell(row=r, column=2, value="Etapa 2 — mejoras (sin imprevistos)").font = f_n
    ws.cell(row=r, column=6, value='=SUMIF(G%d:G%d,2,F%d:F%d)' % (ini_datos, fin_datos, ini_datos, fin_datos)).number_format = soles; r += 2
    ws.cell(row=r, column=2, value="Celdas en azul = datos editables (metrado y precio unitario). Las partidas de cerramiento se descuentan si ya existe cerramiento sobre el parapeto.").font = Font(name="Arial", italic=True, size=9)
    for col, w in zip("ABCDEFGH", (7, 64, 7, 10, 13, 14, 8, 52)):
        ws.column_dimensions[col].width = w
    ws.freeze_panes = "A5"

    # ---------------- Resumen
    rs = wb.create_sheet("Resumen"); rs["A1"] = "AZOTEA GYM — Resumen de inversión"; rs["A1"].font = f_tit
    for i, c in enumerate(["Capítulo", "Monto", "% del total"], 1):
        x = rs.cell(row=3, column=i, value=c); x.font = f_cab; x.fill = PatternFill("solid", fgColor=negro); x.border = borde
    rr = 4
    for nombre, fila in filas_cap:
        rs.cell(row=rr, column=1, value=nombre).font = f_n; x = rs.cell(row=rr, column=2, value="=Presupuesto!F%d" % fila); x.number_format = soles
        rs.cell(row=rr, column=3, value="=B%d/$B$%d" % (rr, 4 + len(filas_cap) + 1)).number_format = "0.0%"
        for cc in (1, 2, 3):
            rs.cell(row=rr, column=cc).border = borde
        rr += 1
    rs.cell(row=rr, column=1, value="Imprevistos (obras)").font = f_n; rs.cell(row=rr, column=2, value="=Presupuesto!F%d" % f_imp).number_format = soles; rr += 1
    rs.cell(row=rr, column=1, value="INVERSIÓN TOTAL").font = Font(name="Arial", bold=True, size=12, color=rojo)
    x = rs.cell(row=rr, column=2, value="=Presupuesto!F%d" % f_tot); x.number_format = soles; x.font = Font(name="Arial", bold=True, size=12, color=rojo); fila_total_res = rr
    rs.column_dimensions["A"].width = 52; rs.column_dimensions["B"].width = 16; rs.column_dimensions["C"].width = 12

    # ---------------- Recuperación
    N = SUPUESTOS_NEGOCIO
    rn = wb.create_sheet("Recuperación"); rn["A1"] = "AZOTEA GYM — ¿En cuánto tiempo se recupera? (modelo simple con supuestos editables)"; rn["A1"].font = f_tit
    rn["A2"] = "Los supuestos en azul NO son datos de mercado: son valores de partida que debes ajustar a la realidad de Huambo."; rn["A2"].font = Font(name="Arial", italic=True, size=9, color=rojo)
    rn["A4"] = "Supuestos de ingreso"; rn["A4"].font = f_b
    rn["A5"] = "Mensualidad por socio (S/)"; rn["B5"] = N["mensualidad"]; rn["B5"].font = f_in; rn["B5"].number_format = soles
    rn["A6"] = "Ingreso extra por socio al mes: bebidas, pases diarios (S/)"; rn["B6"] = N["extra_por_socio"]; rn["B6"].font = f_in; rn["B6"].number_format = soles
    rn["A8"] = "Costos fijos mensuales"; rn["A8"].font = f_b
    r0 = 9
    for i, (c, v) in enumerate(N["costos"]):
        rn.cell(row=r0 + i, column=1, value=c).font = f_n; x = rn.cell(row=r0 + i, column=2, value=v); x.font = f_in; x.number_format = soles
    rf = r0 + len(N["costos"])
    rn.cell(row=rf, column=1, value="Total costos fijos al mes").font = f_b; x = rn.cell(row=rf, column=2, value="=SUM(B%d:B%d)" % (r0, rf - 1)); x.font = f_b; x.number_format = soles
    rn.cell(row=rf + 2, column=1, value="Inversión total (hoja Presupuesto)").font = f_b; x = rn.cell(row=rf + 2, column=2, value="=Resumen!B%d" % fila_total_res); x.number_format = soles; x.font = f_b
    rn.cell(row=rf + 3, column=1, value="Punto de equilibrio (socios que cubren los costos)").font = f_b; x = rn.cell(row=rf + 3, column=2, value="=ROUNDUP(B%d/(B5+B6),0)" % rf); x.font = Font(name="Arial", bold=True, size=11, color=rojo)
    re_ = rf + 5
    for i, c in enumerate(["Escenario", "Socios activos", "Ingreso mensual", "Costos fijos", "Utilidad mensual", "Recuperación (meses)", "Recuperación (años)"], 1):
        x = rn.cell(row=re_, column=i, value=c); x.font = f_cab; x.fill = PatternFill("solid", fgColor=negro); x.border = borde; x.alignment = Alignment(wrap_text=True, horizontal="center")
    for i, (n, s) in enumerate(N["escenarios"], 1):
        q = re_ + i
        rn.cell(row=q, column=1, value=n).font = f_n; x = rn.cell(row=q, column=2, value=s); x.font = f_in
        rn.cell(row=q, column=3, value="=B%d*($B$5+$B$6)" % q).number_format = soles; rn.cell(row=q, column=4, value="=$B$%d" % rf).number_format = soles
        rn.cell(row=q, column=5, value="=C%d-D%d" % (q, q)).number_format = soles
        rn.cell(row=q, column=6, value='=IF(E%d>0,$B$%d/E%d,"no se recupera")' % (q, rf + 2, q)).number_format = "0.0"
        rn.cell(row=q, column=7, value='=IF(E%d>0,F%d/12,"")' % (q, q)).number_format = "0.0"
        for cc in range(1, 8):
            rn.cell(row=q, column=cc).border = borde
    q = re_ + len(N["escenarios"]) + 2
    ar = D.areas()
    notas = ["Aforo simultáneo recomendado: %d personas. Con 7 franjas útiles al día atiende ≈ %d visitas diarias, suficiente para 150 socios que asisten 4 veces por semana." % (ar["aforo"], ar["aforo"] * 7),
             "Si la familia atiende la recepción, el costo de personal baja y la recuperación se acorta.",
             "No incluye impuestos a la renta ni financiamiento. Si la inversión se hace por etapas, usar el monto de la Etapa 1."]
    for i, t in enumerate(notas):
        rn.cell(row=q + i, column=1, value="• " + t).font = Font(name="Arial", size=9)
    rn.column_dimensions["A"].width = 58
    for col in "BCDEFG":
        rn.column_dimensions[col].width = 17

    # ---------------- Cronograma
    cr = wb.create_sheet("Cronograma"); cr["A1"] = "AZOTEA GYM — Cronograma de ejecución (6 semanas)"; cr["A1"].font = f_tit
    cr.cell(row=3, column=1, value="Actividad").font = f_cab; cr.cell(row=3, column=1).fill = PatternFill("solid", fgColor=negro)
    for s in range(1, 7):
        x = cr.cell(row=3, column=1 + s, value="Sem. %d" % s); x.font = f_cab; x.fill = PatternFill("solid", fgColor=negro); x.alignment = Alignment(horizontal="center")
    for i, (act, ini, dur) in enumerate(CRONOGRAMA):
        cr.cell(row=4 + i, column=1, value=act).font = f_n
        for s in range(1, 7):
            x = cr.cell(row=4 + i, column=1 + s); x.border = borde
            if ini <= s < ini + dur:
                x.fill = PatternFill("solid", fgColor=rojo)
    cr.column_dimensions["A"].width = 62
    for s in range(1, 7):
        cr.column_dimensions[get_column_letter(1 + s)].width = 10
    cr.cell(row=5 + len(CRONOGRAMA), column=1, value="La fabricación de las máquinas marca la ruta crítica: confirmar el plazo con el proveedor al hacer el pedido.").font = Font(name="Arial", italic=True, size=9)

    ruta = os.path.join(SALIDA, "Presupuesto_Azotea_Gym%s.xlsx" % D.SUFIJO)
    wb.save(ruta)
    return ruta


if __name__ == "__main__":
    print(generar())
    t = totales()
    for n, v in t["capitulos"]:
        print("  %-52s S/ %9s" % (n, format(v, ",")))
    print("  Imprevistos S/ %s | TOTAL S/ %s | Etapa 1 S/ %s | Etapa 2 S/ %s" % (format(t["imprevistos"], ","), format(t["total"], ","), format(t["etapa1"], ","), format(t["etapa2"], ",")))
    print("  Equilibrio: %d socios | escenarios:" % t["equilibrio"], [(n, s, round(u), None if m is None else round(m, 1)) for n, s, i, u, m in t["escenarios"]])
