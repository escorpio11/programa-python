"""
Pollería campestre en el lote del Jr. Rodríguez de Mendoza (Mendoza, Amazonas).

Geometría de todo el proyecto sobre el mismo lote del anteproyecto de
estacionamiento (`../estacionamiento_rodriguez_mendoza/geometria.py`):

- estructuras existentes que se conservan: almacén de leña (junto al fondo C-D) y
  garaje del propietario (esquina C), medidos sobre el croquis del propietario;
- calzada vehicular de doble sentido desde la calle lateral hasta el garaje, con
  estacionamientos descubiertos, zona de carga y caseta de GLP y residuos;
- edificio central de estructura metálica de 2 pisos (cocina, horno de pollo a la
  brasa y parrilla abajo; bar, terraza y escenario arriba);
- jardines con sombrillas profesionales removibles (modo restaurante y modo evento);
- 2.ª etapa: piscina, vestidores, ducha exterior y zona de relajo.

Marcos de coordenadas (metros):
- (u, v): origen en el vértice B, u a lo largo de B→C (lindero de 40 m), v hacia el lote.
- (s, d): s a lo largo de D→C medido desde D, d desde el lindero C-D hacia el interior.
  El edificio y la calzada se ordenan en este marco (paralelos a la calle lateral D-A,
  que es perpendicular a C-D).
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field

import numpy as np
from shapely.affinity import rotate
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "estacionamiento_rodriguez_mendoza"))
import geometria as g  # noqa: E402

LOTE = g.LOTE
MURO = 0.15                                  # espesor de cercos
INTERIOR = LOTE.buffer(-MURO, join_style=2)
A, B, C, D = g.A, g.B, g.C, g.D


# --------------------------------------------------------------------------
# Marcos y utilidades
# --------------------------------------------------------------------------
def SD(s, d):
    """Punto (u, v) a partir de (s, d)."""
    return g.DC.punto(s, d)


def a_sd(p):
    p = np.asarray(p, float)
    return float(np.dot(p - g.DC.p0, g.DC.t)), float(np.dot(p - g.DC.p0, g.DC.n))


def rect_sd(s0, s1, d0, d1):
    return g.DC.rect(s0, s1, d0, d1)


def rect_uv(u0, u1, v0, v1):
    return box(u0, v0, u1, v1)


def poly_sd(pts):
    return Polygon([SD(s, d) for s, d in pts])


ANG_SD = float(np.degrees(np.arctan2(g.DC.t[1], g.DC.t[0])))   # orientación del eje s en (u, v)


def d_AB(s, retiro=0.0):
    """d del lindero A-B (frente al Jr. Rodríguez de Mendoza) a la altura s, desplazado `retiro` m hacia dentro."""
    # en (s, d): A = (0, 20), B = (22.86, 39.4); la normal interior de A-B tiene componente d = -0.762
    sA, dA = a_sd(A)
    sB, dB = a_sd(B)
    m = (dB - dA) / (sB - sA)
    cosang = 1.0 / np.sqrt(1 + m * m)
    return dA + m * (s - sA) - retiro / cosang


def semiplano_AB(retiro):
    """Región del lote a más de `retiro` m del frente A-B."""
    t = (B - A) / np.linalg.norm(B - A)
    n = np.array([t[1], -t[0]])              # normal hacia el interior del lote
    if np.dot(np.array(LOTE.centroid.coords[0]) - A, n) < 0:
        n = -n
    p0, p1 = A + n * retiro - t * 60, B + n * retiro + t * 60
    return Polygon([p0, p1, p1 + n * 80, p0 + n * 80])


# --------------------------------------------------------------------------
# Estructuras existentes (croquis del propietario sobre la lámina A-01)
# --------------------------------------------------------------------------
LENA = rect_sd(2.6, 9.2, MURO, 3.6)                                     # ≈ 6.6 × 3.45 m
GARAJE = rect_uv(29.45, 41.0, MURO, 5.50).intersection(INTERIOR)        # ≈ 10.4 × 5.35 m

# --------------------------------------------------------------------------
# Zona vehicular (en el marco s, d)
# --------------------------------------------------------------------------
D_CALZ = (5.2, 11.2)            # calzada de 6.00 m, doble sentido
D_VEREDA = (11.2, 12.4)         # vereda interior de 1.20 m
PORTON_V = (D_CALZ[0], D_CALZ[1])                      # portón vehicular en la calle lateral (d desde D)
PORTON_P2 = (D_VEREDA[0] + 0.05, D_VEREDA[0] + 1.85)   # puerta peatonal en la calle lateral (1.80 m)
CALZADA = rect_sd(-0.5, 26.0, *D_CALZ).intersection(INTERIOR).intersection(rect_uv(-5, 50, 5.50, 50))
LARGO_PLAZA, ANCHO_PLAZA, ANCHO_ACC = 5.0, 2.5, 3.8
S_PLAZAS0 = 9.6
_cortes = [S_PLAZAS0, S_PLAZAS0 + ANCHO_ACC]
for _ in range(4):
    _cortes.append(_cortes[-1] + ANCHO_PLAZA)
PLAZAS = []
for i, (s0, s1) in enumerate(zip(_cortes, _cortes[1:])):
    PLAZAS.append(dict(codigo=f"E{i + 1}", tipo="accesible" if i == 0 else "auto",
                       poly=rect_sd(s0, s1, D_CALZ[0] - LARGO_PLAZA, D_CALZ[0]), s0=s0, s1=s1))
MOTOS = rect_sd(0.35, 2.45, 2.55, 5.05)
GLP = rect_sd(0.35, 2.45, MURO + 0.05, 2.45)            # caseta de GLP y residuos, con puerta a la calle lateral
ZONA_CARGA = rect_sd(7.6, 11.0, D_CALZ[1] - 1.9, D_CALZ[1])

# --------------------------------------------------------------------------
# Edificio central (estructura metálica de 2 pisos), marco (s, d)
# --------------------------------------------------------------------------
EJES_S = (7.5, 13.0, 18.5)       # ejes 1-2-3 (fachada de ingreso → fachada posterior)
EJES_D = (12.4, 17.9, 22.9)      # ejes A-B-C (calzada → jardín lateral)
S0, S1 = EJES_S[0], EJES_S[-1]
D0, D1 = EJES_D[0], EJES_D[-1]
VOLADO_N, VOLADO_O = 2.0, 2.0    # voladizos del 2.º piso: sobre el ingreso (N) y hacia el jardín lateral (O)
RETIRO_AEREO = 1.0               # el borde de la losa en volado queda a ≥ 1.00 m del lindero A-B
NPT2 = 3.85                      # nivel del 2.º piso
H_ALERO, H_CUMBRE = 7.15, 8.25   # techo a dos aguas sobre bar y escenario
EDIFICIO = rect_sd(S0, S1, D0, D1)
LOSA2 = rect_sd(S0 - VOLADO_N, S1, D0, D1 + VOLADO_O).intersection(semiplano_AB(RETIRO_AEREO))
PORCHE = LOSA2.difference(EDIFICIO)
COLUMNAS = [(s, d) for s in EJES_S for d in EJES_D]
# Escalera exterior de evacuación y de carga de equipos (sube hacia el sur pegada a la fachada de servicio):
# descanso inferior s 9.3-10.5, tramos de 2.80 m, descanso intermedio de 1.20 m y llegada en s 17.3-18.5,
# junto al pasillo que da al escenario.
S_ESC_EXT = (9.3, 10.5, 13.3, 14.5, 17.3, 18.5)
ESCALERA_EXT = rect_sd(S_ESC_EXT[1], S_ESC_EXT[-1], D_VEREDA[0], D_VEREDA[1])
VEREDA = rect_sd(-0.5, S_ESC_EXT[1], *D_VEREDA).intersection(INTERIOR)

# --------------------------------------------------------------------------
# 2.ª etapa: piscina, vestidores, ducha exterior y relajo (marco u, v, paralelo al lindero B-C)
# --------------------------------------------------------------------------
# D.S. 007-2003-SA (Reglamento Sanitario de Piscinas): andén perimetral de 1.50 m, pediluvio de 3.00 m de largo,
# ducha previa obligatoria y patera para niños separada del vaso de adultos.
ANDEN_ANCHO = 1.50
PISCINA = rect_uv(16.7, 22.7, 1.65, 5.15)          # vaso de adultos 6.00 × 3.50 m (21.0 m²), 1.20 → 1.50 m
PATERA = rect_uv(13.1, 15.5, 1.65, 4.05)           # patera para niños 2.40 × 2.40 m (5.8 m²), 0.30-0.40 m
PISCINA_NINOS = PATERA
PROF_NINOS, PROF_MIN, PROF_MAX = 0.35, 1.20, 1.50
ANDEN = unary_union([PISCINA.buffer(ANDEN_ANCHO, join_style=2), PATERA.buffer(ANDEN_ANCHO, join_style=2)]).intersection(
    rect_uv(-5, 60, MURO, 60))
VESTIDORES = rect_uv(3.4, 8.4, MURO, 3.95)         # control de acceso: se entra por el jardín y se sale a la piscina
# Circulación "sucia → limpia": cada vestidor se entra desde el atrio del jardín (cara de v = 3.95) y se sale al
# paso limpio (franja junto al lindero), que lleva a la ducha y al pediluvio; el cuarto de máquinas se atiende desde
# el jardín, sin entrar a la zona de piscina.
VEST_DAMAS = rect_uv(3.4, 5.4, 1.35, 3.95)         # inodoro, lavatorio, ducha, banca y colgadores
VEST_VARONES = rect_uv(5.4, 7.4, 1.35, 3.95)       # inodoro, urinario, lavatorio, ducha, banca y colgadores
CUARTO_MAQ = rect_uv(7.4, 8.4, 1.35, 3.95)         # filtro, bomba, clorador y tablero de la piscina
PASO_LIMPIO = rect_uv(3.4, 8.4, MURO, 1.35)        # salida de los vestidores hacia la ducha y el pediluvio
DUCHA_EXT = rect_uv(8.55, 9.55, 0.25, 1.45)
PEDILUVIO = rect_uv(8.6, 11.6, 0.25, 1.45)         # 3.00 × 1.20 m, cloro libre 0.01 %, desemboca en el andén
RELAJO = rect_uv(24.2, 29.3, MURO, 5.40)
V_CERCO_PISCINA = 5.70                              # cerco de vidrio de 1.20 m entre el jardín y la piscina
U_CERCO_PISCINA = 11.35                             # quiebre del cerco junto al andén de la patera


def _zona_piscina():
    sw = SD(S1, D1 + VOLADO_O)                       # esquina SO del porche
    se = SD(S1, D0)
    x0, y0, x1, y1 = VESTIDORES.bounds
    poly = Polygon([(x0, -2), (x0, y1), (U_CERCO_PISCINA, y1), (U_CERCO_PISCINA, V_CERCO_PISCINA),
                    (sw[0], V_CERCO_PISCINA), tuple(sw), tuple(se), (se[0], 5.5), (GARAJE.bounds[0], 5.5),
                    (GARAJE.bounds[0], -2)])
    return poly.intersection(INTERIOR).difference(EDIFICIO).difference(LOSA2.buffer(0.0))


ZONA_PISCINA = _zona_piscina()

# --------------------------------------------------------------------------
# Jardines y accesos peatonales
# --------------------------------------------------------------------------
P1_DESDE_A = (1.8, 4.8)       # puerta peatonal principal en el Jr. Rodríguez de Mendoza (m desde A, 3.00 m)
P3_DESDE_A = (24.0, 25.2)     # salida de emergencia al Jr. Rodríguez de Mendoza (1.20 m, abre hacia fuera)


def punto_AB(dist_desde_A):
    t = (B - A) / np.linalg.norm(B - A)
    return A + t * dist_desde_A


ocupado = unary_union([LENA, GARAJE, CALZADA, *[p["poly"] for p in PLAZAS], MOTOS, GLP, VEREDA, EDIFICIO, PORCHE,
                       ESCALERA_EXT, ZONA_PISCINA])
JARDINES = INTERIOR.difference(ocupado.buffer(0.0))
_parts = sorted(getattr(JARDINES, "geoms", [JARDINES]), key=lambda p: -p.area)
JARDIN_NORTE = max(_parts, key=lambda p: p.centroid.y) if _parts else None
JARDIN_OESTE = [p for p in _parts if p is not JARDIN_NORTE and p.area > 5]


# --------------------------------------------------------------------------
# Sombrillas profesionales (3.00 × 3.00 m) — modo restaurante
# --------------------------------------------------------------------------
LADO_SOMBRILLA = 3.0


@dataclass
class Sombrilla:
    codigo: str
    centro: tuple          # (u, v)
    ang: float             # grados
    zona: str
    mesa: str = "6"        # "6": mesa rectangular de 6; "4": mesa cuadrada de 4; "C": 2 camillas

    @property
    def lona(self):
        h = LADO_SOMBRILLA / 2
        return rotate(box(self.centro[0] - h, self.centro[1] - h, self.centro[0] + h, self.centro[1] + h),
                      self.ang, origin=self.centro)


def _somb(cod, s, d, zona, mesa="6", ang=None):
    return Sombrilla(cod, tuple(SD(s, d)), ANG_SD if ang is None else ang, zona, mesa)


# Etapa 1 (sin piscina): 10 sombrillas. En la 2.ª etapa la franja sur se convierte en la zona de piscina: S6 y
# S7 pasan a la zona de relajo y S8-S10 quedan para eventos o se reubican.
SOMBRILLAS = [
    _somb("S1", 2.9, 14.0, "Jardín de ingreso"),
    _somb("S2", 3.0, 17.6, "Jardín de ingreso"),
    _somb("S3", 11.6, 26.6, "Jardín lateral"),
    _somb("S4", 15.3, 27.4, "Jardín lateral"),
    _somb("S5", 17.0, 31.2, "Jardín lateral", "4"),
]
SOMBRILLAS_E1_SUR = [Sombrilla(f"S{6 + i}", (8.6 + 4.0 * i, 2.3), 0.0, "Jardín posterior (etapa 1)") for i in range(5)]
SOMBRILLAS_E2_RELAJO = [Sombrilla("S6", (25.75, 2.05), 0.0, "Zona de relajo", "C")]
CAMILLAS = [rect_uv(24.45 + 1.0 * i, 24.45 + 1.0 * i + 0.72, 0.8, 2.8) for i in range(3)]
HAMACAS = [rect_uv(26.85, 29.2, 3.05 + 1.2 * i, 3.05 + 1.2 * i + 1.0) for i in range(2)]   # soportes de hamaca de 2.35 m

# --------------------------------------------------------------------------
# Paisajismo: árboles (copa en m) y setos en los frentes
# --------------------------------------------------------------------------
ARBOLES = [
    dict(nombre="Árbol ornamental de esquina (cedro o pino)", p=(15.58, 25.11), copa=1.8, tipo="frondoso"),
    dict(nombre="Palmera", p=tuple(SD(9.7, 26.55)), copa=1.6, tipo="palmera"),
    dict(nombre="Palmera", p=(2.2, 1.45), copa=1.2, tipo="palmera"),
    dict(nombre="Arbusto ornamental", p=tuple(SD(0.9, 12.95)), copa=1.1, tipo="arbusto"),
    dict(nombre="Palmera (zona de relajo)", p=(28.4, 1.7), copa=1.3, tipo="palmera", etapa=2),
]
SETO = 0.60    # jardinera con seto vivo detrás del cerco de los frentes

# --------------------------------------------------------------------------
# Circulaciones peatonales (ejes de recorridos pavimentados)
# --------------------------------------------------------------------------
ENTRADA = SD(EJES_S[0] - 0.05, 19.1)                 # puerta principal del edificio (fachada norte, hall de ingreso)
P1_C = punto_AB(sum(P1_DESDE_A) / 2)                 # centro de la puerta peatonal principal
P2_C = SD(0.0, sum(PORTON_P2) / 2)
P3_C = punto_AB(sum(P3_DESDE_A) / 2)
CAMINOS = {
    "principal": LineString([P1_C, SD(5.0, 20.4), SD(6.7, 19.6), ENTRADA]),
    # camino posterior: del extremo del porche lateral a la salida de emergencia P-3 bordeando el futuro cerco de la
    # piscina; en la 2.ª etapa su tramo final es el atrio de ingreso a los vestidores (control de acceso a la piscina)
    "sur": LineString([SD(17.6, 24.0), SD(18.0, 25.4), (12.4, 6.45), (10.6, 6.45), (9.6, 4.65), tuple(P3_C)]),
}
ANCHO_CAMINO = {"principal": 1.80, "sur": 1.20}
ETAPA_CAMINO = {"principal": 1, "sur": 1}


def camino_poly(nombre):
    """Superficie pavimentada de un camino (bordes rectos, recortada al lote)."""
    return CAMINOS[nombre].buffer(ANCHO_CAMINO[nombre] / 2, cap_style=2, join_style=2).intersection(INTERIOR)


def caminos_poly(etapa=2):
    return unary_union([camino_poly(k) for k in CAMINOS if ETAPA_CAMINO[k] <= etapa])


def verificar():
    """Comprobaciones geométricas básicas; devuelve la lista de problemas."""
    prob = []
    for nom, poly in (("leña", LENA), ("garaje", GARAJE), ("edificio", EDIFICIO), ("losa 2.º piso", LOSA2),
                      ("piscina", PISCINA), ("vestidores", VESTIDORES), ("relajo", RELAJO)):
        if not INTERIOR.buffer(1e-6).contains(poly):
            prob.append(f"{nom} sale del lote")
    for p in PLAZAS:
        if p["poly"].intersects(GARAJE) or p["poly"].intersects(LENA) or not INTERIOR.buffer(1e-6).contains(p["poly"]):
            prob.append(f"plaza {p['codigo']} invade garaje, leña o cerco")
    if CALZADA.intersects(LENA.buffer(-0.01)):
        prob.append("la calzada invade el almacén de leña")
    if PISCINA.distance(EDIFICIO) < 1.2:
        prob.append(f"piscina a {PISCINA.distance(EDIFICIO):.2f} m del edificio")
    if not INTERIOR.buffer(1e-6).contains(ANDEN):
        prob.append("el andén de la piscina sale del lote")
    j1 = INTERIOR.difference(unary_union([LENA, GARAJE, CALZADA, *[p["poly"] for p in PLAZAS], MOTOS, GLP, VEREDA,
                                          EDIFICIO, PORCHE, ESCALERA_EXT]).buffer(0))
    for a in SOMBRILLAS_E1_SUR:
        if not j1.buffer(-0.2).contains(a.lona) or any(a.lona.distance(b.lona) < 0.6 for b in SOMBRILLAS):
            prob.append(f"sombrilla {a.codigo} (etapa 1) no cabe en la franja sur")
    for a in SOMBRILLAS_E2_RELAJO:
        if not RELAJO.buffer(0.6).contains(a.lona):
            prob.append(f"sombrilla {a.codigo} fuera de la zona de relajo")
    for etapa, lista in ((1, SOMBRILLAS + SOMBRILLAS_E1_SUR), (2, SOMBRILLAS)):
        caminos = caminos_poly(etapa)
        for a in lista:
            if a.lona.distance(caminos) < 0.2:
                prob.append(f"sombrilla {a.codigo} sobre un camino (etapa {etapa})")
    todas = SOMBRILLAS + SOMBRILLAS_E1_SUR + SOMBRILLAS_E2_RELAJO
    caminos_todos = caminos_poly(2)
    for arb in ARBOLES:
        tronco = Point(arb["p"])
        if any(tronco.distance(x.lona) < 0.4 for x in todas if not (arb.get("etapa") == 2 and x in SOMBRILLAS_E1_SUR)):
            prob.append(f"árbol en {tuple(round(c, 1) for c in arb['p'])} bajo una sombrilla")
        if tronco.distance(caminos_todos) < 0.4:
            prob.append(f"árbol en {tuple(round(c, 1) for c in arb['p'])} sobre un camino")
        if not INTERIOR.contains(tronco):
            prob.append(f"árbol en {tuple(round(c, 1) for c in arb['p'])} fuera del lote")
    invade = caminos_todos.intersection(ZONA_PISCINA).area
    if invade > 0.05:
        prob.append(f"los caminos invaden {invade:.2f} m² de la zona de piscina")
    for a in SOMBRILLAS:
        lona = a.lona
        if not JARDINES.buffer(0.05).contains(lona):
            prob.append(f"sombrilla {a.codigo} fuera de jardín ({lona.difference(JARDINES).area:.2f} m²)")
        for b in SOMBRILLAS:
            if a is not b and a.codigo < b.codigo and lona.distance(b.lona) < 0.6:
                prob.append(f"sombrillas {a.codigo}-{b.codigo} a {lona.distance(b.lona):.2f} m")
    return prob


def cuadro_areas():
    filas = [
        ("Terreno", LOTE.area),
        ("Almacén de leña (existente)", LENA.area),
        ("Garaje del propietario (existente)", GARAJE.area),
        ("Calzada vehicular", CALZADA.area),
        ("Estacionamientos (5)", sum(p["poly"].area for p in PLAZAS)),
        ("Motos, GLP y residuos", MOTOS.area + GLP.area),
        ("Vereda interior y escalera exterior", VEREDA.area + ESCALERA_EXT.area),
        ("Edificio (1.er piso, cerrado)", EDIFICIO.area),
        ("Porches techados bajo el 2.º piso", PORCHE.area),
        ("Jardines con sombrillas", JARDINES.area),
        ("Zona de piscina y relajo (2.ª etapa)", ZONA_PISCINA.area),
        ("2.º piso (losa total)", LOSA2.area),
    ]
    return filas


if __name__ == "__main__":
    for f in cuadro_areas():
        print(f"{f[0]:42s} {f[1]:8.1f} m²")
    print("jardines:", [round(p.area, 1) for p in getattr(JARDINES, "geoms", [JARDINES])])
    print("problemas:", verificar() or "ninguno")
