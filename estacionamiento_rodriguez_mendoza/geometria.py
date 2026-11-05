"""
Geometría del terreno y distribución del estacionamiento.

Sistema de coordenadas local (metros):
    origen  = vértice B (extremo sur del frente a Jr. Rodríguez de Mendoza)
    eje u   = a lo largo del lindero B->C (lado de 40 m, colindante)
    eje v   = perpendicular a B->C, hacia el interior del terreno

Vértices:
    A  esquina Jr. Rodríguez de Mendoza / calle lateral
    B  extremo del frente sobre Jr. Rodríguez de Mendoza (junto a edificaciones)
    C  esquina posterior (colindantes)
    D  esquina sobre la calle lateral (fondo)

Lados medidos (Google Maps): AB = 30 m, BC = 40 m, CD = 30 m, DA = 20 m.
El ángulo en A (~130°) se estimó sobre la imagen satelital; con él quedan
definidos los demás (B ≈ 60°, C ≈ 80°, D ≈ 90°), que coinciden con lo que se
ve en las cuatro capturas.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union

# --------------------------------------------------------------------------
# Parámetros de diseño
# --------------------------------------------------------------------------
LADO_AB = 30.0
LADO_BC = 40.0
LADO_CD = 30.0
LADO_DA = 20.0
ANGULO_A = 130.0          # grados, estimado de la imagen satelital
RUMBO_AB = 155.0          # rumbo aproximado de A->B (desde el norte, horario)

FRANJA_MURO = 0.25        # franja perimetral para cerco / columnas de cerco
ANCHO_PLAZA = 2.50        # RNE A.010, uso público, 3 o más continuos
LARGO_PLAZA = 5.00
ANCHO_ACCESIBLE = 3.80    # RNE A.120
PASILLO = 6.50            # distancia entre plazas opuestas (criterio conservador)
ANCHO_PORTON = 3.00
PASO_MOTOS = 2.00         # paso para motos / mototaxis hacia la zona interior

# Portones (distancias medidas a lo largo del lindero)
P1_DESDE_D = (6.5, 9.5)   # portón de INGRESO sobre la calle lateral (lado DA)
P2_DESDE_B = (7.5, 10.5)  # portón de SALIDA sobre Jr. Rodríguez de Mendoza (lado AB)
PEATONAL_DESDE_B = (6.2, 7.2)
PEATONAL2_DESDE_A = (5.0, 6.2)

# Cobertura (voladizo asimétrico)
VOLADO_POSTERIOR = 0.10   # la cobertura empieza a 0.10 m del cerco
VOLADO_SOBRE_PASILLO = 0.55
COLUMNA_DESDE_FONDO = 1.00  # eje de columna a 1.00 m del fondo de la plaza
LADO_COLUMNA = 0.20


# --------------------------------------------------------------------------
# Terreno
# --------------------------------------------------------------------------
def _resolver_vertices():
    """Calcula A, B, C, D en el sistema local a partir de lados + ángulo en A."""
    # Marco auxiliar: A en el origen, B sobre +x, terreno hacia +y
    a = np.array([0.0, 0.0])
    b = np.array([LADO_AB, 0.0])
    ang = math.radians(ANGULO_A)
    d = LADO_DA * np.array([math.cos(ang), math.sin(ang)])
    # C: a LADO_BC de B y LADO_CD de D, del lado opuesto a A respecto de BD
    bd = d - b
    dist = np.linalg.norm(bd)
    ubd = bd / dist
    x = (LADO_BC**2 - LADO_CD**2 + dist**2) / (2 * dist)
    h = math.sqrt(LADO_BC**2 - x**2)
    perp = np.array([-ubd[1], ubd[0]])
    if np.dot(a - b, perp) > 0:
        perp = -perp
    c = b + x * ubd + h * perp

    # Cambio al sistema local (origen B, u = B->C)
    u = (c - b) / np.linalg.norm(c - b)
    v = np.array([-u[1], u[0]])
    if np.dot(a - b, v) < 0:
        v = -v

    def loc(p):
        return np.array([np.dot(p - b, u), np.dot(p - b, v)])

    pts = {k: loc(p) for k, p in dict(A=a, B=b, C=c, D=d).items()}
    # Ángulo de u medido desde el norte: rumbo(B->C)
    ang_bc_aux = math.degrees(math.atan2(*(c - b)[::-1]))
    rumbo_u = (RUMBO_AB - ang_bc_aux) % 360
    return pts, rumbo_u


VERT, RUMBO_U = _resolver_vertices()
A, B, C, D = (VERT[k] for k in "ABCD")
LOTE = Polygon([B, C, D, A])
UTIL = LOTE.buffer(-FRANJA_MURO, join_style=2)


def angulo_interior(p_prev, p, p_next):
    v1 = p_prev - p
    v2 = p_next - p
    cosang = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
    return math.degrees(math.acos(np.clip(cosang, -1, 1)))


ANGULOS = {
    "A": angulo_interior(D, A, B),
    "B": angulo_interior(A, B, C),
    "C": angulo_interior(B, C, D),
    "D": angulo_interior(C, D, A),
}

# Vector "norte" en coordenadas locales (para la flecha de norte)
_ang_norte = math.radians(RUMBO_U)          # el norte está girado RUMBO_U (antihorario) desde +u
NORTE = np.array([math.cos(_ang_norte), math.sin(_ang_norte)])


# --------------------------------------------------------------------------
# Marcos de borde
# --------------------------------------------------------------------------
@dataclass
class Borde:
    nombre: str
    p0: np.ndarray
    p1: np.ndarray

    @property
    def t(self):
        d = self.p1 - self.p0
        return d / np.linalg.norm(d)

    @property
    def n(self):
        t = self.t
        n = np.array([-t[1], t[0]])
        centro = np.array(LOTE.centroid.coords[0])
        if np.dot(centro - self.p0, n) < 0:
            n = -n
        return n

    @property
    def largo(self):
        return float(np.linalg.norm(self.p1 - self.p0))

    def punto(self, s, d=0.0):
        return self.p0 + s * self.t + d * self.n

    def rect(self, s0, s1, d0, d1) -> Polygon:
        return Polygon([self.punto(s0, d0), self.punto(s1, d0),
                        self.punto(s1, d1), self.punto(s0, d1)])

    def dist(self, p):
        return float(np.dot(np.asarray(p) - self.p0, self.n))


BC = Borde("BC", B, C)          # lindero colindante de 40 m
DC = Borde("DC", D, C)          # fondo (medido desde D hacia C)
DA = Borde("DA", D, A)          # frente a calle lateral (medido desde D)
BA = Borde("BA", B, A)          # frente a Jr. Rodríguez de Mendoza (desde B)


def banda(borde: Borde, d0, d1, extra=60.0) -> Polygon:
    """Franja paralela a un borde entre distancias d0 y d1 (recortada al lote)."""
    r = borde.rect(-extra, borde.largo + extra, d0, d1)
    return r.intersection(LOTE)


def semiplano(borde: Borde, dmin, extra=80.0) -> Polygon:
    return banda(borde, dmin, dmin + extra, extra)


# --------------------------------------------------------------------------
# Elementos del proyecto
# --------------------------------------------------------------------------
@dataclass
class Plaza:
    codigo: str
    fila: str
    poly: Polygon
    tipo: str = "auto"          # auto | accesible
    borde: Borde | None = None
    s0: float = 0.0
    s1: float = 0.0
    d0: float = 0.0
    d1: float = 0.0


@dataclass
class Fila:
    nombre: str
    borde: Borde
    d0: float                   # distancia al borde del fondo de plaza
    d1: float                   # distancia al borde del frente de plaza
    plazas: list = field(default_factory=list)
    lado_fondo: str = "d0"      # dónde está el fondo de la plaza (columnas)

    @property
    def s_ini(self):
        return min(p.s0 for p in self.plazas)

    @property
    def s_fin(self):
        return max(p.s1 for p in self.plazas)

    @property
    def lineas(self):
        """Posiciones s de las líneas divisorias de plazas."""
        xs = sorted({round(p.s0, 4) for p in self.plazas} | {round(p.s1, 4) for p in self.plazas})
        return xs


def _valida(poly: Polygon, prohibido: Polygon | None) -> bool:
    if not UTIL.buffer(1e-6).contains(poly):
        return False
    if prohibido is not None and poly.intersection(prohibido).area > 1e-4:
        return False
    return True


def colocar_fila(nombre, borde, d0, d1, anchos, prohibido=None, s_inicio=None,
                 desde_fin=False, paso=0.005, max_plazas=None):
    """Coloca plazas contiguas a lo largo de `borde`.

    Busca la primera posición válida (o la última si desde_fin) y avanza
    mientras quepan. `anchos` es la secuencia de anchos (se repite el último).
    """
    fila = Fila(nombre, borde, d0, d1)
    L = borde.largo
    def ancho_i(i):
        return anchos[i] if i < len(anchos) else anchos[-1]

    if not desde_fin:
        s = 0.0 if s_inicio is None else s_inicio
        while s < L:
            if _valida(borde.rect(s, s + ancho_i(0), d0, d1), prohibido):
                break
            s += paso
        i = 0
        while True:
            w = ancho_i(i)
            r = borde.rect(s, s + w, d0, d1)
            if not _valida(r, prohibido) or (max_plazas and i >= max_plazas):
                break
            fila.plazas.append(Plaza("", nombre, r, borde=borde, s0=s, s1=s + w, d0=d0, d1=d1))
            s += w
            i += 1
    else:
        s = L if s_inicio is None else s_inicio
        while s > 0:
            if _valida(borde.rect(s - ancho_i(0), s, d0, d1), prohibido):
                break
            s -= paso
        i = 0
        while True:
            w = ancho_i(i)
            r = borde.rect(s - w, s, d0, d1)
            if not _valida(r, prohibido) or (max_plazas and i >= max_plazas):
                break
            fila.plazas.append(Plaza("", nombre, r, borde=borde, s0=s - w, s1=s, d0=d0, d1=d1))
            s -= w
            i += 1
        fila.plazas.sort(key=lambda p: p.s0)
    return fila


# Distancias de las bandas
D_FILA_EXT = (FRANJA_MURO, FRANJA_MURO + LARGO_PLAZA)                          # 0.25 - 5.25
D_PASILLO = (D_FILA_EXT[1], D_FILA_EXT[1] + PASILLO)                           # 5.25 - 11.75
D_FILA_INT = (D_PASILLO[1], D_PASILLO[1] + LARGO_PLAZA)                        # 11.75 - 16.75

# Pasillos de circulación (en L)
PASILLO_A = banda(DC, *D_PASILLO).intersection(UTIL)                           # paralelo al fondo
PASILLO_B = banda(BC, *D_PASILLO).intersection(semiplano(DC, D_PASILLO[0])).intersection(UTIL)
CIRCULACION = unary_union([PASILLO_A, PASILLO_B])

# ---- Fila A: a lo largo del fondo (C-D), toda la longitud ----
FILA_A = colocar_fila("A", DC, *D_FILA_EXT, [ANCHO_PLAZA])

# ---- Fila B: a lo largo del lindero B-C, desde el frente hasta el pasillo A ----
#      Las dos primeras (junto a la salida peatonal) son accesibles.
_prohibido_B = semiplano(DC, -50).difference(semiplano(DC, D_PASILLO[1]))       # dist_DC < 11.75
FILA_B = colocar_fila("B", BC, *D_FILA_EXT, [ANCHO_ACCESIBLE, ANCHO_ACCESIBLE, ANCHO_PLAZA],
                      prohibido=_prohibido_B)
for p in FILA_B.plazas[:2]:
    p.tipo = "accesible"

# ---- Fila C: isla, frente al pasillo B (paralela a B-C) ----
FILA_C = colocar_fila("C", BC, *D_FILA_INT, [ANCHO_PLAZA], prohibido=_prohibido_B)

# ---- Fila D: isla, frente al pasillo A (paralela al fondo), deja paso de motos junto al cerco ----
_ocupado_C = unary_union([p.poly for p in FILA_C.plazas]).buffer(0.10, join_style=2)
_bajo_isla = semiplano(BC, -50).difference(semiplano(BC, D_PASILLO[1]))       # dist_BC < 11.75
FILA_D = colocar_fila("D", DC, *D_FILA_INT, [ANCHO_PLAZA],
                      prohibido=unary_union([_ocupado_C, _bajo_isla]), desde_fin=True)
# recortar para dejar el paso de motos junto al cerco de la calle lateral
while FILA_D.plazas and FILA_D.plazas[0].s0 < FRANJA_MURO + PASO_MOTOS - 1e-6:
    FILA_D.plazas.pop(0)

FILAS = [FILA_A, FILA_B, FILA_C, FILA_D]


def numerar():
    n = 1
    for fila in FILAS:
        orden = fila.plazas
        for p in orden:
            p.codigo = f"{n:02d}"
            n += 1


numerar()
PLAZAS = [p for f in FILAS for p in f.plazas]


# --------------------------------------------------------------------------
# Portones, accesos y zonas complementarias
# --------------------------------------------------------------------------
def segmento(borde: Borde, s0, s1, d=0.0):
    return LineString([borde.punto(s0, d), borde.punto(s1, d)])


PORTON_INGRESO = segmento(DA, *P1_DESDE_D)
PORTON_SALIDA = segmento(BA, *P2_DESDE_B)
PUERTA_PEATONAL = segmento(BA, *PEATONAL_DESDE_B)
AB_desde_A = Borde("AB", A, B)
PUERTA_PEATONAL_2 = segmento(AB_desde_A, *PEATONAL2_DESDE_A)

# Garita de control (1.50 x 1.50) en la esquina B, junto a la salida
_s_garita_fin = FILA_B.s_ini - 0.15
GARITA = BC.rect(_s_garita_fin - 1.50, _s_garita_fin, FRANJA_MURO + 0.10, FRANJA_MURO + 1.60)

# Zona interior de la isla (servicios + motos)
_isla = (semiplano(DC, D_PASILLO[1]).intersection(semiplano(BC, D_PASILLO[1]))
         .intersection(UTIL))
_filas_isla = unary_union([p.poly for p in FILA_C.plazas + FILA_D.plazas])
ZONA_INTERIOR = _isla.difference(_filas_isla.buffer(0.05, join_style=2))
# paso de motos (entre fila D y el cerco de la calle lateral)
PASO_MOTO = DC.rect(FRANJA_MURO, FILA_D.s_ini - 0.05, D_FILA_INT[0], D_FILA_INT[1])

# Módulo de servicios: SS.HH. + depósito, apoyado en el frente (cerca de A)
_sv_borde = Borde("AB", A, B)
SSHH = _sv_borde.rect(0.80, 3.00, FRANJA_MURO, FRANJA_MURO + 2.20).intersection(UTIL)
DEPOSITO = _sv_borde.rect(3.00, 4.50, FRANJA_MURO, FRANJA_MURO + 2.20).intersection(UTIL)

# Plazas de motos / mototaxis en la zona interior (motos 1.00 x 2.20; mototaxis 1.50 x 3.00)
def _plazas_motos():
    motos, mototaxis = [], []
    servicios = unary_union([SSHH, DEPOSITO]).buffer(0.90, join_style=2)
    # motos: en batería detrás de la fila D (perpendiculares al fondo C-D)
    d0 = D_FILA_INT[1] + 0.10
    s = FILA_D.s_ini
    while s + 1.0 <= FILA_D.s_fin + 1e-6:
        r = DC.rect(s, s + 1.00, d0, d0 + 2.20)
        if UTIL.contains(r) and r.intersection(servicios).area < 1e-6:
            motos.append(r)
        s += 1.00
    ocup = unary_union(motos + [p.poly for p in FILA_D.plazas]).buffer(0.30, join_style=2)
    # mototaxis: en batería detrás de la fila C (mirando hacia el interior)
    d0 = D_FILA_INT[1] + 0.10
    u = FILA_C.s_ini
    while u + 1.5 <= FILA_C.s_fin:
        r = BC.rect(u, u + 1.50, d0, d0 + 3.00)
        if UTIL.contains(r) and r.intersection(ocup).area < 1e-6 and r.intersection(servicios).area < 1e-6:
            mototaxis.append(r)
            u += 1.50
        else:
            u += 0.05
    return motos, mototaxis


MOTOS, MOTOTAXIS = _plazas_motos()


# --------------------------------------------------------------------------
# Coberturas y columnas
# --------------------------------------------------------------------------
@dataclass
class Cobertura:
    nombre: str
    fila: Fila
    poly: Polygon
    columnas: list           # lista de (Point centro, s, d)
    d_atras: float
    d_frente: float
    d_col: float
    s0: float
    s1: float
    mira_hacia: int          # +1 si el frente de plaza está a mayor d


def _cobertura(nombre, fila: Fila, cols_idx, fondo_en_d0=True, extremo_extra=0.0):
    b = fila.borde
    if fondo_en_d0:
        d_atras = fila.d0 - (FRANJA_MURO - VOLADO_POSTERIOR) if fila.d0 <= FRANJA_MURO + 1e-6 else fila.d0 - 0.15
        d_frente = fila.d1 + VOLADO_SOBRE_PASILLO
        d_col = fila.d0 + COLUMNA_DESDE_FONDO
        mira = 1
    else:
        d_atras = fila.d1 + 0.15
        d_frente = fila.d0 - VOLADO_SOBRE_PASILLO
        d_col = fila.d1 - COLUMNA_DESDE_FONDO
        mira = -1
    s0 = fila.s_ini - extremo_extra
    s1 = fila.s_fin + extremo_extra
    poly = b.rect(s0, s1, min(d_atras, d_frente), max(d_atras, d_frente))
    lineas = fila.lineas
    cols = []
    for i in cols_idx:
        s = lineas[i]
        cols.append((Point(*b.punto(s, d_col)), s, d_col))
    return Cobertura(nombre, fila, poly, cols, d_atras, d_frente, d_col, s0, s1, mira)


def _indices_columnas(n_lineas, cada=3):
    """Líneas divisorias con columna: cada 3 plazas, centradas en la fila."""
    n_plazas = n_lineas - 1
    if n_plazas <= cada:
        return [0, n_lineas - 1]
    resto = n_plazas % cada
    ini = resto // 2 if resto != 0 else 0
    idx = list(range(ini, n_lineas, cada))
    if idx[-1] != n_lineas - 1 and (n_lineas - 1 - idx[-1]) > cada // 2 + 1:
        idx.append(n_lineas - 1)
    return idx


def _cols_fila_B(fila):
    # anchos: 3.80, 3.80, 2.50 x n  -> columnas en extremos y cada ~7.5 m
    lin = fila.lineas
    objetivo = []
    s = lin[0]
    objetivo.append(0)
    while True:
        cand = [i for i, x in enumerate(lin) if x - s <= 7.60 + 1e-6 and x > s]
        if not cand:
            break
        j = max(cand)
        objetivo.append(j)
        s = lin[j]
        if j == len(lin) - 1:
            break
    return objetivo


COB_A = _cobertura("T-1", FILA_A, _indices_columnas(len(FILA_A.lineas)))
COB_B = _cobertura("T-2", FILA_B, _cols_fila_B(FILA_B))
COB_C = _cobertura("T-3", FILA_C, [0, 3, 6] if len(FILA_C.lineas) == 7 else _indices_columnas(len(FILA_C.lineas)),
                   fondo_en_d0=False)
COB_D = _cobertura("T-4", FILA_D, [0, len(FILA_D.lineas) - 1], fondo_en_d0=False)
COBERTURAS = [COB_A, COB_B, COB_C, COB_D]
COLUMNAS = [(cob.nombre, i + 1, c[0]) for cob in COBERTURAS for i, c in enumerate(cob.columnas)]


# --------------------------------------------------------------------------
# Resumen y verificaciones
# --------------------------------------------------------------------------
def verificar():
    errores = []
    polys = [p.poly for p in PLAZAS]
    for i, p in enumerate(PLAZAS):
        if not UTIL.buffer(1e-6).contains(p.poly):
            errores.append(f"Plaza {p.codigo} fuera del área útil")
        if p.poly.intersection(CIRCULACION).area > 1e-3:
            errores.append(f"Plaza {p.codigo} invade la circulación")
        for q in PLAZAS[i + 1:]:
            if p.poly.intersection(q.poly).area > 1e-3:
                errores.append(f"Plazas {p.codigo} y {q.codigo} se superponen")
    for cob in COBERTURAS:
        for (pt, s, d) in cob.columnas:
            for p in PLAZAS:
                if p.poly.buffer(-LADO_COLUMNA / 2 + 0.001).contains(pt):
                    errores.append(f"Columna de {cob.nombre} dentro de la plaza {p.codigo}")
            if CIRCULACION.buffer(-0.01).contains(pt):
                errores.append(f"Columna de {cob.nombre} en la circulación")
    # portones dentro de los pasillos
    for nombre, seg in (("P1", PORTON_INGRESO), ("P2", PORTON_SALIDA)):
        mid = seg.interpolate(0.5, normalized=True)
        if CIRCULACION.buffer(FRANJA_MURO + 0.05).distance(mid) > 1e-6:
            errores.append(f"Portón {nombre} no desemboca en un pasillo")
    return errores


def resumen():
    n_auto = sum(1 for p in PLAZAS if p.tipo == "auto")
    n_acc = sum(1 for p in PLAZAS if p.tipo == "accesible")
    area_cob = sum(c.poly.area for c in COBERTURAS)
    return dict(
        area_lote=LOTE.area,
        perimetro=LOTE.length,
        plazas_total=len(PLAZAS),
        plazas_estandar=n_auto,
        plazas_accesibles=n_acc,
        motos=len(MOTOS),
        mototaxis=len(MOTOTAXIS),
        columnas=len(COLUMNAS),
        area_techada=area_cob,
        area_circulacion=CIRCULACION.area,
        area_plazas=sum(p.poly.area for p in PLAZAS),
        filas={f.nombre: len(f.plazas) for f in FILAS},
        angulos=ANGULOS,
        diagonal_AC=float(np.linalg.norm(A - C)),
        diagonal_BD=float(np.linalg.norm(B - D)),
    )


if __name__ == "__main__":
    import json
    print({k: v.round(3).tolist() for k, v in VERT.items()})
    print("Rumbo eje u:", round(RUMBO_U, 1))
    r = resumen()
    print(json.dumps(r, indent=2, default=float))
    print("Errores:", verificar())
    for f in FILAS:
        print(f.nombre, [(p.codigo, round(p.s0, 2), round(p.s1, 2), p.tipo) for p in f.plazas])
    for c in COBERTURAS:
        print(c.nombre, [(round(s, 2)) for (_, s, _) in c.columnas], "d_col", round(c.d_col, 2),
              "area", round(c.poly.area, 1))
