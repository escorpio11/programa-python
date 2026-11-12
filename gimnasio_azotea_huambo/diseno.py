# -*- coding: utf-8 -*-
"""
AZOTEA GYM - Huambo (Amazonas).  Geometria unica del proyecto.

Sistema de coordenadas (metros):
    x : a lo largo de la azotea, desde la cara exterior del muro del lado
        MERCADO (eje 7) hacia el lado CALLE (eje 1).
    y : desde la cara exterior del muro del fondo (lado A, eje D) hacia el
        muro del lado B (eje G).
    z : altura sobre el piso terminado de la azotea.

Fuentes
    [P1] Plano de distribucion de maquinas "AZOTEA GYM" (ago-2026): base
         general 14.62 x 6.65 m, vigas, ubicacion de maquinas.
    [P2] A-01 modif. "SS.HH. y zona de servicio - MEDIDAS DE OBRA" (nov-2026):
         banos construidos, tanque elevado, lavadero y tragaluces.
    [P3] Techo metalico Casa de Huambo (jul-2024): cerchas, alturas,
         calamina translucida sobre tragaluces.
    [P4] Catalogo 2026 Fitness Extreme: dimensiones y precios.

Ajuste de base: el bano construido mide 3.70 m interiores [P2] frente a los
3.35 m del plano base [P1].  Se respeta la medida de obra y todo lo que queda
a la derecha del bano se desplaza DX = 0.35 m; el resto se mantiene como en
[P1].  El largo del modelo resulta 14.97 m (ver verificacion de medidas).
"""
import json
import math
import os

AQUI = os.path.dirname(os.path.abspath(__file__))

# --------------------------------------------------------------------------- base
DX = 0.35                      # corrimiento por medida de obra del bano
L_BASE, W = 14.62, 6.65        # plano base [P1]
L = round(L_BASE + DX, 2)      # 14.97
T = 0.15                       # espesor de muros/parapetos
H_PARAPETO = 1.00
H_BANO = 2.40
Y_BLOQUE = 0.40                # retiro del bloque de banos respecto del muro del fondo
NOMBRE = "AZOTEA GYM"
LUGAR = "Huambo, Rodríguez de Mendoza - Amazonas"


def bx(x_base):
    """x del plano base [P1] -> x del modelo (corre DX lo que esta a la derecha del bano)."""
    return round(x_base + (DX if x_base >= 3.49 else 0.0), 3)


# Ejes transversales (cara/centro de viga en el modelo) y alturas de techo [P3]
EJES = {
    "7": 0.15, "6": 2.67, "5": bx(4.68), "4": bx(7.22),
    "3": bx(9.87), "2": bx(12.40), "1": bx(13.48),
}
EJES_Y = {"D": 0.075, "E": Y_BLOQUE + 0.075, "F": 1.30, "G": W - 0.075}

# Vigas del techo del ultimo piso (proyeccion, segun [P1]) : bandas (x0, x1) y (y0, y1)
VIGAS_X = [(0.15, 0.30), (2.52, 2.82), (bx(4.55), bx(4.84)), (bx(7.08), bx(7.37)),
           (bx(9.72), bx(10.02)), (bx(12.27), bx(12.55)), (bx(13.39), bx(13.68))]
VIGAS_Y = [(2.06, 2.34, 0.15, bx(7.37)), (3.24, 3.54, 0.15, bx(10.02))]   # (y0, y1, x0, x1)
# Elementos del nivel inferior dibujados en [P1] (muro/viga eje F y eje 6, columnas eje 1)
INFERIOR = [
    {"tipo": "muro", "rect": (bx(7.07), 1.23, bx(12.56), 1.37), "nota": "Eje F (nivel inferior)"},
    {"tipo": "muro", "rect": (2.60, 3.42, 2.75, 6.50), "nota": "Eje 6 (nivel inferior)"},
    {"tipo": "columna", "rect": (bx(13.44), 1.23, bx(13.64), 1.73), "nota": "C 0.20x0.50 eje 1-F"},
    {"tipo": "columna", "rect": (bx(13.44), 6.17, bx(13.64), 6.67), "nota": "C 0.20x0.50 eje 1-G"},
]

# --------------------------------------------------------------------------- existente
X_BANO_D = 0.15 + 3.70          # cara interior del muro derecho del bano (L4) = 3.85
X_TRAG_E0, X_TRAG_E1 = X_BANO_D + T, bx(4.84)          # tragaluz E : 4.00 .. 5.19
X_ESC0, X_ESC1 = X_TRAG_E1, bx(7.155)                  # caja de escalera : 5.19 .. 7.505
Y_ESC1 = 2.07                                          # cara interior del muro sur de escalera
X_VANO0, X_VANO1 = bx(6.185), X_ESC1                   # llegada de la escalera : 6.535 .. 7.505
Y_HALL0 = Y_ESC1 + T                                   # 2.22 : cara sur del muro de escalera

# Muros existentes: (x0, y0, x1, y1, altura, clave)
MUROS = [
    # perimetro (parapeto h = 1.00)
    (X_TRAG_E0, 0.0, L, T, H_PARAPETO, "parapeto"),                 # fondo (lado A)
    (L - T, 0.0, L, W, H_PARAPETO, "parapeto"),                     # lado calle
    (0.0, W - T, L, W, H_PARAPETO, "parapeto"),                     # lado B
    (0.0, 2.05, T, W, H_PARAPETO, "parapeto"),                      # lado mercado (bajo los banos)
    # bloque de banos [P2] (altura completa)
    (0.0, Y_BLOQUE, X_TRAG_E0, Y_BLOQUE + T, H_BANO, "bano"),       # muro fondo banos
    (0.0, Y_BLOQUE, T, 2.05, H_BANO, "bano"),                       # muro lado mercado
    (X_BANO_D, 0.0, X_TRAG_E0, Y_HALL0, H_BANO, "bano"),            # muro derecho (L4)
    (2.40, Y_BLOQUE + T, 2.51, 2.05, H_BANO, "bano"),               # tabique entre banos (0.11)
    (0.15, 1.70, 1.79, 1.81, H_BANO, "bano"),                       # frente SS.HH. 1
    (3.15, 1.93, X_BANO_D, 2.05, H_BANO, "bano"),                   # frente SS.HH. 2
    # caja de escalera y tragaluz E
    (X_BANO_D, Y_ESC1, X_VANO0, Y_HALL0, H_PARAPETO, "escalera"),   # muro sur (tragaluz + escalera)
    (X_ESC1, 0.0, X_ESC1 + T, 2.05, H_PARAPETO, "escalera"),        # muro este de la escalera
    # tragaluz SO (bajo la plataforma del tanque)
    (0.0, 1.81, 1.08, 1.96, H_PARAPETO, "tragaluz"),
    (0.0, 3.05, 1.08, 3.20, H_PARAPETO, "tragaluz"),
    (0.93, 1.81, 1.08, 3.20, H_PARAPETO, "tragaluz"),
]
PUERTAS = [
    {"id": "P-1", "x0": 1.79, "x1": 2.41, "y": 1.755, "bisagra": "x1", "abre": "N", "ancho": 0.62},
    {"id": "P-2", "x0": 2.51, "x1": 3.15, "y": 1.99, "bisagra": "x0", "abre": "N", "ancho": 0.64},
]
BANOS = [
    {"id": "SS.HH. 1 + DUCHA", "rect": (0.15, 0.55, 2.40, 1.70), "area": 2.83,
     "ducha": (0.15, 0.55, 0.96, 1.70), "inodoro": (1.33, 0.90), "lavatorio": (2.05, 0.75)},
    {"id": "SS.HH. 2", "rect": (2.51, 0.55, 3.85, 1.93), "area": 1.86,
     "ducha": (3.20, 0.55, 3.85, 1.23), "inodoro": (2.82, 0.90), "lavatorio": (3.62, 1.55)},
]
TRAGALUCES = [
    {"id": "TRAGALUZ E", "rect": (X_TRAG_E0, T, X_TRAG_E1, Y_ESC1),
     "nota": "Existente. Se cierra con baranda-celosía y policarbonato hasta el techo; no se cubre."},
    {"id": "TRAGALUZ SO", "rect": (0.15, 1.96, 0.93, 3.05),
     "nota": "Existente, bajo la plataforma del tanque TQ-1. Malla anticaída y celosía perimetral."},
]
TANQUE = {"centro": (0.54, 2.505), "diam": 1.10, "base": 1.22, "alto": 1.40,
          "plataforma": (0.0, 1.81, 1.08, 3.20), "capacidad_l": 1100}
LAVADERO = {"rect": (1.08, 1.87, 1.63, 3.41), "alto": 0.90}
ESCALERA = {"rect": (X_ESC0, T, X_ESC1, Y_ESC1), "vano": (X_VANO0, X_VANO1),
            "espina": (bx(5.80), 1.10, bx(6.17), Y_ESC1)}

# Columnas que reciben las cerchas [P3]: (x0, y0, x1, y1, altura)
H_TECHO = {"7": 2.80, "5": 2.65, "3": 2.50, "1": 2.40}
X_CERCHA = {"7": 0.15, "5": bx(4.70), "3": bx(9.89), "1": bx(13.50)}
COLUMNAS = [
    (0.0, Y_BLOQUE, 0.30, Y_BLOQUE + 0.30, 2.80), (0.0, W - 0.30, 0.30, W, 2.80),
    (X_CERCHA["5"] - 0.15, 0.0, X_CERCHA["5"] + 0.15, 0.30, 2.65),
    (X_CERCHA["5"] - 0.15, W - 0.30, X_CERCHA["5"] + 0.15, W, 2.65),
    (X_CERCHA["3"] - 0.15, 0.0, X_CERCHA["3"] + 0.15, 0.30, 2.50),
    (X_CERCHA["3"] - 0.15, W - 0.30, X_CERCHA["3"] + 0.15, W, 2.50),
    (X_CERCHA["1"] - 0.15, 0.0, X_CERCHA["1"] + 0.15, 0.30, 2.40),
    (X_CERCHA["1"] - 0.10, W - 0.50, X_CERCHA["1"] + 0.10, W, 2.40),
]
CERCHAS_SEC_Y = [0.075, 1.67, 3.34, 5.01, W - 0.075]      # cerchas secundarias [P3]
PERALTE_CERCHA = 0.40
# Calamina translucida prevista en [P3] (x0, y0, x1, y1)
TRANSLUCIDO = [(X_BANO_D, 0.0, bx(7.38), 1.67), (0.0, 1.67, 1.63, 3.34)]


def altura_techo(x):
    """Altura libre bajo cercha (m) interpolada entre ejes 7-5-3-1 [P3]."""
    pts = sorted((X_CERCHA[k], H_TECHO[k]) for k in H_TECHO)
    if x <= pts[0][0]:
        return pts[0][1]
    for (xa, ha), (xb, hb) in zip(pts, pts[1:]):
        if x <= xb:
            return ha + (hb - ha) * (x - xa) / (xb - xa)
    (xa, ha), (xb, hb) = pts[-2], pts[-1]
    return hb + (hb - ha) * (x - xb) / (xb - xa)


# --------------------------------------------------------------------------- maquinas [P4]
# frente: hacia donde mira el lado de uso ('N','S','E','O').  w = ancho visto de frente, d = fondo.
# peso_kg = peso propio estimado + carga maxima de trabajo (discos/placas), sin usuario.
MAQUINAS = [
    {"id": "M01", "tipo": "mancuernero", "nombre": "Mancuernero 2 niveles", "cat": "pág. 29",
     "precio": 2200, "alto": 0.85, "w": 3.00, "d": 0.70, "c": (bx(8.895), 0.53), "frente": "S",
     "peso_kg": 300, "zona": "peso_libre", "dim_cat": "aprox. 300 x 70 cm (sin dato)"},
    {"id": "M02", "tipo": "porta_barras", "nombre": "Porta barras", "cat": "pág. 29",
     "precio": 1300, "alto": 1.45, "w": 0.84, "d": 0.72, "c": (bx(10.93), 0.54), "frente": "S",
     "peso_kg": 160, "zona": "peso_libre", "dim_cat": "145 x 84 x 72 cm"},
    {"id": "M03", "tipo": "triceps", "nombre": "Tríceps a bloques", "cat": "pág. 22",
     "precio": 5300, "alto": 1.50, "w": 1.27, "d": 1.46, "c": (bx(12.155), 0.88), "frente": "S",
     "peso_kg": 240, "zona": "tren_superior", "dim_cat": "150 x 127 x 146 cm"},
    {"id": "M04", "tipo": "biceps", "nombre": "Máquina bíceps dual", "cat": "pág. 21",
     "precio": 5500, "alto": 1.73, "w": 1.28, "d": 1.18, "c": (bx(13.66), 0.79), "frente": "S",
     "peso_kg": 230, "zona": "tren_superior", "dim_cat": "173 x 118 x 128 cm"},
    {"id": "M05", "tipo": "banco", "nombre": "Banco graduable pro", "cat": "pág. 28",
     "precio": 2400, "alto": 0.50, "w": 0.65, "d": 1.45, "c": (bx(8.06), 2.24), "frente": "S",
     "peso_kg": 45, "zona": "peso_libre", "dim_cat": "sin dato (aprox. 65 x 145 cm)"},
    {"id": "M06", "tipo": "banco", "nombre": "Banco graduable pro", "cat": "pág. 28",
     "precio": 2400, "alto": 0.50, "w": 0.65, "d": 1.45, "c": (bx(9.305), 2.24), "frente": "S",
     "peso_kg": 45, "zona": "peso_libre", "dim_cat": "sin dato (aprox. 65 x 145 cm)"},
    {"id": "M07", "tipo": "extension", "nombre": "Extensión dual", "cat": "pág. 05",
     "precio": 6300, "alto": 1.80, "w": 1.30, "d": 1.68, "c": (bx(13.455), 2.99), "frente": "O",
     "peso_kg": 260, "zona": "tren_inferior", "dim_cat": "180 x 130 x 168 cm"},
    {"id": "M08", "tipo": "aductor", "nombre": "Aductor dual", "cat": "pág. 10",
     "precio": 5500, "alto": 1.80, "w": 1.65, "d": 1.55, "c": (bx(13.51), 5.345), "frente": "O",
     "peso_kg": 260, "zona": "tren_inferior", "dim_cat": "180 x 165 x 155 cm"},
    {"id": "M09", "tipo": "crossover", "nombre": "Crossover + pasamanos", "cat": "pág. 24",
     "precio": 7400, "alto": 2.30, "w": 3.30, "d": 1.10, "c": (bx(10.76), 5.95), "frente": "N",
     "peso_kg": 480, "zona": "tren_superior", "dim_cat": "230 x 330 x 110 cm"},
    {"id": "M10", "tipo": "prensa", "nombre": "Prensa olímpica", "cat": "pág. 03",
     "precio": 5800, "alto": 1.46, "w": 1.60, "d": 2.35, "c": (bx(7.577), 5.325), "frente": "N",
     "peso_kg": 540, "zona": "tren_inferior", "dim_cat": "146 x 160 x 235 cm"},
    {"id": "M11", "tipo": "hip_thrust", "nombre": "Hip thrust", "cat": "pág. 11",
     "precio": 4900, "alto": 0.50, "w": 2.20, "d": 1.90, "c": (3.72, 5.47), "frente": "N",
     "peso_kg": 290, "zona": "tren_inferior", "dim_cat": "50 x 220 x 190 cm"},
    {"id": "M12", "tipo": "press_plano", "nombre": "Press plano olímpico", "cat": "pág. 15",
     "precio": 2200, "alto": 1.22, "w": 2.20, "d": 1.67, "c": (1.185, 4.95), "frente": "O",
     "peso_kg": 250, "zona": "peso_libre", "dim_cat": "122 x 220 x 167 cm"},
    {"id": "M13", "tipo": "dominadas", "nombre": "Dominadas asistidas", "cat": "pág. 18",
     "precio": 4900, "alto": 2.23, "w": 1.15, "d": 1.15, "c": (5.925, 5.825), "frente": "N",
     "peso_kg": 270, "zona": "tren_superior", "dim_cat": "223 x 115 x 115 cm"},
]
# Posicion original de [P1] (para la lamina comparativa), en coordenadas del modelo
MAQUINAS_P1 = {
    "M11": (bx(3.985), 4.523, bx(6.184), 6.421),
    "M12": (1.839, 4.297, 3.508, 6.495),
    "M13": (0.305, 5.185, 1.455, 6.335),
}
ACCESORIOS = [
    # (descripcion, unidad, cantidad, precio unitario S/, referencia)
    ("Juego de mancuernas hexagonales 2.5 a 20 kg (8 pares)", "jgo", 1, 2160, "pág. 30"),
    ("Discos olímpicos (300 kg en total)", "kg", 300, 7.50, "pág. 30"),
    ("Barra olímpica certificada 220 cm con sujetadores", "und", 3, 850, "pág. 30"),
    ("Barra Z", "und", 1, 450, "pág. 30"),
    ("Barra recta", "und", 1, 450, "pág. 30"),
    ("Porta discos (junto a prensa y press plano)", "und", 2, 1300, "pág. 29"),
]
PORTA_DISCOS = [  # ubicacion de los 2 porta discos (x, y)
    (bx(6.60) + 0.0, 6.20), (2.32, 3.75),
]


def rect_maquina(m):
    """(x0, y0, x1, y1) en planta segun el frente."""
    cx, cy = m["c"]
    if m["frente"] in ("N", "S"):
        a, b = m["w"] / 2, m["d"] / 2
    else:
        a, b = m["d"] / 2, m["w"] / 2
    return (round(cx - a, 3), round(cy - b, 3), round(cx + a, 3), round(cy + b, 3))


# --------------------------------------------------------------------------- propuesta
RECEPCION = {
    "mostrador": (6.00, Y_HALL0, 6.50, 3.72), "alto_mostrador": 1.05,
    "zona_personal": (5.10, Y_HALL0, 6.00, 3.72),
    "panel_marca": (5.02, Y_HALL0, 5.10, 3.72), "alto_panel": 2.30,
    "lockers": (4.60, Y_HALL0, 5.02, 3.42), "alto_lockers": 1.80, "n_lockers": 12,
    "banca": (3.25, Y_HALL0, 4.05, 2.60),
    "estante": (5.12, Y_HALL0, 5.95, 2.50),
}
ZONA_FUNCIONAL = (bx(9.95), 2.00, bx(12.35), 4.20)          # grass sintetico + colchonetas
ESPEJOS = [  # (x0, x1) sobre el muro del fondo, de z = 0.35 a 2.15
    (bx(7.42), bx(11.40)),
]
CELOSIAS = [  # (x0, y0, x1, y1, altura) celosia de listones
    (1.66, 3.48, 0.15, 3.48, 2.20),      # oculta tanque y lavadero desde la sala
    (1.08, 3.20, 1.08, 3.48, 2.20),
]
# Cerramiento propuesto sobre el parapeto: (x0, y0, x1, y1, tipo)
CERRAMIENTO = [
    (bx(7.305), 0.0, L, 0.0, "panel_espejo"),      # fondo: panel ciego (lleva los espejos)
    (X_TRAG_E0, 0.0, bx(7.305), 0.0, "policarbonato"),
    (L, 0.0, L, W, "ventanal"),                    # lado calle: transparente
    (0.0, W, L, W, "policarbonato"),               # lado B
    (0.0, 2.05, 0.0, W, "policarbonato"),          # lado mercado
    (X_BANO_D, Y_HALL0, X_VANO0, Y_HALL0, "muro_luz"),   # tragaluz/escalera hacia la sala
    (X_ESC1 + T, 0.15, X_ESC1 + T, 2.05, "panel"),       # escalera hacia peso libre
]
PISOS = [
    {"id": "caucho", "nombre": "Caucho 15 mm (zona de máquinas)"},
    {"id": "caucho_pl", "nombre": "Caucho 25 mm (peso libre)", "rect": (bx(7.305), 0.15, bx(11.45), 3.35)},
    {"id": "grass", "nombre": "Grass sintético deportivo", "rect": ZONA_FUNCIONAL},
    {"id": "vinilico", "nombre": "Piso vinílico SPC (recepción y servicios)",
     "poligono": [(1.63, 1.81), (2.40, 1.81), (2.40, 2.05), (X_BANO_D, 2.05), (X_BANO_D, Y_HALL0),
                  (X_VANO0, Y_HALL0), (X_VANO0, Y_ESC1 - 0.9), (X_VANO1, Y_ESC1 - 0.9),
                  (X_VANO1, 3.90), (1.63, 3.90)]},
]
# Luminarias LED lineales 40 W colgadas de las cerchas secundarias (x, y, giro)
LUMINARIAS = [(x, y) for y in (1.05, 2.75, 4.45, 5.85)
              for x in (bx(8.6), bx(10.9), bx(13.2))] + \
             [(1.3, 4.45), (3.9, 4.45), (6.3, 4.45), (1.3, 5.85), (3.9, 5.85), (6.3, 5.85), (3.0, 3.0), (5.6, 3.0)]
VENTILADORES = [(bx(7.6), 0.35, "S"), (bx(11.6), 0.35, "S"), (L - 0.35, 3.9, "O"),
                (4.3, W - 0.35, "N"), (bx(9.0), W - 0.35, "N")]
EXTINTORES = [(X_VANO1 + 0.25, 2.12), (L - 0.30, 4.08)]
LUCES_EMERGENCIA = [(X_VANO0 + 0.5, Y_HALL0 + 0.05), (bx(11.0), W - 0.2), (2.0, 2.15)]
TOMACORRIENTES = [(5.55, Y_HALL0 + 0.05, "Recepción (doble) x2"), (5.2, Y_HALL0 + 0.05, "Equipo de sonido"),
                  (bx(9.4), 0.18, "Peso libre"), (L - 0.18, 1.9, "Lado calle"), (L - 0.18, 4.1, "Ventilador"),
                  (bx(8.9), W - 0.18, "Ventilador"), (4.3, W - 0.18, "Ventilador"), (0.18, 4.0, "Servicio")]

ZONAS = {
    "recepcion": {"nombre": "Recepción y lockers", "color": "#E24B4A"},
    "servicios": {"nombre": "SS.HH., duchas y lavadero", "color": "#5B8DB8"},
    "peso_libre": {"nombre": "Peso libre", "color": "#E8A33D"},
    "tren_superior": {"nombre": "Tren superior", "color": "#7A6FD1"},
    "tren_inferior": {"nombre": "Tren inferior", "color": "#3FA37C"},
    "funcional": {"nombre": "Funcional y estiramiento", "color": "#6BBF59"},
}


# --------------------------------------------------------------------------- verificaciones
def _dist_rect(a, b):
    dx = max(b[0] - a[2], a[0] - b[2], 0.0)
    dy = max(b[1] - a[3], a[1] - b[3], 0.0)
    return math.hypot(dx, dy)


def obstaculos():
    """Rectangulos fijos (nombre, rect)."""
    R = RECEPCION
    obs = [(m["id"] + " " + m["nombre"], rect_maquina(m)) for m in MAQUINAS]
    obs += [("Mostrador", R["mostrador"]), ("Panel de marca", R["panel_marca"]),
            ("Lockers", R["lockers"]), ("Banca", R["banca"]), ("Lavadero", LAVADERO["rect"]),
            ("Tanque/tragaluz SO", TANQUE["plataforma"])]
    return obs


def verificar():
    """Devuelve lista de (descripcion, valor_m, minimo_m, ok)."""
    M = {m["id"]: rect_maquina(m) for m in MAQUINAS}
    R = RECEPCION
    chk = []

    def paso(desc, a, b, minimo):
        d = round(_dist_rect(a, b), 2)
        chk.append((desc, d, minimo, d >= minimo - 1e-6))

    def valor(desc, v, minimo):
        chk.append((desc, round(v, 2), minimo, v >= minimo - 1e-6))

    # circulacion principal
    paso("Vestíbulo: lockers - hip thrust", R["lockers"], M["M11"], 1.10)
    paso("Hall de llegada: mostrador - dominadas", R["mostrador"], M["M13"], 1.20)
    paso("Eje principal: banco 1 - prensa", M["M05"], M["M10"], 1.10)
    valor("Ancho de la llegada de escalera", X_VANO1 - X_VANO0, 0.90)
    valor("Frente de baños libre (P-2 a hip thrust)", M["M11"][1] - 2.05, 1.50)
    paso("Frente de crossover libre (a zona funcional)", M["M09"], ZONA_FUNCIONAL, 1.10)
    # separaciones para cargar discos / acceso lateral
    paso("Press plano - hip thrust (carga de discos)", M["M12"], M["M11"], 0.55)
    paso("Hip thrust - dominadas (carga de discos)", M["M11"], M["M13"], 0.50)
    paso("Dominadas - prensa (carga de discos)", M["M13"], M["M10"], 0.55)
    paso("Prensa - crossover", M["M10"], M["M09"], 0.60)
    paso("Mancuernero - bancos (pasillo de mancuernas)", M["M01"], M["M05"], 0.60)
    paso("Bíceps - extensión (acceso)", M["M04"], M["M07"], 0.80)
    paso("Extensión - aductor (acceso)", M["M07"], M["M08"], 0.80)
    valor("Press plano: barra a muro lado B", (W - T) - M["M12"][3], 0.40)
    valor("Press plano: barra a tanque/lavadero", M["M12"][1] - LAVADERO["rect"][3], 0.40)
    # alturas
    for m in MAQUINAS:
        if m["alto"] >= 1.7:
            h = altura_techo(m["c"][0])
            chk.append(("Altura libre sobre %s (%.2f m de alto)" % (m["nombre"], m["alto"]),
                        round(h - m["alto"], 2), 0.10, h - m["alto"] >= 0.10))
    # choques
    obs = obstaculos()
    for i in range(len(obs)):
        for j in range(i + 1, len(obs)):
            a, b = obs[i][1], obs[j][1]
            if a[0] < b[2] - 1e-6 and b[0] < a[2] - 1e-6 and a[1] < b[3] - 1e-6 and b[1] < a[3] - 1e-6:
                chk.append(("CHOQUE %s / %s" % (obs[i][0], obs[j][0]), 0.0, 0.0, False))
    return chk


def areas():
    sala_e = (L - T - (X_ESC1 + T)) * (W - 2 * T)
    sala_o = (X_ESC1 + T - T) * (W - T - Y_HALL0) - 1.08 * (3.20 - Y_HALL0) - 0.55 * (3.41 - Y_HALL0)
    vest = (X_BANO_D - 1.63) * (Y_HALL0 - 2.05) + (2.40 - 1.63) * (2.05 - 1.81)
    util = sala_e + sala_o + vest
    huella = sum(m["w"] * m["d"] for m in MAQUINAS)
    return {"techada": round(L * W - X_TRAG_E0 * Y_BLOQUE, 1), "sala": round(util, 1),
            "sala_este": round(sala_e, 1), "sala_oeste": round(sala_o + vest, 1),
            "banos": 2.83 + 1.86, "huella_maquinas": round(huella, 1),
            "ocupacion": round(100 * huella / util, 0), "aforo": int(util // 4.6)}


def cargas():
    """Carga repartida equivalente por maquina (kg/m2 sobre su huella + 0.3 m de contorno)."""
    filas = []
    for m in MAQUINAS:
        a = (m["w"] + 0.6) * (m["d"] + 0.6)
        total = m["peso_kg"] + 85                  # + un usuario
        filas.append((m["id"], m["nombre"], m["peso_kg"], total, round(a, 2), round(total / a)))
    return filas


def escena():
    """Diccionario con todo lo necesario para el modelo 3D."""
    return {
        "nombre": NOMBRE, "L": L, "W": W, "T": T, "H_PARAPETO": H_PARAPETO, "H_BANO": H_BANO,
        "Y_BLOQUE": Y_BLOQUE, "X_BANO_D": X_BANO_D, "Y_HALL0": Y_HALL0,
        "muros": MUROS, "puertas": PUERTAS, "banos": BANOS, "tragaluces": TRAGALUCES,
        "tanque": TANQUE, "lavadero": LAVADERO, "escalera": ESCALERA, "columnas": COLUMNAS,
        "x_cercha": X_CERCHA, "h_techo": H_TECHO, "cerchas_sec_y": CERCHAS_SEC_Y,
        "peralte": PERALTE_CERCHA, "translucido": TRANSLUCIDO,
        "maquinas": [dict(m, rect=rect_maquina(m)) for m in MAQUINAS],
        "porta_discos": PORTA_DISCOS, "recepcion": RECEPCION, "zona_funcional": ZONA_FUNCIONAL,
        "espejos": ESPEJOS, "celosias": CELOSIAS, "cerramiento": CERRAMIENTO, "pisos": PISOS,
        "luminarias": LUMINARIAS, "ventiladores": VENTILADORES, "extintores": EXTINTORES,
    }


def exportar_escena(ruta=None):
    ruta = ruta or os.path.join(AQUI, "render3d", "web", "escena.json")
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(escena(), f, ensure_ascii=False, indent=1)
    return ruta


if __name__ == "__main__":
    print(NOMBRE, "-", LUGAR)
    print("Modelo: %.2f x %.2f m" % (L, W), "| áreas:", areas())
    mal = 0
    for desc, v, mn, ok in verificar():
        print("  [%s] %-58s %5.2f m (mín. %.2f)" % ("ok" if ok else "NO", desc, v, mn))
        mal += (not ok)
    print("Verificaciones con observación:", mal)
    print("Inversión en máquinas (catálogo): S/ %s" % format(sum(m["precio"] for m in MAQUINAS), ","))
    print("Escena:", exportar_escena())
