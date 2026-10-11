"""
Predimensionamiento de la estructura metálica ligera de las coberturas.

Sistema: voladizo asimétrico ("T" desbalanceada) con una sola línea de
columnas detrás de las plazas, a 1.00 m del fondo, una columna cada 3 plazas
(7.50 - 7.60 m). Viga en voladizo reticulada de peralte variable, correas
continuas entre vigas y cobertura TR-4.

Normas de referencia (RNE Perú): E.020 Cargas, E.030 Diseño Sismorresistente,
E.050 Suelos y Cimentaciones, E.060 Concreto Armado, E.090 Estructuras
Metálicas (método LRFD).

IMPORTANTE: es un PREDIMENSIONAMIENTO para anteproyecto y presupuesto. El
expediente de obra debe ser revisado y firmado por un ingeniero civil
colegiado (CIP), con estudio de mecánica de suelos (EMS).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import geometria as g

E = 200_000.0          # MPa
FY_TUBO = 250.0        # MPa (ASTM A500 Gr. A / A36 equivalente, conservador)
FY_CORREA = 250.0      # MPa (ASTM A653 / A1011 galvanizado)
ACERO_KG_M3 = 7850.0

# --------------------------------------------------------------------------
# Cargas (kPa)
# --------------------------------------------------------------------------
CARGAS = {
    "cobertura TR-4 0.40 mm + accesorios": 0.05,
    "correas (prom.)": 0.045,
    "vigas, arriostres y canaletas (prom.)": 0.035,
    "instalaciones (luminarias, tuberías)": 0.02,
}
D_KPA = sum(CARGAS.values())          # carga muerta
LR_KPA = 0.30                          # E.020: techos con coberturas livianas
V_VIENTO = 75.0                        # km/h, mínimo E.020
C_VIENTO = 1.5                         # coeficiente neto conservador (cubierta abierta)
W_KPA = 0.005 * C_VIENTO * V_VIENTO**2 * 9.81 / 1000   # kgf/m2 -> kPa
Z_SISMO, U_SISMO, C_SISMO, S_SISMO, R_SISMO = 0.35, 1.0, 2.5, 1.15, 2.0


# --------------------------------------------------------------------------
# Secciones
# --------------------------------------------------------------------------
@dataclass
class Tubo:
    nombre: str
    h: float  # mm (en el plano de flexión)
    b: float
    t: float

    @property
    def area(self):
        return self.h * self.b - (self.h - 2 * self.t) * (self.b - 2 * self.t)

    @property
    def peso(self):
        return self.area * 1e-6 * ACERO_KG_M3

    @property
    def ix(self):
        return (self.b * self.h**3 - (self.b - 2 * self.t) * (self.h - 2 * self.t) ** 3) / 12

    @property
    def iy(self):
        return (self.h * self.b**3 - (self.h - 2 * self.t) * (self.b - 2 * self.t) ** 3) / 12

    @property
    def zx(self):
        return (self.b * self.h**2 - (self.b - 2 * self.t) * (self.h - 2 * self.t) ** 2) / 4

    @property
    def zy(self):
        return (self.h * self.b**2 - (self.h - 2 * self.t) * (self.b - 2 * self.t) ** 2) / 4

    @property
    def rx(self):
        return math.sqrt(self.ix / self.area)

    @property
    def ry(self):
        return math.sqrt(self.iy / self.area)

    def compacta(self, fy):
        lp = 1.12 * math.sqrt(E / fy)
        return (self.b - 3 * self.t) / self.t <= lp and (self.h - 3 * self.t) / self.t <= 2.42 * math.sqrt(E / fy)


@dataclass
class CanalC:
    """Perfil C con pestañas (correa) plegado en frío."""
    nombre: str
    h: float
    b: float
    c: float
    t: float

    @property
    def area(self):
        return (self.h + 2 * self.b + 2 * self.c) * self.t

    @property
    def peso(self):
        return self.area * 1e-6 * ACERO_KG_M3

    @property
    def ix(self):
        h, b, c, t = self.h, self.b, self.c, self.t
        alma = t * h**3 / 12
        alas = 2 * (b * t**3 / 12 + b * t * (h / 2 - t / 2) ** 2)
        pest = 2 * (t * c**3 / 12 + c * t * (h / 2 - c / 2) ** 2)
        return alma + alas + pest

    @property
    def sx(self):
        return self.ix / (self.h / 2)


CATALOGO_COLUMNAS = [
    Tubo("Tubo 200x200x6 mm", 200, 200, 6),
    Tubo("Tubo 250x150x6 mm", 250, 150, 6),
    Tubo("Tubo 300x150x6 mm", 300, 150, 6),
    Tubo("Tubo 300x200x6 mm", 300, 200, 6),
    Tubo("Tubo 300x200x8 mm", 300, 200, 8),
]
CATALOGO_CORREAS = [
    CanalC("C 150x50x15x2.0 mm", 150, 50, 15, 2.0),
    CanalC("C 175x60x20x2.0 mm", 175, 60, 20, 2.0),
    CanalC("C 200x50x15x2.0 mm", 200, 50, 15, 2.0),
    CanalC("C 200x60x20x2.5 mm", 200, 60, 20, 2.5),
    CanalC("C 250x75x20x2.5 mm", 250, 75, 20, 2.5),
]
CORDON = Tubo("Tubo 75x75x3 mm (3\"x3\")", 75, 75, 3)
DIAGONAL = Tubo("Tubo 50x50x3 mm (2\"x2\")", 50, 50, 3)
VIGA_BORDE = Tubo("Tubo 100x50x2.5 mm (4\"x2\")", 100, 50, 2.5)

# --------------------------------------------------------------------------
# Geometría típica de la cobertura (tomada del layout)
# --------------------------------------------------------------------------
COB = g.COB_A
ANCHO_COB = abs(COB.d_frente - COB.d_atras)                   # 5.70 m
BRAZO_FRONTAL = abs(COB.d_frente - COB.d_col)                 # 4.55 m
BRAZO_POSTERIOR = abs(COB.d_col - COB.d_atras)                # 1.15 m
N_CORREAS = 6
SEP_CORREAS = (ANCHO_COB - 0.20) / (N_CORREAS - 1)


def _luces():
    luces = []
    for cob in g.COBERTURAS:
        ss = [s for (_, s, _) in cob.columnas]
        luces += [b - a for a, b in zip(ss, ss[1:])]
    return luces


LUZ_MAX_CORREA = max(_luces())
VOLADO_LAT_MAX = max(max(abs(cob.columnas[0][1] - cob.s0), abs(cob.s1 - cob.columnas[-1][1]))
                     for cob in g.COBERTURAS)
ANCHO_TRIB_MAX = max(
    max(((b - a) / 2 + (c - b) / 2) for a, b, c in zip(*(lambda s: (s, s[1:], s[2:]))([s for (_, s, _) in cob.columnas])))
    if len(cob.columnas) > 2 else 0
    for cob in g.COBERTURAS)
ANCHO_TRIB_MAX = max(ANCHO_TRIB_MAX, max(
    (abs(cob.columnas[1][1] - cob.columnas[0][1]) / 2 + abs(cob.columnas[0][1] - cob.s0))
    for cob in g.COBERTURAS))

# Niveles (m, respecto al NPT +/-0.00)
NIV_FONDO_COB = 3.40        # borde posterior (canaleta)
PENDIENTE = 0.10            # 10 % sube hacia el pasillo
NIV_INF_VIGA_COL = 2.80     # gálibo mínimo bajo viga (en la columna)
NIV_INF_VIGA_PUNTA = 3.62
NIV_SUP_DADO = 0.10
NIV_INF_VIGA_FONDO = 3.10
PERALTE_CORREA = 0.175
DF_ZAPATA = 1.20            # profundidad de desplante
H_ZAPATA = 0.60
ZAP_B = 1.80                # dimensión en dirección del voladizo
ZAP_L = 1.40                # dimensión a lo largo de la fila
DADO_B = 0.65               # pedestal, en dirección del voladizo
DADO_L = 0.50               # pedestal, a lo largo de la fila
Q_ADM_SUPUESTA = 100.0      # kPa (1.0 kg/cm2) -> confirmar con EMS


def niv_sup_cubierta(d_desde_atras):
    return NIV_FONDO_COB + PENDIENTE * d_desde_atras


def peralte_viga(x_desde_atras):
    """Peralte exterior (m) de la viga reticulada a la distancia x del borde posterior."""
    xc = BRAZO_POSTERIOR
    sup = niv_sup_cubierta(x_desde_atras) - PERALTE_CORREA  # cara superior del cordón sup. (bajo la correa)
    if x_desde_atras <= xc:
        inf = NIV_INF_VIGA_COL + (NIV_INF_VIGA_FONDO - NIV_INF_VIGA_COL) * (xc - x_desde_atras) / xc
    else:
        inf = NIV_INF_VIGA_COL + (NIV_INF_VIGA_PUNTA - NIV_INF_VIGA_COL) * (x_desde_atras - xc) / BRAZO_FRONTAL
    return sup - inf, sup, inf


# --------------------------------------------------------------------------
# Verificaciones
# --------------------------------------------------------------------------
def verificar_correa():
    L = LUZ_MAX_CORREA * 1000
    s = SEP_CORREAS
    res = []
    for sec in CATALOGO_CORREAS:
        wd = (0.05 + 0.02) * s + sec.peso * 9.81 / 1000
        wl = LR_KPA * s
        ww = W_KPA * s
        wu_g = 1.2 * wd + 1.6 * wl
        wu_up = 1.3 * ww - 0.9 * wd
        mu = max(wu_g, wu_up) * L**2 / 8 / 1e6                # kN.m
        se = 0.85 * sec.sx                                    # sección efectiva aprox.
        phimn = 0.90 * FY_CORREA * se / 1e6
        # con succión: ala inferior comprimida, templadores a L/3 -> factor 0.75
        phimn_up = 0.75 * phimn
        flecha = 5 * wl * L**4 / (384 * E * sec.ix)
        ok = (wu_g * L**2 / 8 / 1e6 <= 0.90 * phimn and wu_up * L**2 / 8 / 1e6 <= 0.90 * phimn_up
              and flecha <= L / 180)
        res.append(dict(seccion=sec, mu=mu, phimn=phimn, flecha=flecha, flecha_lim=L / 180, ok=ok,
                        ratio=max(wu_g * L**2 / 8 / 1e6 / phimn, wu_up * L**2 / 8 / 1e6 / phimn_up)))
        if ok:
            return res[-1], res
    return res[-1], res


CORREA_SEL, _ = verificar_correa()
CORREA = CORREA_SEL["seccion"]


def verificar_viga():
    trib = ANCHO_TRIB_MAX
    wd = D_KPA * trib
    wl = LR_KPA * trib
    ww = W_KPA * trib
    a, b = BRAZO_FRONTAL, BRAZO_POSTERIOR
    wu = 1.2 * wd + 1.6 * wl
    mu_raiz = wu * a**2 / 2
    vu = wu * a
    mu_up = (1.3 * ww - 0.9 * wd) * a**2 / 2
    h_ext, _, _ = peralte_viga(b)
    h_cc = h_ext - CORDON.h / 1000
    f_cordon = mu_raiz / h_cc
    f_cordon_up = mu_up / h_cc
    # tracción cordón superior
    phit = 0.9 * FY_TUBO * CORDON.area / 1000
    # compresión cordón inferior (panel 0.60 m, arriostrado lateralmente cada 1.14 m con tornapuntas)
    kl = 1.14 * 1000
    lam = kl / CORDON.rx
    lc2 = (lam**2) * FY_TUBO / (math.pi**2 * E)
    fcr = (0.658**lc2) * FY_TUBO if lc2 <= 2.25 else 0.877 * FY_TUBO / lc2
    phic = 0.9 * fcr * CORDON.area / 1000
    # diagonal
    f_diag = vu / math.sin(math.radians(45))
    lam_d = 0.6 * 1000 * 1.0 / DIAGONAL.rx
    lc2d = (lam_d**2) * FY_TUBO / (math.pi**2 * E)
    phic_d = 0.9 * (0.658**lc2d) * FY_TUBO * DIAGONAL.area / 1000
    # flecha del voladizo (integración numérica con inercia variable de cordones)
    n = 200
    dx = a / n
    wl_n = wl  # kN/m
    rot = 0.0
    flecha = 0.0
    # integración desde la raíz (empotrada en la columna) hacia la punta
    xs = [i * dx for i in range(n + 1)]
    momentos = [wl_n * (a - x) ** 2 / 2 for x in xs]
    inercias = []
    for x in xs:
        h_e, _, _ = peralte_viga(b + x)
        hc = max(h_e - CORDON.h / 1000, 0.08)
        inercias.append(2 * CORDON.area * (hc * 1000 / 2) ** 2 + 2 * CORDON.ix)
    curv = [m * 1e6 / (E * i) for m, i in zip(momentos, inercias)]   # 1/mm
    for i in range(n):
        rot_new = rot + 0.5 * (curv[i] + curv[i + 1]) * dx * 1000
        flecha += 0.5 * (rot + rot_new) * dx * 1000
        rot = rot_new
    return dict(trib=trib, wu=wu, mu_raiz=mu_raiz, vu=vu, mu_succion=mu_up, h_ext=h_ext, h_cc=h_cc,
                f_cordon=f_cordon, f_cordon_succion=f_cordon_up, phit=phit, phic=phic, f_diag=f_diag,
                phic_d=phic_d, flecha_viga=flecha,
                ok=f_cordon <= phit and f_cordon <= phic and f_diag <= phic_d)


VIGA = verificar_viga()


def verificar_columna():
    trib = ANCHO_TRIB_MAX
    a, b = BRAZO_FRONTAL, BRAZO_POSTERIOR
    wd, wl, ww = D_KPA * trib, LR_KPA * trib, W_KPA * trib
    h_col = NIV_INF_VIGA_COL + peralte_viga(b)[0] / 2 - NIV_SUP_DADO + 0.10
    # momento desbalanceado en la base (Lr solo en el brazo frontal = caso crítico)
    mu_g = (1.2 * wd + 1.6 * wl) * a**2 / 2 - 0.9 * wd * b**2 / 2 * 0 - 1.2 * wd * b**2 / 2
    pu = (1.2 * wd + 1.6 * wl) * (a + b) + 1.2 * 0.6
    # sismo (dirección longitudinal y transversal) - péndulo invertido
    peso_sis = wd * (a + b) + 1.5
    v_sis = Z_SISMO * U_SISMO * C_SISMO * S_SISMO / R_SISMO * peso_sis
    m_sis = v_sis * h_col
    # viento lateral sobre el canto (0.40 m) a lo largo de la cobertura
    m_vie_lat = 1.3 * W_KPA * 0.40 * trib * h_col
    ms_d = wd * a**2 / 2 - wd * b**2 / 2
    ms_l = wl * a**2 / 2
    res = []
    for sec in CATALOGO_COLUMNAS:
        phimn = 0.9 * FY_TUBO * sec.zx / 1e6
        phimny = 0.9 * FY_TUBO * sec.zy / 1e6
        k_l = 2.1 * h_col * 1000
        lam = k_l / min(sec.rx, sec.ry)
        lc2 = (lam**2) * FY_TUBO / (math.pi**2 * E)
        fcr = (0.658**lc2) * FY_TUBO if lc2 <= 2.25 else 0.877 * FY_TUBO / lc2
        phipn = 0.9 * fcr * sec.area / 1000
        r_axial = pu / phipn
        inter = r_axial / 2 + mu_g / phimn if r_axial < 0.2 else r_axial + 8 / 9 * mu_g / phimn
        inter_y = pu / phipn / 2 + max(m_sis, m_vie_lat) / phimny
        # giro en la cabeza de la columna por Lr -> descenso de la punta del voladizo
        theta_l = ms_l * 1e6 * h_col * 1000 / (E * sec.ix)
        flecha_total = theta_l * a * 1000 + VIGA["flecha_viga"]
        lim = 2 * a * 1000 / 180
        ok = inter <= 0.9 and inter_y <= 0.9 and flecha_total <= 0.9 * lim and sec.compacta(FY_TUBO)
        r = dict(seccion=sec, h_col=h_col, mu=mu_g, pu=pu, phimn=phimn, phipn=phipn, inter=inter,
                 inter_y=inter_y, m_sis=m_sis, v_sis=v_sis, flecha_total=flecha_total, flecha_lim=lim,
                 ms_d=ms_d, ms_l=ms_l, ok=ok)
        res.append(r)
        if ok:
            return r, res
    return res[-1], res


COLUMNA_SEL, _COLS = verificar_columna()
COLUMNA = COLUMNA_SEL["seccion"]


def verificar_placa_base():
    mu = COLUMNA_SEL["mu"]
    pu = COLUMNA_SEL["pu"]
    sep_pernos = 0.30 if COLUMNA.h <= 250 else 0.40       # en el plano del momento
    sep_pernos_l = 0.25                                    # transversal
    placa = (sep_pernos + 0.10) * 1000
    placa_l = (sep_pernos_l + 0.10) * 1000
    brazo = sep_pernos + 0.05 - 0.04   # entre pernos a tracción y resultante de compresión
    t_total = mu / brazo - pu / 2
    t_perno = t_total / 2
    a_perno = 507.0   # ø 1"
    phirn = 0.75 * 0.75 * 400 * a_perno / 1000
    return dict(placa=placa, placa_l=placa_l, sep=sep_pernos, sep_l=sep_pernos_l, t_perno=t_perno, phirn=phirn, ok=t_perno <= phirn,
                perno='ø 1" (25 mm) ASTM F1554 Gr.36, L = 0.75 m con gancho')


PLACA = verificar_placa_base()


def verificar_zapata():
    trib = ANCHO_TRIB_MAX
    a, b = BRAZO_FRONTAL, BRAZO_POSTERIOR
    wd, wl = D_KPA * trib, LR_KPA * trib
    peso_col = COLUMNA.peso * COLUMNA_SEL["h_col"] * 9.81 / 1000
    n_est = wd * (a + b) + wl * a + peso_col + 1.2
    m_est = COLUMNA_SEL["ms_d"] + COLUMNA_SEL["ms_l"]
    vol_zap = ZAP_B * ZAP_L * H_ZAPATA
    h_dado = DF_ZAPATA - H_ZAPATA + NIV_SUP_DADO
    vol_dado = DADO_B * DADO_L * h_dado
    relleno = (ZAP_B * ZAP_L - DADO_B * DADO_L) * (DF_ZAPATA - H_ZAPATA) * 17.0
    n_tot = n_est + 24 * (vol_zap + vol_dado) + relleno
    e = m_est / n_tot
    if e <= ZAP_B / 6:
        qmax = n_tot / (ZAP_B * ZAP_L) * (1 + 6 * e / ZAP_B)
    else:
        qmax = 2 * n_tot / (3 * ZAP_L * (ZAP_B / 2 - e))
    fs_volteo = n_tot * ZAP_B / 2 / m_est
    return dict(n_est=n_est, m_est=m_est, n_tot=n_tot, e=e, qmax=qmax, fs_volteo=fs_volteo,
                vol_zap=vol_zap, vol_dado=vol_dado, h_dado=h_dado,
                ok=qmax <= Q_ADM_SUPUESTA and fs_volteo >= 1.5)


ZAPATA = verificar_zapata()


# --------------------------------------------------------------------------
# Metrado de acero
# --------------------------------------------------------------------------
def longitud_viga_reticulada():
    """Longitud de cordones + diagonales de una viga (m)."""
    paneles = 10
    dx = ANCHO_COB / paneles
    cordones = 2 * ANCHO_COB * 1.005
    diag = 0.0
    for i in range(paneles + 1):
        h, _, _ = peralte_viga(i * dx)
        h = max(h - CORDON.h / 1000, 0.05)
        diag += h                               # montante
        if i < paneles:
            diag += math.hypot(dx, h)           # diagonal
    return cordones, diag


def metrado():
    n_col = len(g.COLUMNAS)
    h_col = COLUMNA_SEL["h_col"]
    filas = []
    kg_col = n_col * h_col * COLUMNA.peso
    filas.append(("Columnas", COLUMNA.nombre, n_col, n_col * h_col, COLUMNA.peso, kg_col))
    placa_kg = (PLACA["placa"] / 1000) * (PLACA["placa_l"] / 1000) * 0.025 * ACERO_KG_M3 + 4 * 0.20 * 0.15 * 0.010 * ACERO_KG_M3
    filas.append(("Placas base + cartelas", f"PL {PLACA['placa']:.0f}x{PLACA['placa_l']:.0f}x25 mm + 4 PL 10 mm",
                  n_col, n_col, placa_kg, n_col * placa_kg))
    cord, diag = longitud_viga_reticulada()
    filas.append(("Vigas voladizo - cordones", CORDON.nombre, n_col, n_col * cord, CORDON.peso, n_col * cord * CORDON.peso))
    filas.append(("Vigas voladizo - diagonales/montantes", DIAGONAL.nombre, n_col, n_col * diag, DIAGONAL.peso,
                  n_col * diag * DIAGONAL.peso))
    long_cob = sum(cob.s1 - cob.s0 for cob in g.COBERTURAS)
    l_correas = N_CORREAS * long_cob * 1.03
    filas.append(("Correas", CORREA.nombre + " galv.", N_CORREAS * len(g.COBERTURAS), l_correas, CORREA.peso,
                  l_correas * CORREA.peso))
    # templadores ø3/8" a tercios + arriostres en X ø1/2" en paños extremos
    n_paños = sum(len(cob.columnas) - 1 for cob in g.COBERTURAS)
    l_templ = sum(2 * ANCHO_COB * (len(cob.columnas) - 1) for cob in g.COBERTURAS)
    filas.append(("Templadores", 'Barra lisa ø 3/8"', n_paños * 2, l_templ, 0.56, l_templ * 0.56))
    l_arr = sum(2 * 2 * math.hypot(ANCHO_COB, 7.5) for _ in g.COBERTURAS)
    filas.append(("Arriostres de techo en X", 'Barra lisa ø 1/2" + tensor', len(g.COBERTURAS) * 2, l_arr, 0.99, l_arr * 0.99))
    sub = sum(f[-1] for f in filas)
    filas.append(("Planchas de conexión, clips, pernos (8 %)", "-", "-", "-", "-", 0.08 * sub))
    total = sum(f[-1] for f in filas)
    return filas, total


METRADO, ACERO_TOTAL_KG = metrado()
AREA_TECHADA = sum(c.poly.area for c in g.COBERTURAS)


def resumen_texto():
    v, c, z, p = VIGA, COLUMNA_SEL, ZAPATA, PLACA
    lineas = [
        f"Cargas: D = {D_KPA:.2f} kPa, Lr = {LR_KPA:.2f} kPa, W = {W_KPA:.2f} kPa (V = {V_VIENTO:.0f} km/h, C = {C_VIENTO})",
        f"Luz máx. de correas = {LUZ_MAX_CORREA:.2f} m; voladizo lateral máx. = {VOLADO_LAT_MAX:.2f} m; ancho tributario máx. = {ANCHO_TRIB_MAX:.2f} m",
        f"Correa: {CORREA.nombre} -> ratio {CORREA_SEL['ratio']:.2f}, flecha {CORREA_SEL['flecha']:.0f} mm <= {CORREA_SEL['flecha_lim']:.0f} mm",
        f"Viga voladizo: Mu = {v['mu_raiz']:.1f} kN.m, cordón {v['f_cordon']:.0f} kN (phiTn {v['phit']:.0f} / phiPn {v['phic']:.0f} kN), diagonal {v['f_diag']:.0f} kN (phiPn {v['phic_d']:.0f})",
        f"Columna: {COLUMNA.nombre}, h = {c['h_col']:.2f} m, Mu = {c['mu']:.1f} kN.m, interacción {c['inter']:.2f}, flecha punta (Lr) {c['flecha_total']:.0f} mm <= {c['flecha_lim']:.0f} mm",
        f"Placa base {p['placa']:.0f}x{p['placa_l']:.0f} mm, tracción por perno {p['t_perno']:.0f} kN <= {p['phirn']:.0f} kN",
        f"Zapata {ZAP_L:.2f} x {ZAP_B:.2f} x {H_ZAPATA:.2f} m: e = {z['e']:.2f} m, qmax = {z['qmax']:.0f} kPa, FS volteo = {z['fs_volteo']:.2f}",
        f"Acero estructural total = {ACERO_TOTAL_KG:,.0f} kg  ->  {ACERO_TOTAL_KG / AREA_TECHADA:.1f} kg/m2 de techo ({AREA_TECHADA:.0f} m2)",
    ]
    return lineas


if __name__ == "__main__":
    for l in resumen_texto():
        print(l)
    print("Viga OK:", VIGA["ok"], " Columna OK:", COLUMNA_SEL["ok"], " Placa OK:", PLACA["ok"], " Zapata OK:", ZAPATA["ok"])
    for r in _COLS:
        print("  ", r["seccion"].nombre, "inter", round(r["inter"], 2), "flecha", round(r["flecha_total"]), "/",
              round(r["flecha_lim"]), r["ok"])
    for f in METRADO:
        print(f)
