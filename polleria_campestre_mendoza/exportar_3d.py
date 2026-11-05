"""
Exporta la geometría de la pollería a JSON para el modelo 3D (three.js).

Convención: puntos en (u, v) metros, origen en el vértice B del lote; en three.js
x = u, y = altura, z = -v. Alturas en metros sobre el NPT del 1.er piso (±0.00).
El entorno urbano (calles, casas vecinas, cerros) se toma del JSON del
estacionamiento: ../estacionamiento_rodriguez_mendoza/animacion_3d/web/escena.json
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
from shapely.geometry import LineString, MultiLineString, Polygon
from shapely.ops import unary_union

import diseno as dz
import edificio as ed
import estructura_pol as es

R = lambda x: round(float(x), 3)  # noqa: E731


def pts(geom):
    if geom is None or geom.is_empty:
        return []
    if geom.geom_type == "Polygon":
        return [[R(x), R(y)] for x, y in list(geom.exterior.coords)[:-1]]
    if geom.geom_type in ("LineString",):
        return [[R(x), R(y)] for x, y in geom.coords]
    if hasattr(geom, "geoms"):
        mayor = max(geom.geoms, key=lambda g_: g_.area if g_.area else g_.length)
        return pts(mayor)
    raise ValueError(geom.geom_type)


def polys(geom):
    if geom is None or geom.is_empty:
        return []
    if geom.geom_type == "Polygon":
        return [pts(geom)]
    return [pts(g_) for g_ in geom.geoms if g_.geom_type == "Polygon" and g_.area > 0.05]


def P(s, d):
    p = dz.SD(s, d)
    return [R(p[0]), R(p[1])]


def seg_sd(s0, d0, s1, d1, tipo, h0=0.0, h1=3.3, **extra):
    return dict(a=P(s0, d0), b=P(s1, d1), tipo=tipo, h0=h0, h1=h1, **extra)


def muros():
    S0, S1, D0, D1 = dz.S0, dz.S1, dz.D0, dz.D1
    B1 = dz.EJES_D[1]
    H1 = dz.NPT2 - 0.45                   # cielo raso bajo vigas
    m1 = [
        # 1.er piso: fachada este (servicio) con puerta y ventanas altas
        seg_sd(S0, D0, 8.95, D0, "muro", 0, H1), seg_sd(8.95, D0, 9.85, D0, "puerta", 0, 2.4),
        seg_sd(9.85, D0, S1, D0, "muro_ventana_alta", 0, H1),
        # fachada sur (cocina y SS.HH.): muro con ventanas altas
        seg_sd(S1, D0, S1, D1, "muro_ventana_alta", 0, H1),
        # fachada oeste: SS.HH. (muro), despacho (puertas plegables de vidrio), hall (vidrio)
        seg_sd(S1, D1, 15.0, D1, "muro", 0, H1), seg_sd(15.0, D1, 12.3, D1, "vidrio_plegable", 0, 2.7),
        seg_sd(12.3, D1, S0, D1, "vidrio", 0, H1),
        # fachada norte: hall (vidrio con puerta corrediza) y servicio (muro)
        seg_sd(S0, D1, S0, 20.2, "vidrio", 0, H1), seg_sd(S0, 20.2, S0, 18.4, "puerta_vidrio", 0, 2.4),
        seg_sd(S0, 18.4, S0, B1, "vidrio", 0, H1), seg_sd(S0, B1, S0, D0, "muro", 0, H1),
        # tabique entre cocina y franja pública (con ventana de despacho)
        seg_sd(S0, B1, 10.8, B1, "tabique", 0, H1), seg_sd(10.8, B1, 14.6, B1, "pase", 0, H1),
        seg_sd(14.6, B1, S1, B1, "tabique", 0, H1),
    ]
    N2, H2 = dz.NPT2, dz.H_ALERO - dz.NPT2 - 0.15
    m2 = [
        # fachada este: SS.HH., bar y depósito con ventanas; puerta del pasillo a la escalera exterior
        seg_sd(S0, D0, 17.3, D0, "muro_ventana", N2, N2 + H2), seg_sd(17.3, D0, S1, D0, "puerta", N2, N2 + 2.4),
        # fachada sur: depósito y pasillo; muro acústico al fondo del escenario
        seg_sd(S1, D0, S1, B1, "muro", N2, N2 + H2),
        seg_sd(S1, B1, S1, 23.9, "muro_acustico", N2, N2 + H2 + 0.6),
        # fachada norte (SS.HH. hacia el volado norte techado), con sus 3 puertas
        seg_sd(S0, D0, S0, 12.9, "muro", N2, N2 + H2), seg_sd(S0, 12.9, S0, 13.9, "puerta", N2, N2 + 2.1),
        seg_sd(S0, 13.9, S0, 14.6, "muro", N2, N2 + H2), seg_sd(S0, 14.6, S0, 15.4, "puerta", N2, N2 + 2.1),
        seg_sd(S0, 15.4, S0, 16.8, "muro", N2, N2 + H2), seg_sd(S0, 16.8, S0, 17.6, "puerta", N2, N2 + 2.1),
        seg_sd(S0, 17.6, S0, B1, "muro", N2, N2 + H2),
        # cara oeste de la franja del bar: SS.HH. (muro), bar (vidrio plegable), depósito (muro); pasillo abierto
        seg_sd(S0, B1, 10.0, B1, "muro", N2, N2 + H2), seg_sd(10.0, B1, 15.0, B1, "vidrio_plegable", N2, N2 + 2.7),
        seg_sd(15.0, B1, 17.3, B1, "muro", N2, N2 + H2),
        # tabiques interiores
        seg_sd(10.0, D0, 10.0, B1, "tabique", N2, N2 + H2), seg_sd(15.0, D0, 15.0, B1, "tabique", N2, N2 + H2),
        seg_sd(17.3, D0, 17.3, B1, "tabique", N2, N2 + H2),
        seg_sd(S0, 14.4, 10.0, 14.4, "tabique", N2, N2 + H2), seg_sd(S0, 16.2, 10.0, 16.2, "tabique", N2, N2 + H2),
        # ascensor panorámico exterior (caja de vidrio y acero sobre el porche de ingreso)
        *[seg_sd(*seg, "vidrio", 0, N2 + 3.4) for seg in (
            (ed.ASCENSOR[0], ed.ASCENSOR[2], ed.ASCENSOR[1], ed.ASCENSOR[2]),
            (ed.ASCENSOR[1], ed.ASCENSOR[2], ed.ASCENSOR[1], ed.ASCENSOR[3]),
            (ed.ASCENSOR[1], ed.ASCENSOR[3], ed.ASCENSOR[0], ed.ASCENSOR[3]),
            (ed.ASCENSOR[0], ed.ASCENSOR[3], ed.ASCENSOR[0], ed.ASCENSOR[2]))],
    ]
    return m1, m2


def barandas():
    """Bordes de la losa del 2.º piso que no son muro: baranda de vidrio de 1.10 m."""
    borde = dz.LOSA2.exterior
    excluir = unary_union([LineString([dz.SD(dz.S0, dz.D0), dz.SD(dz.S1, dz.D0)]).buffer(0.05),
                           LineString([dz.SD(dz.S1, dz.D0), dz.SD(dz.S1, 24.4)]).buffer(0.05)])
    resto = LineString(borde.coords).difference(excluir)
    segs = []
    for ln in getattr(resto, "geoms", [resto]):
        c = list(ln.coords)
        for a, b in zip(c, c[1:]):
            if np.hypot(b[0] - a[0], b[1] - a[1]) > 0.2:
                segs.append(dict(a=[R(a[0]), R(a[1])], b=[R(b[0]), R(b[1])], h=1.10))
    return segs


def techo(rect_local, dir_cumbrera):
    """rect_local en coordenadas de dibujo (x = -d, y = -s) -> 4 esquinas (u, v) y eje de cumbrera."""
    x0, y0, x1, y1 = rect_local.bounds
    s0, s1, d0, d1 = -y1, -y0, -x1, -x0
    esq = [P(s0, d0), P(s1, d0), P(s1, d1), P(s0, d1)]
    if dir_cumbrera == "s":
        cum = [P(s0, (d0 + d1) / 2), P(s1, (d0 + d1) / 2)]
    else:
        cum = [P((s0 + s1) / 2, d0), P((s0 + s1) / 2, d1)]
    return dict(esquinas=esq, cumbrera=cum, alero=dz.H_ALERO, h_cumbrera=dz.H_CUMBRE)


def cerco_piscina():
    """Línea del cerco de vidrio (1.20 m) entre el jardín y la zona de piscina, de los vestidores al porche."""
    x1, y1 = dz.VESTIDORES.bounds[2], dz.VESTIDORES.bounds[3]
    sw = dz.SD(dz.S1, dz.D1 + dz.VOLADO_O)
    return [(x1, y1), (dz.U_CERCO_PISCINA, y1), (dz.U_CERCO_PISCINA, dz.V_CERCO_PISCINA),
            (sw[0], dz.V_CERCO_PISCINA), (sw[0], sw[1])]


def autos():
    out = []
    tipos = ["suv", "sedan", "pickup", "hatchback"]
    for p, tipo in zip(dz.PLAZAS[1:], tipos):
        c = p["poly"].centroid
        out.append(dict(plaza=p["codigo"], centro=[R(c.x), R(c.y)], frente=[R(-dz.g.DC.n[0]), R(-dz.g.DC.n[1])],
                        tipo=tipo))
    return out


def exportar(ruta):
    import laminas                        # import diferido: laminas importa este módulo
    m1, m2 = muros()
    t1, desc, t2, lleg = ed.escalera_exterior()
    datos = dict(
        meta=dict(proyecto="Pollería campestre", ubicacion="Jr. Rodríguez de Mendoza, Mendoza (Amazonas)",
                  convencion="(u, v) en m, origen en B; three.js: x = u, y = altura, z = -v",
                  contexto="../../estacionamiento_rodriguez_mendoza/animacion_3d/web/escena.json",
                  norte=[R(dz.g.NORTE[0]), R(dz.g.NORTE[1])]),
        lote=pts(dz.LOTE), interior=pts(dz.INTERIOR),
        marco_sd=dict(D=[R(dz.D[0]), R(dz.D[1])], t=[R(dz.g.DC.t[0]), R(dz.g.DC.t[1])], n=[R(dz.g.DC.n[0]), R(dz.g.DC.n[1])]),
        vanos=[
            dict(codigo="V-1", tipo="porton_corredizo", ancho=6.0, a=P(0.0, dz.PORTON_V[0]), b=P(0.0, dz.PORTON_V[1])),
            dict(codigo="P-2", tipo="puerta_peatonal", ancho=1.8, a=P(0.0, dz.PORTON_P2[0]), b=P(0.0, dz.PORTON_P2[1])),
            dict(codigo="GLP", tipo="puerta_servicio", ancho=1.6, a=P(0.0, 0.6), b=P(0.0, 2.2)),
            dict(codigo="P-1", tipo="portada_principal", ancho=3.0,
                 a=[R(x) for x in dz.punto_AB(dz.P1_DESDE_A[0])], b=[R(x) for x in dz.punto_AB(dz.P1_DESDE_A[1])]),
            dict(codigo="P-3", tipo="puerta_emergencia", ancho=1.2,
                 a=[R(x) for x in dz.punto_AB(dz.P3_DESDE_A[0])], b=[R(x) for x in dz.punto_AB(dz.P3_DESDE_A[1])]),
        ],
        cercos=dict(frentes=dict(lados=["AB", "DA"], tipo="murete 0.60 m de piedra + reja de madera hasta 1.80 m + seto",
                                 altura=1.80),
                    vecinos=dict(lados=["BC", "CD"], tipo="muro tarrajeado existente", altura=2.40)),
        existentes=dict(lena=dict(poly=pts(dz.LENA), altura=2.6, tipo="cobertizo de madera con techo de calamina"),
                        garaje=dict(poly=pts(dz.GARAJE), altura=2.8, puerta_lado="norte (hacia la calzada)")),
        pisos=dict(
            calzada=pts(dz.CALZADA), vereda=pts(dz.VEREDA), zona_carga=pts(dz.ZONA_CARGA),
            plazas=[dict(codigo=p["codigo"], tipo=p["tipo"], poly=pts(p["poly"])) for p in dz.PLAZAS],
            motos=pts(dz.MOTOS), glp=pts(dz.GLP), porche=polys(dz.PORCHE), jardines=polys(dz.JARDINES),
            setos=polys(laminas.seto(1)), setos2=polys(laminas.seto(2)),
            mesas_evento=[[R(c[0]), R(c[1])] for c in laminas.mesas_evento(1)[0]],
            caminos=[dict(nombre=k, eje=pts(v), ancho=dz.ANCHO_CAMINO[k], etapa=dz.ETAPA_CAMINO[k],
                          poly=pts(dz.camino_poly(k))) for k, v in dz.CAMINOS.items()],
        ),
        edificio=dict(
            ejes_s=list(dz.EJES_S), ejes_d=list(dz.EJES_D), columnas=[P(s, d) for s, d in dz.COLUMNAS],
            columna_lado=0.203, columnas_hasta_techo=[P(s, d) for s, d in dz.COLUMNAS if not (s == dz.EJES_S[0] and d == dz.EJES_D[2])],
            npt2=dz.NPT2, alero=dz.H_ALERO, cumbrera=dz.H_CUMBRE, espesor_losa=0.12,
            peralte_vigas=0.41, envolvente1=pts(dz.EDIFICIO), losa2=pts(dz.LOSA2),
            muros1=m1, muros2=m2, barandas=barandas(),
            escenario=dict(poly=pts(ed.local_inv(ed.ESCENARIO)), altura=0.40),
            techos=[techo(ed.TECHO_BAR, "s"), techo(ed.TECHO_ESC, "d")],
            chimenea=dict(poly=[P(10.4, 12.0), P(13.1, 12.0), P(13.1, 12.6), P(10.4, 12.6)], altura=9.30),
            escalera_exterior=dict(ancho=1.20, d0=dz.D_VEREDA[0], d1=dz.D_VEREDA[1], s=list(dz.S_ESC_EXT),
                                   contrapaso=round(ed.CONTRA, 4), huella=ed.HUELLA),
            escalera_principal=dict(descripcion="en U, 2 tramos de 1.20 m, 22 contrapasos", poly=[P(7.9, 20.3), P(12.3, 20.3),
                                                                                                  P(12.3, 22.9), P(7.9, 22.9)]),
            barra2=[P(10.2, 15.35), P(14.8, 15.35), P(14.8, 15.95), P(10.2, 15.95)],
            ascensor=[P(ed.ASCENSOR[0], ed.ASCENSOR[2]), P(ed.ASCENSOR[1], ed.ASCENSOR[2]),
                      P(ed.ASCENSOR[1], ed.ASCENSOR[3]), P(ed.ASCENSOR[0], ed.ASCENSOR[3])],
            secciones=dict(columnas=es.COLUMNA["seccion"].nombre, vigas=es.VIGA["seccion"].nombre,
                           viguetas=es.VIGUETA["seccion"].nombre),
        ),
        sombrillas=[dict(codigo=a.codigo, centro=[R(a.centro[0]), R(a.centro[1])], ang=R(a.ang), lado=dz.LADO_SOMBRILLA,
                         mesa=a.mesa, etapas=[1, 2]) for a in dz.SOMBRILLAS]
        + [dict(codigo=a.codigo, centro=[R(a.centro[0]), R(a.centro[1])], ang=R(a.ang), lado=dz.LADO_SOMBRILLA,
                mesa=a.mesa, etapas=[1]) for a in dz.SOMBRILLAS_E1_SUR]
        + [dict(codigo=a.codigo, centro=[R(a.centro[0]), R(a.centro[1])], ang=R(a.ang), lado=dz.LADO_SOMBRILLA,
                mesa=a.mesa, etapas=[2]) for a in dz.SOMBRILLAS_E2_RELAJO],
        mesas_1=[pts(ed.local_inv(m)) for m in ed.MESAS_1],
        mesas_2=[pts(ed.local_inv(m)) for m in ed.MESAS_2],
        arboles=[dict(p=[R(a["p"][0]), R(a["p"][1])], copa=a["copa"], tipo=a["tipo"], etapa=a.get("etapa", 1),
                      nombre=a["nombre"]) for a in dz.ARBOLES],
        piscina=dict(poly=pts(dz.PISCINA), ninos=pts(dz.PATERA), prof_ninos=dz.PROF_NINOS,
                     vest_damas=pts(dz.VEST_DAMAS), vest_varones=pts(dz.VEST_VARONES), paso_limpio=pts(dz.PASO_LIMPIO),
                     cerco=[[R(x), R(y)] for x, y in cerco_piscina()],
                     prof_min=dz.PROF_MIN, prof_max=dz.PROF_MAX, anden=pts(dz.ANDEN), zona=pts(dz.ZONA_PISCINA),
                     vestidores=pts(dz.VESTIDORES), cuarto_maquinas=pts(dz.CUARTO_MAQ), ducha=pts(dz.DUCHA_EXT),
                     pediluvio=pts(dz.PEDILUVIO), relajo=pts(dz.RELAJO), camillas=[pts(c) for c in dz.CAMILLAS],
                     hamacas=[pts(h_) for h_ in dz.HAMACAS], altura_vestidores=2.70, cerco_altura=1.20),
        autos=autos(),
    )
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=1)
    return ruta


if __name__ == "__main__":
    ruta = sys.argv[1] if len(sys.argv) > 1 else os.path.join(dz.AQUI, "render3d", "web", "escena_polleria.json")
    print(exportar(ruta), os.path.getsize(ruta) // 1024, "KB")
