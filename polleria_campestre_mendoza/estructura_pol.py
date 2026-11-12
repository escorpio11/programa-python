"""
Predimensionamiento de la estructura metálica del edificio de la pollería.

Sistema: pórticos de acero con columnas HSS cuadradas y vigas W, grilla de
2 × 2 paños (ejes 1-2-3 cada 5.50 m a lo largo de s; ejes A-B-C a 5.50 y 5.00 m
a lo largo de d), con voladizos de 2.00 m al norte y al oeste en el 2.º piso.
Entrepiso de losa colaborante (steel deck) sobre viguetas W cada ≈ 1.80 m.
Fuerzas sísmicas tomadas por pórticos arriostrados concéntricos en X ubicados en
muros llenos: eje A (paño 2-3), eje C (paño 2-3), eje 1 (paño A-B) y eje 3 (paño B-C).
Techo a dos aguas de panel termoacústico sobre vigas W y correas C.

Normas: RNE E.020 Cargas, E.030 Diseño Sismorresistente, E.050 Suelos, E.060 Concreto
Armado y E.090 Estructuras Metálicas (LRFD: 1.2D + 1.6L; φb = 0.90; φc = 0.90).

IMPORTANTE: es un PREDIMENSIONAMIENTO para anteproyecto y presupuesto. El expediente
técnico debe ser calculado y firmado por un ingeniero civil colegiado, con estudio de
mecánica de suelos (EMS) y la zona sísmica confirmada.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import diseno as dz
import edificio as ed

IN = 25.4
LB_FT = 1.48816                # kg/m por lb/ft
E = 200_000.0                  # MPa
FY_W = 345.0                   # MPa: perfiles W ASTM A572 Gr. 50
FY_HSS = 317.0                 # MPa: tubos HSS ASTM A500 Gr. B (46 ksi)
G = 9.81

# --------------------------------------------------------------------------
# Cargas (kPa) — E.020
# --------------------------------------------------------------------------
CARGAS_LOSA = {
    "Losa colaborante AD-600 cal. 20, e = 12 cm, concreto f'c 210": 2.25,
    "Contrapiso, porcelanato antideslizante e impermeabilización": 1.00,
    "Cielo raso e instalaciones colgadas": 0.30,
}
TABIQUERIA = 0.50              # solo en la franja del bar y SS.HH. (drywall / fibrocemento)
D_LOSA = sum(CARGAS_LOSA.values())
L_TERRAZA = 4.0                # restaurantes, terrazas de uso público
L_ESCENARIO = 7.5              # E.020: escenarios 750 kgf/m². En vigas, columnas y zapatas se aplica a toda la losa
                               # (del lado seguro: la tarima es modular y en eventos puede ampliarse sobre la terraza)
L_ESCALERA = 5.0               # E.020: corredores y escaleras de lugares de asamblea
CARGAS_TECHO = {"Panel termoacústico tipo teja e = 30 mm": 0.12, "Correas C": 0.08,
                "Vigas de techo y arriostres": 0.15, "Luminarias, sonido e instalaciones": 0.05}
D_TECHO = sum(CARGAS_TECHO.values())
LR_TECHO = 0.30                # coberturas livianas
Q_VIENTO = 0.005 * 75.0 ** 2 * G / 1000 * 1.3   # V = 75 km/h, coeficiente neto 1.3

# Sismo (E.030-2018): Mendoza (prov. Rodríguez de Mendoza) figura en zona 2 (Z = 0.25) y un restaurante es categoría C
# (U = 1.0). Se predimensiona del lado seguro con Z = 0.35 (zona 3) y U = 1.3 (terraza con espectáculos, lugar de
# reunión) hasta confirmar con la E.030 vigente (RM 183-2026-VIVIENDA) y el estudio de mecánica de suelos.
Z, U, C_SIS, S_SUELO = 0.35, 1.3, 2.5, 1.15     # U = 1.3: lugar de reunión (terraza con espectáculos)
R0_SCBF = 7.0                   # pórticos especiales concéntricamente arriostrados (SCBF)
Q_ADM = 100.0                   # kPa (1.0 kg/cm²) supuesto -> confirmar con EMS
UTIL_MAX = 0.90                 # margen para conexiones, pandeo lateral en volados y cargas de montaje


# --------------------------------------------------------------------------
# Catálogos (AISC): W [lb/ft, d in, Ix in4, Zx in3]; HSS [lb/ft, A in2, r in, Z in3]
# --------------------------------------------------------------------------
@dataclass
class W:
    nombre: str
    peso: float
    d: float
    Ix: float
    Zx: float

    @property
    def kg_m(self):
        return self.peso * LB_FT

    @property
    def I_mm4(self):
        return self.Ix * IN ** 4

    @property
    def Z_mm3(self):
        return self.Zx * IN ** 3


@dataclass
class HSS:
    nombre: str
    peso: float
    A: float
    r: float
    Z: float

    @property
    def kg_m(self):
        return self.peso * LB_FT

    @property
    def A_mm2(self):
        return self.A * IN ** 2

    @property
    def r_mm(self):
        return self.r * IN


CAT_W = [W("W8x10", 10, 7.89, 30.8, 8.87), W("W8x13", 13, 7.99, 39.6, 11.4), W("W8x15", 15, 8.11, 48.0, 13.6),
         W("W8x18", 18, 8.14, 61.9, 17.0), W("W10x15", 15, 9.99, 68.9, 16.0), W("W10x17", 17, 10.1, 81.9, 18.7),
         W("W10x19", 19, 10.2, 96.3, 21.6), W("W10x22", 22, 10.2, 118, 26.0), W("W12x19", 19, 12.2, 130, 24.7),
         W("W12x22", 22, 12.3, 156, 29.3), W("W12x26", 26, 12.2, 204, 37.2), W("W14x26", 26, 13.9, 245, 40.2),
         W("W14x30", 30, 13.8, 291, 47.3), W("W14x34", 34, 14.0, 340, 54.6), W("W16x31", 31, 15.9, 375, 54.0),
         W("W16x36", 36, 15.9, 448, 64.0), W("W16x40", 40, 16.0, 518, 73.0), W("W18x40", 40, 17.9, 612, 78.4)]
CAT_HSS = [HSS("HSS 3x3x1/4", 8.81, 2.44, 1.08, 2.48), HSS("HSS 4x4x1/4", 12.21, 3.37, 1.52, 4.69),
           HSS("HSS 4x4x3/8", 17.27, 4.78, 1.48, 6.34), HSS("HSS 6x6x1/4", 19.02, 5.24, 2.34, 11.2),
           HSS("HSS 6x6x3/8", 27.48, 7.58, 2.28, 15.8), HSS("HSS 8x8x1/4", 25.82, 7.10, 3.15, 20.5),
           HSS("HSS 8x8x3/8", 37.69, 10.4, 3.10, 29.4)]


def fcr(KL_mm, r_mm, Fy):
    """Esfuerzo crítico de pandeo flexional (E.090 / AISC E3)."""
    lam = KL_mm / r_mm
    Fe = math.pi ** 2 * E / lam ** 2
    if Fy / Fe <= 2.25:
        return 0.658 ** (Fy / Fe) * Fy, lam
    return 0.877 * Fe, lam


# --------------------------------------------------------------------------
# Geometría estructural
# --------------------------------------------------------------------------
LUZ_VIGUETA = dz.EJES_S[1] - dz.EJES_S[0]                 # 5.50 m (a lo largo de s)
SEP_VIGUETAS = (dz.EJES_D[1] - dz.EJES_D[0]) / 3          # ≈ 1.83 m (luz del steel deck)
LUZ_VIGA = dz.EJES_D[1] - dz.EJES_D[0]                    # 5.50 m (a lo largo de d)
ANCHO_TRIB_VIGA = LUZ_VIGUETA                             # eje 2: 2.75 + 2.75 m
H_PISO = dz.NPT2                                          # 3.85 m
H_COL_TECHO = dz.H_ALERO                                  # 7.15 m


def _sel_viga(Mu_kNm, w_L_kNm, L_m, lim=360.0, cantilever=False):
    for s in CAT_W:
        phiMn = 0.9 * FY_W * s.Z_mm3 / 1e6
        if cantilever:
            flecha = w_L_kNm * (L_m * 1000) ** 4 / (8 * E * s.I_mm4)
            lim_f = 2 * L_m * 1000 / lim
        else:
            flecha = 5 * w_L_kNm * (L_m * 1000) ** 4 / (384 * E * s.I_mm4)
            lim_f = L_m * 1000 / lim
        if Mu_kNm <= UTIL_MAX * phiMn and flecha <= 0.95 * lim_f:
            return dict(seccion=s, phiMn=phiMn, Mu=Mu_kNm, ratio=Mu_kNm / phiMn, flecha_mm=flecha, lim_mm=lim_f)
    raise ValueError("sin sección")


def vigueta(L_viva=L_TERRAZA, tab=TABIQUERIA):
    wD = (D_LOSA + tab) * SEP_VIGUETAS
    wL = L_viva * SEP_VIGUETAS
    wu = 1.2 * wD + 1.6 * wL
    Mu = wu * LUZ_VIGUETA ** 2 / 8
    r = _sel_viga(Mu, wL, LUZ_VIGUETA)
    r.update(wu=wu, wD=wD, wL=wL)
    return r


def vigueta_volado():
    """Viguetas que continúan 2.00 m en volado al norte (terraza sobre el ingreso)."""
    wD = D_LOSA * SEP_VIGUETAS + 0.5          # + baranda
    wL = L_TERRAZA * SEP_VIGUETAS
    wu = 1.2 * wD + 1.6 * wL
    Mu = wu * dz.VOLADO_N ** 2 / 2
    r = _sel_viga(Mu, wL, dz.VOLADO_N, cantilever=True)
    r.update(wu=wu)
    return r


def viga_principal():
    """Viga del eje 2 (la más cargada): recibe las viguetas de ambos paños; luz 5.50 m + volado oeste 2.00 m."""
    q = 1.2 * (D_LOSA + TABIQUERIA) + 1.6 * L_ESCENARIO
    wu = q * ANCHO_TRIB_VIGA + 1.2 * 0.6       # + peso propio aprox.
    wL = L_ESCENARIO * ANCHO_TRIB_VIGA
    Mu = wu * LUZ_VIGA ** 2 / 8
    r = _sel_viga(Mu, wL, LUZ_VIGA)
    Mu_volado = wu * dz.VOLADO_O ** 2 / 2 + 1.2 * 0.5 * ANCHO_TRIB_VIGA * dz.VOLADO_O
    r.update(wu=wu, Mu_volado=Mu_volado, ok_volado=Mu_volado <= r["phiMn"])
    return r


def columna():
    """Columna interior B2: área tributaria de entrepiso y techo; K = 1.0 (pórticos arriostrados)."""
    A_trib = LUZ_VIGUETA * (dz.EJES_D[1] - dz.EJES_D[0] + dz.EJES_D[2] - dz.EJES_D[1]) / 2
    Pu = A_trib * (1.2 * (D_LOSA + TABIQUERIA) + 1.6 * L_ESCENARIO) + A_trib * (1.2 * D_TECHO + 1.6 * LR_TECHO)
    Pu += 1.2 * 0.40 * H_COL_TECHO                                   # peso propio
    for s in CAT_HSS[5:]:          # mínimo HSS 8x8 para recibir vigas W14 con conexiones atornilladas
        Fcr, lam = fcr(1.0 * H_PISO * 1000, s.r_mm, FY_HSS)
        phiPn = 0.9 * Fcr * s.A_mm2 / 1000
        # momento por excentricidad de vigas (10 % de la carga a 0.15 m) y desbalance del volado
        Mu = 0.10 * Pu * 0.15 + 0.5 * viga_principal()["Mu_volado"] * 0.25
        phiMn = 0.9 * FY_HSS * s.Z * IN ** 3 / 1e6
        inter = Pu / phiPn + 8 / 9 * Mu / phiMn if Pu / phiPn >= 0.2 else Pu / (2 * phiPn) + Mu / phiMn
        if inter <= 0.85 and lam <= 200:
            return dict(seccion=s, Pu=Pu, phiPn=phiPn, Mu=Mu, interaccion=inter, esbeltez=lam, A_trib=A_trib)
    raise ValueError("sin columna")


def peso_sismico():
    losa = dz.LOSA2.area * (D_LOSA + 0.5 * L_TERRAZA)          # categoría B: 50 % de la carga viva
    techo = (ed.TECHO_BAR.area + ed.TECHO_ESC.area) * D_TECHO
    muros = 0.6 * 4 * 11.0 * 3.85 * 0.5                         # tabiques y mamparas tributarios (aprox.)
    return losa + techo + muros


def cortante_basal():
    P = peso_sismico()
    V = Z * U * C_SIS * S_SUELO / R0_SCBF * P
    return dict(P=P, V=V, coef=Z * U * C_SIS * S_SUELO / R0_SCBF)


def arriostre():
    """Diagonal en X de un paño de 5.50 × 3.85 m: 2 paños por dirección, +10 % por torsión accidental."""
    V = cortante_basal()["V"] * 0.5 * 1.10
    Lx, Hy = 5.50, H_PISO
    Ld = math.hypot(Lx, Hy)
    F = (V / 2) / (Lx / Ld)                     # una diagonal en tracción y otra en compresión
    for s in CAT_HSS[1:]:          # mínimo HSS 4x4x1/4 (esbeltez y relación ancho/espesor de SCBF)
        Fcr, lam = fcr(0.5 * Ld * 1000, s.r_mm, FY_HSS)     # cruce de la X arriostra a media longitud
        phiPn = 0.9 * Fcr * s.A_mm2 / 1000
        if phiPn >= F and lam <= 200 * 0.9:
            return dict(seccion=s, F=F, phiPn=phiPn, L_diag=Ld, esbeltez=lam, V_paño=V)
    raise ValueError("sin arriostre")


def zapata(tipo="interior"):
    A_trib = {"interior": 28.9, "borde": 18.5, "esquina": 11.0}[tipo]
    P = A_trib * (D_LOSA + TABIQUERIA + L_ESCENARIO) + A_trib * (D_TECHO + LR_TECHO) + 4.0
    A_req = P * 1.10 / Q_ADM
    lado = math.ceil(math.sqrt(A_req) * 10) / 10
    lado = max(lado, 1.20)
    return dict(P=P, A_req=A_req, lado=lado, h=0.50 if lado <= 1.6 else 0.60, Df=1.50)


VIGUETA = vigueta()
VIGUETA_ESC = vigueta(L_ESCENARIO)
VIGUETA_VOL = vigueta_volado()
VIGA = viga_principal()
COLUMNA = columna()
ARRIOSTRE = arriostre()
SISMO = cortante_basal()
ZAPATAS = {t: zapata(t) for t in ("interior", "borde", "esquina")}
VIGA_TECHO = CAT_W[1]          # W8x13: vigas inclinadas de techo (luz ≤ 3.4 m entre cumbrera y alero)
CORREA_TECHO = "C 150x50x15x2.5 mm @ 1.10 m"
VIGA_BORDE = CAT_W[2]          # W8x15: viga de borde de la losa en volado
PLACA_BASE = "PL 400 x 400 x 25 mm, 4 pernos de anclaje Ø 3/4\" (ASTM F1554 Gr. 36), L = 600 mm, grout 25 mm"


# --------------------------------------------------------------------------
# Metrado de acero
# --------------------------------------------------------------------------
def metrado():
    items = []
    n_col_techo = 8
    items.append(("Columnas " + COLUMNA["seccion"].nombre, n_col_techo * (H_COL_TECHO + 0.1) + (dz.NPT2 + 1.2),
                  COLUMNA["seccion"].kg_m))
    largo_viga = dz.EJES_D[-1] - dz.EJES_D[0] + dz.VOLADO_O
    items.append(("Vigas principales " + VIGA["seccion"].nombre + " (ejes 1-2-3, con volado oeste)", 3 * largo_viga,
                  VIGA["seccion"].kg_m))
    n_lineas = 3 + 3 + 1 + 1                                  # paños A-B y B-C + volado oeste + borde
    largo_vig = dz.EJES_S[-1] - dz.EJES_S[0] + dz.VOLADO_N
    largo_esc = 4 * (dz.EJES_S[2] - dz.EJES_S[1])            # 4 líneas bajo el escenario (paño B-C y volado oeste)
    items.append((f"Viguetas {VIGUETA['seccion'].nombre} @ {SEP_VIGUETAS:.2f} m (con volado norte)",
                  n_lineas * largo_vig - largo_esc, VIGUETA["seccion"].kg_m))
    items.append((f"Viguetas bajo el escenario {VIGUETA_ESC['seccion'].nombre}", largo_esc, VIGUETA_ESC["seccion"].kg_m))
    items.append(("Vigas de borde " + VIGA_BORDE.nombre + " (volados)", 14.0 + 12.5, VIGA_BORDE.kg_m))
    items.append(("Arriostres en X " + ARRIOSTRE["seccion"].nombre + " (4 paños)", 4 * 2 * ARRIOSTRE["L_diag"],
                  ARRIOSTRE["seccion"].kg_m))
    items.append(("Vigas de techo y cumbreras " + VIGA_TECHO.nombre, 3 * 2 * 3.6 + 3 * 2 * 3.4 + 12.5 + 7.6,
                  VIGA_TECHO.kg_m))
    items.append(("Correas " + CORREA_TECHO, 7 * 13.2 + 7 * 7.6, 6.2))
    items.append(("Escalera principal en U (zancas, peldaños y descansos)", 1, 950.0))
    items.append(("Escalera exterior de evacuación y servicio", 1, 1050.0))
    items.append(("Barandas de terraza (acero + vidrio laminado, estructura)", 34.0, 22.0))
    items.append(("Placas base, cartelas, conexiones y pernos (8 %)", None, None))
    filas = []
    tot = 0.0
    for nombre, largo, kgm in items:
        if largo is None:
            continue
        kg = largo * kgm
        tot += kg
        filas.append((nombre, largo, kgm, kg))
    conex = 0.08 * tot
    filas.append(("Placas base, cartelas, conexiones y pernos (8 %)", None, None, conex))
    return filas, tot + conex


METRADO, ACERO_TOTAL_KG = metrado()


def resumen():
    return [
        ("Losa colaborante", f"Steel deck AD-600 cal. 20 + concreto f'c 210 kg/cm², e = 12 cm; luz {SEP_VIGUETAS:.2f} m"),
        ("Viguetas", f"{VIGUETA['seccion'].nombre} @ {SEP_VIGUETAS:.2f} m, L = {LUZ_VIGUETA:.2f} m "
                     f"(uso {VIGUETA['ratio'] * 100:.0f} %, flecha {VIGUETA['flecha_mm']:.0f} mm ≤ {VIGUETA['lim_mm']:.0f}); "
                     f"bajo el escenario {VIGUETA_ESC['seccion'].nombre}"),
        ("Vigas principales", f"{VIGA['seccion'].nombre}, L = {LUZ_VIGA:.2f} m + volado {dz.VOLADO_O:.2f} m "
                              f"(uso {VIGA['ratio'] * 100:.0f} %)"),
        ("Columnas", f"{COLUMNA['seccion'].nombre}, Pu = {COLUMNA['Pu']:.0f} kN, φPn = {COLUMNA['phiPn']:.0f} kN, "
                     f"interacción {COLUMNA['interaccion']:.2f}"),
        ("Arriostres", f"{ARRIOSTRE['seccion'].nombre} en X, F = {ARRIOSTRE['F']:.0f} kN, φPn = {ARRIOSTRE['phiPn']:.0f} kN"),
        ("Sismo", f"Z {Z} · U {U} · C {C_SIS} · S {S_SUELO} / R {R0_SCBF:.0f} = {SISMO['coef']:.3f}; "
                  f"P = {SISMO['P']:.0f} kN; V = {SISMO['V']:.0f} kN"),
        ("Zapatas", f"interior {ZAPATAS['interior']['lado']:.1f} × {ZAPATAS['interior']['lado']:.1f} m, "
                    f"borde {ZAPATAS['borde']['lado']:.1f} m, esquina {ZAPATAS['esquina']['lado']:.1f} m; "
                    f"q adm supuesta {Q_ADM / 100:.1f} kg/cm²"),
        ("Acero estructural", f"{ACERO_TOTAL_KG:,.0f} kg ({ACERO_TOTAL_KG / dz.LOSA2.area:.0f} kg por m² de entrepiso)"),
    ]


if __name__ == "__main__":
    for k, v in resumen():
        print(f"{k:20s} {v}")
    print()
    for f in METRADO:
        print(f)
