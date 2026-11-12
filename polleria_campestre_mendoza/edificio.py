"""
Edificio central de la pollería: ambientes, equipos, puertas, escaleras y techos.

Todo se define en el marco (s, d) del edificio (ver `diseno.py`): s crece desde la fachada de
ingreso (hacia la calle lateral, orientada al ONO) hacia la fachada posterior (piscina, ESE); d crece desde
la calzada (fachada de servicio, NNE) hacia el jardín lateral (fachada lateral, SSO).
`local(geom)` lleva cualquier geometría (u, v) al marco de dibujo de las plantas
del edificio: x = -d (jardín lateral a la izquierda), y = -s (ingreso arriba); el norte
verdadero apunta hacia la derecha y algo arriba (ver `NORTE_LOCAL`).

Niveles: NPT 1.er piso ±0.00; 2.º piso +3.85; alero +7.15; cumbrera +8.25.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from shapely import affinity
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

import diseno as dz
from diseno import D0, D1, EJES_D, EJES_S, NPT2, S0, S1, VOLADO_N, VOLADO_O, rect_sd

DC = dz.g.DC
_t, _n, _p0 = DC.t, DC.n, DC.p0
# (u, v) -> (x, y) = (-d, -s)
_M = [-_n[0], -_n[1], -_t[0], -_t[1], float(np.dot(_n, _p0)), float(np.dot(_t, _p0))]


def local(geom):
    return affinity.affine_transform(geom, _M)


# (x, y) = (-d, -s) -> (u, v)
_MI = [-_n[0], -_t[0], -_n[1], -_t[1], float(_p0[0]), float(_p0[1])]


def local_inv(geom):
    return affinity.affine_transform(geom, _MI)


_NOR = np.asarray(dz.g.NORTE, float)
NORTE_LOCAL = (float(np.dot(_NOR, -_n)), float(np.dot(_NOR, -_t)))   # norte en el dibujo del edificio (x, y)


def L(s, d):
    """Punto (s, d) en coordenadas de dibujo del edificio."""
    return (-d, -s)


def RL(s0, s1, d0, d1):
    return box(-d1, -s1, -d0, -s0)


@dataclass
class Ambiente:
    nombre: str
    poly: Polygon            # coordenadas locales (x, y)
    piso: int
    uso: str = ""            # cocina, servicio, publico, sshh, circulacion, exterior, escenario
    mostrar_area: bool = True


@dataclass
class Equipo:
    nombre: str
    poly: Polygon
    piso: int
    tipo: str = "equipo"     # equipo, mueble, sanitario, mesa
    etiqueta: str = ""


@dataclass
class Puerta:
    p0: tuple                # bisagra (local)
    p1: tuple                # extremo de la hoja cerrada (local)
    piso: int
    lado: int = 1            # +1/-1: hacia qué lado abre
    tipo: str = "batiente"   # batiente, corrediza, plegable, vano


# --------------------------------------------------------------------------
# Muros: exteriores del 1.er piso (las fachadas lateral y de ingreso son mamparas de vidrio)
# --------------------------------------------------------------------------
ESP_MURO = 0.15
ENVOLVENTE_1 = RL(S0, S1, D0, D1)
LOSA2_L = local(dz.LOSA2)
PORCHE_L = local(dz.PORCHE)

# ---- 1.er piso -------------------------------------------------------------
AMB = []
EQ = []
PUERTAS = []


def amb(nombre, s0, s1, d0, d1, piso, uso, mostrar=True):
    a = Ambiente(nombre, RL(s0, s1, d0, d1), piso, uso, mostrar)
    AMB.append(a)
    return a


def eq(nombre, s0, s1, d0, d1, piso, tipo="equipo", etiqueta=""):
    e = Equipo(nombre, RL(s0, s1, d0, d1), piso, tipo, etiqueta)
    EQ.append(e)
    return e


# Franja de servicio (junto a la calzada): d 12.4-17.9. El ingreso de servicio es un pasillo transversal que
# entra desde la vereda y llega a la cocina por el pasillo frío (lejos de la línea de fuego).
amb("SS.HH. y vestidor del personal", 7.5, 8.8, 12.4, 14.6, 1, "sshh")
amb("Almacén de insumos", 7.5, 8.8, 14.6, 17.9, 1, "servicio")
amb("Ingreso de servicio", 8.8, 10.0, 12.4, 17.9, 1, "circulacion")
amb("Cocina: horno pollero, parrilla y freidoras", 10.0, 15.0, 12.4, 17.9, 1, "cocina")
amb("Lavado de vajilla", 15.0, 18.5, 12.4, 14.4, 1, "cocina")
amb("Preparación fría y maceración", 15.0, 18.5, 14.4, 16.2, 1, "cocina")
amb("Cámara y bebidas", 15.0, 18.5, 16.2, 17.9, 1, "servicio")
# Franja pública (hacia el jardín lateral): d 17.9-22.9
amb("Hall de ingreso", 7.5, 12.3, 17.9, 20.3, 1, "circulacion")
amb("Escalera principal", 7.9, 12.3, 20.3, 22.9, 1, "circulacion", False)
ASCENSOR = (5.6, 7.4, 21.6, 23.4)         # ascensor panorámico exterior de 2 paradas en el porche de ingreso,
                                          # cabina 1.20 × 1.40 m (A.120); puertas hacia el ingreso (d = 21.6)
amb("Ascensor", *ASCENSOR, 1, "circulacion", False)
amb("Despacho, caja y mesas", 12.3, 15.0, 17.9, 22.9, 1, "publico")
amb("Lavatorios", 15.0, 16.2, 17.9, 22.9, 1, "sshh", False)
amb("SS.HH. accesible", 16.2, 18.5, 17.9, 20.0, 1, "sshh")
amb("SS.HH. damas", 16.2, 18.5, 20.0, 21.5, 1, "sshh")
amb("SS.HH. varones", 16.2, 18.5, 21.5, 22.9, 1, "sshh")

# Equipos de cocina (línea de fuego contra el muro este, bajo una campana continua de 5.0 m)
eq("Horno pollero 1 (leña, 40 pollos)", 10.15, 11.65, 12.55, 13.65, 1, "equipo", "HP-1")
eq("Horno pollero 2 (leña, 40 pollos)", 11.75, 13.25, 12.55, 13.65, 1, "equipo", "HP-2")
eq("Parrilla a carbón", 13.35, 14.45, 12.55, 13.45, 1, "equipo", "PA")
eq("Freidoras (2)", 14.45, 14.95, 12.55, 13.35, 1, "equipo", "FR")
eq("Campana extractora", 10.05, 15.0, 12.4, 13.75, 1, "campana")
eq("Mesa de trabajo (isla)", 10.8, 14.2, 14.7, 15.5, 1, "mueble", "MT")
eq("Pase caliente y despacho", 10.8, 14.6, 17.3, 17.9, 1, "mueble", "PC")
eq("Lavadero de 2 pozas", 15.3, 17.1, 12.55, 13.2, 1, "sanitario", "LV")
eq("Lavavajilla y escurridor", 17.1, 18.35, 12.55, 13.2, 1, "mueble", "")
eq("Mesa de maceración", 15.6, 18.0, 14.65, 15.35, 1, "mueble", "MM")
eq("Conservadoras y cámara", 15.25, 18.35, 17.2, 17.8, 1, "equipo", "CF")
eq("Estantería de insumos", 7.55, 8.0, 14.8, 17.8, 1, "mueble", "")
eq("Inodoro", 7.6, 8.25, 12.6, 13.05, 1, "sanitario", "")
eq("Lavatorio", 7.6, 8.05, 13.55, 14.1, 1, "sanitario", "")
eq("Mostrador de despacho y caja", 12.4, 14.9, 17.95, 18.65, 1, "mueble", "DC")

# Mesas del 1.er piso: 2 mesas de 2 en el despacho; porches con mesas de 4 (se deja libre el frente de la puerta
# plegable del despacho, s 11.6-15.6, para salir al jardín lateral)
MESAS_1 = [RL(13.3, 14.0, 20.25, 20.95), RL(13.3, 14.0, 21.85, 22.55)]
for s_c in (8.4, 10.4, 16.3):                       # porche lateral (bajo el volado)
    MESAS_1.append(RL(s_c - 0.45, s_c + 0.45, 23.45, 24.35))
for d_c in (13.6, 15.6):                             # porche de ingreso (bajo el volado)
    MESAS_1.append(RL(6.1, 6.9, d_c - 0.45, d_c + 0.45))

# aparatos sanitarios del 1.er piso
eq("Inodoro accesible", 17.8, 18.45, 19.3, 19.75, 1, "sanitario", "")
eq("Lavatorio accesible", 17.95, 18.4, 18.1, 18.65, 1, "sanitario", "")
eq("Inodoro", 17.8, 18.45, 20.52, 20.98, 1, "sanitario", "")
eq("Inodoro", 17.8, 18.45, 22.27, 22.73, 1, "sanitario", "")
eq("Urinario", 16.95, 17.35, 22.55, 22.85, 1, "sanitario", "")
for d_c in (21.25, 21.85, 22.45):
    eq("Lavatorio", 15.05, 15.5, d_c - 0.25, d_c + 0.25, 1, "sanitario", "")

PUERTAS += [
    Puerta(L(8.95, D0), L(9.85, D0), 1, -1),                     # ingreso de servicio (desde la vereda)
    Puerta(L(S0, 18.4), L(S0, 20.2), 1, 1, "corrediza"),          # ingreso principal (fachada de ingreso)
    Puerta(L(12.5, D1), L(15.0, D1), 1, 1, "plegable"),           # despacho -> porche lateral
    Puerta(L(10.0, 15.8), L(10.0, 16.7), 1, 1),                   # ingreso de servicio -> cocina (pasillo frío)
    Puerta(L(8.8, 13.2), L(8.8, 13.9), 1, -1),                    # SS.HH. y vestidor del personal
    Puerta(L(8.8, 15.0), L(8.8, 15.9), 1, 1, "corrediza"),         # almacén
    Puerta(L(15.0, 13.3), L(15.0, 14.2), 1, 1, "vano"),            # cocina -> lavado
    Puerta(L(15.0, 15.3), L(15.0, 16.1), 1, 1, "vano"),            # cocina -> maceración
    Puerta(L(15.0, 16.4), L(15.0, 17.2), 1, -1),                   # cámara
    Puerta(L(16.2, 18.1), L(16.2, 19.1), 1, -1),                   # SS.HH. accesible (0.90 útil)
    Puerta(L(16.2, 20.2), L(16.2, 21.0), 1, -1),                   # damas
    Puerta(L(16.2, 21.65), L(16.2, 22.45), 1, -1),                 # varones
    Puerta(L(15.0, 19.6), L(15.0, 20.8), 1, 1, "vano"),            # despacho -> lavatorios
    Puerta(L(12.3, 20.7), L(12.3, 21.5), 1, 1),                    # depósito bajo la escalera
]

# ---- 2.º piso --------------------------------------------------------------
# Franja de servicio bajo el techo del bar: SS.HH. al frente (se entra desde el volado de ingreso), bar al
# centro, depósito al fondo junto al pasillo que lleva a la escalera exterior (abastecimiento y carga de equipos del escenario).
amb("SS.HH. accesible", 7.5, 10.0, 12.4, 14.4, 2, "sshh")
amb("SS.HH. damas", 7.5, 10.0, 14.4, 16.2, 2, "sshh")
amb("SS.HH. varones", 7.5, 10.0, 16.2, 17.9, 2, "sshh")
amb("Bar y bebidas", 10.0, 15.0, 12.4, 17.9, 2, "publico")
amb("Depósito del bar", 15.0, 17.3, 12.4, 17.9, 2, "servicio")
amb("Pasillo de servicio y evacuación", 17.3, 18.5, 12.4, 17.9, 2, "circulacion", False)
ESCENARIO = RL(14.5, 18.5, 17.9, 23.9)
AMB.append(Ambiente("Escenario (+0.40)", ESCENARIO, 2, "escenario"))
TERRAZA = LOSA2_L.difference(unary_union([RL(S0, S1, D0, EJES_D[1]), ESCENARIO, RL(7.9, 12.3, 20.3, 22.9),
                                          RL(*ASCENSOR)]))
AMB.append(Ambiente("Terraza exterior", TERRAZA, 2, "exterior"))
AMB.append(Ambiente("Escalera principal", RL(7.9, 12.3, 20.3, 22.9), 2, "circulacion", False))
AMB.append(Ambiente("Ascensor", RL(*ASCENSOR), 2, "circulacion", False))

eq("Barra de atención (4.6 m)", 10.2, 14.8, 15.35, 15.95, 2, "mueble", "BA")
eq("Contrabarra: cámaras y lavavasos", 10.2, 14.8, 13.05, 13.75, 2, "mueble", "CB")
eq("Ducto de chimeneas y campana", 10.15, 13.35, 12.4, 13.0, 2, "ducto", "DCH")
eq("Tarima del escenario", 14.5, 18.5, 17.9, 23.9, 2, "escenario")
# aparatos sanitarios del 2.º piso (inodoros, urinarios y lavatorios)
eq("Inodoro accesible", 9.15, 9.85, 13.0, 13.5, 2, "sanitario", "")
eq("Lavatorio accesible", 7.65, 8.15, 12.55, 13.15, 2, "sanitario", "")
for d_c in (14.85, 15.75):
    eq("Inodoro", 9.2, 9.85, d_c - 0.22, d_c + 0.22, 2, "sanitario", "")
eq("Lavatorio", 7.65, 8.15, 15.5, 16.05, 2, "sanitario", "")
eq("Inodoro", 9.2, 9.85, 17.25, 17.7, 2, "sanitario", "")
for s_c in (8.3, 8.85):
    eq("Urinario", s_c - 0.2, s_c + 0.2, 17.55, 17.85, 2, "sanitario", "")
eq("Lavatorio", 7.65, 8.15, 16.35, 16.9, 2, "sanitario", "")
PUERTAS += [
    Puerta(L(S0, 12.9), L(S0, 13.9), 2, -1),                      # SS.HH. accesible (0.90 útil)
    Puerta(L(S0, 14.6), L(S0, 15.4), 2, -1),                      # SS.HH. damas
    Puerta(L(S0, 16.8), L(S0, 17.6), 2, -1),                      # SS.HH. varones
    Puerta(L(17.3, D0), L(18.5, D0), 2, 1, "vano"),               # salida a la escalera exterior
    Puerta(L(15.0, 13.9), L(15.0, 14.8), 2, 1),                    # depósito desde la zona de barra
    Puerta(L(17.3, 13.2), L(17.3, 14.1), 2, -1),                   # depósito desde el pasillo
]
MESAS_2 = []
for s_c, d_c in ((6.5, 19.2), (8.6, 23.9), (10.6, 23.9), (13.4, 19.4), (13.4, 21.4), (13.4, 23.5)):
    MESAS_2.append(RL(s_c - 0.4, s_c + 0.4, d_c - 0.4, d_c + 0.4))
TABURETES = [L(s_c, 16.35) for s_c in np.arange(10.5, 14.6, 0.6)]

# --------------------------------------------------------------------------
# Tabiques interiores (s0, d0, s1, d1, tipo): "tabique" (drywall o ladrillo), "pase" (ventana de despacho),
# "baranda" (baranda de escalera). Las puertas se recortan con PUERTAS.
# --------------------------------------------------------------------------
B1 = EJES_D[1]
TABIQUES = {
    1: [(8.8, D0, 8.8, B1, "tabique"), (S0, 14.6, 8.8, 14.6, "tabique"),
        (10.0, D0, 10.0, B1, "tabique"), (15.0, D0, 15.0, B1, "tabique"),
        (15.0, 14.4, S1, 14.4, "tabique"), (15.0, 16.2, S1, 16.2, "tabique"),
        (S0, B1, 10.8, B1, "tabique"), (10.8, B1, 14.6, B1, "pase"), (14.6, B1, S1, B1, "tabique"),
        (15.0, B1, 15.0, D1, "tabique"), (16.2, B1, 16.2, D1, "tabique"),
        (16.2, 20.0, S1, 20.0, "tabique"), (16.2, 21.5, S1, 21.5, "tabique"),
        (10.3, 20.3, 12.3, 20.3, "tabique"), (12.3, 20.3, 12.3, D1, "tabique")],
    2: [(10.0, D0, 10.0, B1, "tabique"), (15.0, D0, 15.0, B1, "tabique"), (17.3, D0, 17.3, B1, "tabique"),
        (S0, 14.4, 10.0, 14.4, "tabique"), (S0, 16.2, 10.0, 16.2, "tabique"),
        (8.2, 20.3, 12.3, 20.3, "baranda"), (12.3, 20.3, 12.3, D1, "baranda")],
}
DEPOSITO_ESCALERA = RL(10.3, 12.3, 20.3, D1)       # bajo el tramo 2 y el descanso (altura libre < 2.10 m)


# --------------------------------------------------------------------------
# Escaleras
# --------------------------------------------------------------------------
N_CONTRA, CONTRA, HUELLA = 22, NPT2 / 22, 0.28


def escalera_U():
    """Escalera principal en U: 2 tramos de 1.20 m y 11 contrapasos, descanso de 1.20 m."""
    tramo1 = [RL(8.2 + i * HUELLA, 8.2 + (i + 1) * HUELLA, 21.7, 22.9) for i in range(10)]   # sube hacia el sur
    descanso = RL(11.0, 12.3, 20.3, 22.9)
    tramo2 = [RL(11.0 - (i + 1) * HUELLA, 11.0 - i * HUELLA, 20.3, 21.5) for i in range(10)]  # sube hacia el norte
    return tramo1, descanso, tramo2


def escalera_exterior():
    """Escalera de evacuación y servicio, adosada a la fachada este (tramos de 1.20 m)."""
    s0, s1, s2, s3, s4, s5 = dz.S_ESC_EXT
    d0, d1 = dz.D_VEREDA
    t1 = [RL(s1 + i * HUELLA, s1 + (i + 1) * HUELLA, d0, d1) for i in range(10)]
    desc = RL(s2, s3, d0, d1)
    t2 = [RL(s3 + i * HUELLA, s3 + (i + 1) * HUELLA, d0, d1) for i in range(10)]
    llegada = RL(s4, s5, d0, d1)
    return t1, desc, t2, llegada


# --------------------------------------------------------------------------
# Techos (dos aguas): bar (franja de servicio completa) y escenario (franja lateral, ejes 2-3)
# --------------------------------------------------------------------------
TECHO_BAR = RL(S0 - VOLADO_N, S1 + 0.6, D0 - 0.6, EJES_D[1] + 0.3)  # cumbrera a lo largo de s; cubre el volado de ingreso
TECHO_ESC = RL(EJES_S[1], S1 + 0.6, EJES_D[1] + 0.3, D1 + VOLADO_O)  # cumbrera a lo largo de d


def area(nombre, piso):
    return sum(a.poly.area for a in AMB if a.nombre == nombre and a.piso == piso)


def cuadro_areas_edificio():
    filas = []
    for piso in (1, 2):
        for a in AMB:
            if a.piso == piso:
                filas.append((piso, a.nombre, a.poly.area))
    return filas


if __name__ == "__main__":
    for piso, n, a in cuadro_areas_edificio():
        print(piso, f"{n:45s} {a:6.1f}")
    print("terraza", round(TERRAZA.area, 1), "losa 2", round(LOSA2_L.area, 1), "porche", round(PORCHE_L.area, 1))
    print("mesas 1er piso", len(MESAS_1), "mesas 2.º piso", len(MESAS_2))
