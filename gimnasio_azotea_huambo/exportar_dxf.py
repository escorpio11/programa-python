# -*- coding: utf-8 -*-
"""Planta del gimnasio en DXF (metros, por capas) para AutoCAD."""
import os
import ezdxf

import diseno as D

AQUI = os.path.dirname(os.path.abspath(__file__))
SALIDA = D.SALIDA
CAPAS = {  # nombre: color ACI
    "G-EJES": 8, "G-MUROS-PARAPETO": 7, "G-MUROS-BANOS": 7, "G-COLUMNAS": 7, "G-TRAGALUCES": 9, "G-ESCALERA": 9, "G-TANQUE-LAVADERO": 5,
    "G-MAQUINAS": 4, "G-MAQUINAS-TEXTO": 4, "G-RECEPCION": 1, "G-PISOS": 3, "G-CERRAMIENTO": 6, "G-LUMINARIAS": 2, "G-ELECTRICO": 1,
    "G-SEGURIDAD": 1, "G-VIGAS-PROY": 150, "G-COTAS": 8, "G-TEXTO": 7, "G-PLANO-BASE": 30,
}


def generar():
    doc = ezdxf.new("R2010", setup=True); doc.units = ezdxf.units.M; doc.header["$INSUNITS"] = 6
    for n, c in CAPAS.items():
        doc.layers.add(n, color=c)
    msp = doc.modelspace()
    Y = lambda y: -y                                    # y del modelo crece hacia abajo en planta

    def rect(r, capa):
        msp.add_lwpolyline([(r[0], Y(r[1])), (r[2], Y(r[1])), (r[2], Y(r[3])), (r[0], Y(r[3]))], close=True, dxfattribs={"layer": capa})

    def texto(t, x, y, h=0.12, capa="G-TEXTO", rot=0):
        msp.add_text(t, height=h, dxfattribs={"layer": capa, "rotation": rot}).set_placement((x, Y(y)), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)

    for x0, y0, x1, y1, h, clave in D.MUROS:
        rect((x0, y0, x1, y1), "G-MUROS-BANOS" if clave == "bano" else "G-MUROS-PARAPETO")
    for x0, y0, x1, y1, h in D.COLUMNAS:
        rect((x0, y0, x1, y1), "G-COLUMNAS")
    for t in D.TRAGALUCES:
        r = t["rect"]; rect(r, "G-TRAGALUCES")
        msp.add_line((r[0], Y(r[1])), (r[2], Y(r[3])), dxfattribs={"layer": "G-TRAGALUCES"}); msp.add_line((r[0], Y(r[3])), (r[2], Y(r[1])), dxfattribs={"layer": "G-TRAGALUCES"})
        texto(t["id"], (r[0] + r[2]) / 2, (r[1] + r[3]) / 2, 0.1, "G-TRAGALUCES", 90)
    rect(D.ESCALERA["rect"], "G-ESCALERA"); rect(D.ESCALERA["espina"], "G-ESCALERA"); texto("ESCALERA (llega)", 6.3, 0.5, 0.1, "G-ESCALERA")
    for p in D.PUERTAS:
        xb = p["x1"] if p["bisagra"] == "x1" else p["x0"]
        msp.add_line((xb, Y(p["y"])), (xb, Y(p["y"] - p["ancho"])), dxfattribs={"layer": "G-MUROS-BANOS"})
        msp.add_arc((xb, Y(p["y"])), p["ancho"], 90, 180, dxfattribs={"layer": "G-MUROS-BANOS"}) if p["bisagra"] == "x1" else msp.add_arc((xb, Y(p["y"])), p["ancho"], 0, 90, dxfattribs={"layer": "G-MUROS-BANOS"})
        texto(p["id"], (p["x0"] + p["x1"]) / 2, p["y"] + 0.15, 0.08, "G-MUROS-BANOS")
    for b in D.BANOS:
        r = b["rect"]; texto(b["id"], (r[0] + r[2]) / 2, (r[1] + r[3]) / 2, 0.09); rect(b["ducha"], "G-MUROS-BANOS")
    tq = D.TANQUE; rect(tq["plataforma"], "G-TANQUE-LAVADERO"); msp.add_circle((tq["centro"][0], Y(tq["centro"][1])), tq["diam"] / 2, dxfattribs={"layer": "G-TANQUE-LAVADERO"})
    texto("TQ-1 1100 L", tq["centro"][0], tq["centro"][1], 0.09, "G-TANQUE-LAVADERO"); rect(D.LAVADERO["rect"], "G-TANQUE-LAVADERO"); texto("LAVADERO", 1.355, 2.64, 0.08, "G-TANQUE-LAVADERO", 90)
    for m in D.MAQUINAS:
        r = D.rect_maquina(m); rect(r, "G-MAQUINAS")
        texto("%d %s" % (int(m["id"][1:]), m["nombre"]), m["c"][0], m["c"][1], 0.09, "G-MAQUINAS-TEXTO", 90 if (r[3] - r[1]) > 1.6 * (r[2] - r[0]) else 0)
    for mid, r in D.MAQUINAS_P1.items():
        rect(r, "G-PLANO-BASE"); texto("ubicación original " + mid, (r[0] + r[2]) / 2, r[1] + 0.12, 0.07, "G-PLANO-BASE")
    for x, y in D.PORTA_DISCOS:
        msp.add_circle((x, Y(y)), 0.26, dxfattribs={"layer": "G-MAQUINAS"}); texto("PD", x, y, 0.08, "G-MAQUINAS-TEXTO")
    R = D.RECEPCION
    for k, n in (("mostrador", "MOSTRADOR"), ("panel_marca", ""), ("lockers", "LOCKERS (12)"), ("banca", "BANCA"), ("estante", "")):
        rect(R[k], "G-RECEPCION")
        if n:
            texto(n, (R[k][0] + R[k][2]) / 2, (R[k][1] + R[k][3]) / 2, 0.08, "G-RECEPCION", 90 if k != "banca" else 0)
    for x0, y0, x1, y1, h in D.CELOSIAS:
        msp.add_line((x0, Y(y0)), (x1, Y(y1)), dxfattribs={"layer": "G-RECEPCION"})
    for p in D.PISOS:
        if "rect" in p:
            rect(p["rect"], "G-PISOS"); texto(p["nombre"], (p["rect"][0] + p["rect"][2]) / 2, p["rect"][3] - 0.15, 0.08, "G-PISOS")
        if "poligono" in p:
            msp.add_lwpolyline([(x, Y(y)) for x, y in p["poligono"]], close=True, dxfattribs={"layer": "G-PISOS"})
    for x0, y0, x1, y1, tipo in D.CERRAMIENTO:
        msp.add_line((x0, Y(y0)), (x1, Y(y1)), dxfattribs={"layer": "G-CERRAMIENTO"}); texto(tipo, (x0 + x1) / 2, (y0 + y1) / 2, 0.07, "G-CERRAMIENTO", 90 if x0 == x1 else 0)
    for a, b in D.ESPEJOS:
        msp.add_line((a, Y(D.T + 0.03)), (b, Y(D.T + 0.03)), dxfattribs={"layer": "G-CERRAMIENTO"})
    for x, y in D.LUMINARIAS:
        rect((x - 0.06, y - 0.6, x + 0.06, y + 0.6), "G-LUMINARIAS")
    for x, y, d in D.VENTILADORES:
        msp.add_circle((x, Y(y)), 0.24, dxfattribs={"layer": "G-ELECTRICO"}); texto("V", x, y, 0.1, "G-ELECTRICO")
    for x, y, t in D.TOMACORRIENTES:
        msp.add_circle((x, Y(y)), 0.1, dxfattribs={"layer": "G-ELECTRICO"})
    for x, y in D.EXTINTORES:
        msp.add_circle((x, Y(y)), 0.14, dxfattribs={"layer": "G-SEGURIDAD"}); texto("E", x, y, 0.1, "G-SEGURIDAD")
    for x, y in D.LUCES_EMERGENCIA:
        rect((x - 0.14, y - 0.08, x + 0.14, y + 0.08), "G-SEGURIDAD")
    for a, b in D.VIGAS_X:
        rect((a, 0.15, b, D.W - 0.15), "G-VIGAS-PROY")
    for y0, y1, x0, x1 in D.VIGAS_Y:
        rect((x0, y0, x1, y1), "G-VIGAS-PROY")
    for k, x in D.EJES.items():
        msp.add_line((x, Y(-0.8)), (x, Y(D.W + 0.3)), dxfattribs={"layer": "G-EJES"}); msp.add_circle((x, Y(-1.05)), 0.22, dxfattribs={"layer": "G-EJES"}); texto(k, x, -1.05, 0.16, "G-EJES")
    dim = doc.dimstyles.get("EZDXF")
    for p1, p2, base in (((0, Y(D.W)), (D.L, Y(D.W)), (0, Y(D.W + 0.9))), ((D.L, 0), (D.L, Y(D.W)), (D.L + 0.7, 0))):
        d = msp.add_linear_dim(base=base, p1=p1, p2=p2, angle=0 if p1[1] == p2[1] else 90, dimstyle="EZDXF", override={"dimtxt": 0.14, "dimasz": 0.1, "dimexe": 0.05, "dimexo": 0.05, "dimdec": 2}, dxfattribs={"layer": "G-COTAS"}); d.render()
    texto("AZOTEA GYM - PLANTA DE DISTRIBUCION%s (m). Verificar medidas en obra." % (" VERSION B CON CARDIO" if D.VERSION == "B" else " PROPUESTA"), D.L / 2, D.W + 1.5, 0.2)
    if D.ZONA_SEGURIDAD:
        rect(D.ZONA_SEGURIDAD, "G-SEGURIDAD"); texto("ZONA LIBRE DE SEGURIDAD", (D.ZONA_SEGURIDAD[0] + D.ZONA_SEGURIDAD[2]) / 2, (D.ZONA_SEGURIDAD[1] + D.ZONA_SEGURIDAD[3]) / 2, 0.08, "G-SEGURIDAD")
    ruta = os.path.join(SALIDA, "Azotea_Gym_planta%s.dxf" % D.SUFIJO)
    doc.saveas(ruta)
    return ruta


if __name__ == "__main__":
    print(generar())
