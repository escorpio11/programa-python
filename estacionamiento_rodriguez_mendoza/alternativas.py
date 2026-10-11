"""
Alternativas de uso del terreno: qué construir (o no) para maximizar la ganancia
presente y futura. Compara el estacionamiento del anteproyecto con locales
comerciales, uso mixto por etapas, cancha sintética, local de eventos, hostal,
terminal de vans y con alquilar o vender el terreno.

Montos en soles (S/) de octubre de 2026, con IGV. Las rentas, tarifas y costos
vienen de la investigación de mercado (ver `FUENTES` y la hoja «Fuentes» del
Excel); casi no hay precios publicados de Mendoza, así que muchos son
estimaciones por comparables (Chachapoyas, Moyobamba, Lima) que deben validarse
en campo antes de invertir.

Cada alternativa se arma por fases (año de inversión, partidas, ingresos y
gastos). El flujo a 20 años usa la misma tasa (10 %), crecimiento (3 %) y
criterios que `rentabilidad.py`.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import geometria as g
import rentabilidad as rb

TASA = rb.TASA                    # 10 % anual
CRECIMIENTO = rb.CRECIMIENTO      # 3 % anual en rentas, tarifas y gastos
HORIZONTE = rb.HORIZONTE          # 20 años
IMPREVISTOS = 0.10                # supervisión e imprevistos sobre obras valorizadas a precio de contratista
AREA_LOTE = round(g.LOTE.area, 1)
VALOR_M2 = (500.0, 750.0, 1000.0)         # S/ por m² de terreno (pesimista, base, optimista) - requiere tasación
PLUSVALIA = 0.03                  # valorización anual del terreno (nominal)
DEPOSITO = 0.06                   # rendimiento de un depósito a plazo en caja municipal (referencial)
IMP_ALQUILER = 0.05               # renta de primera categoría: 5 % efectivo sobre el alquiler cobrado
GUARDIAN = rb.SUELDO_RMV * rb.FACTOR_LABORAL * 12   # un trabajador a sueldo mínimo con cargas (S/ por año)
ESCENARIOS = ("Pesimista", "Base", "Optimista")
FACTOR_COSTO = (1.15, 1.00, 0.92)        # sobrecosto / ahorro de obra por escenario


@dataclass
class Fase:
    nombre: str
    anio: int                                  # año en que se invierte; opera desde el año siguiente
    partidas: list                             # [(descripción, unidad, cantidad, precio unitario)]
    ingreso: tuple                             # ingreso bruto potencial S/ por mes (pes, base, opt), precios de hoy
    ocupacion: tuple = (1.0, 1.0, 1.0)         # fracción cobrada (1 - vacancia)
    opex_fijo: float = 0.0                     # S/ por año a precios de hoy
    opex_var: float = 0.0                      # fracción del ingreso cobrado (insumos, comisiones, personal por evento)
    impuesto: float = 0.0                      # fracción del ingreso cobrado
    rampa: tuple = (0.7, 0.9)                  # ingreso relativo en el 1.er y 2.º año de operación
    vida: int = 50                             # años, para el valor residual lineal al año 20
    reposiciones: list = field(default_factory=list)   # [(años después de invertir, monto a precios de hoy)]
    capex_fijo: float | None = None            # inversión total ya calculada (incluye imprevistos)

    def capex(self, esc=1):
        if self.capex_fijo is not None:
            return self.capex_fijo * FACTOR_COSTO[esc]
        sub = sum(c * p for _, _, c, p in self.partidas)
        return sub * (1 + IMPREVISTOS) * FACTOR_COSTO[esc]

    def neto_regimen(self, esc=1):
        """Utilidad neta anual en régimen (después de la rampa), a precios de hoy."""
        cobrado = self.ingreso[esc] * 12 * self.ocupacion[esc]
        return cobrado * (1 - self.opex_var - self.impuesto) - self.opex_fijo


@dataclass
class Opcion:
    clave: str
    nombre: str
    corto: str
    resumen: str
    fases: list
    riesgo: str            # bajo / medio / alto
    futuro: str            # qué tan bien conserva o crea opciones futuras
    gestion: str           # esfuerzo de gestión para el propietario
    notas: list = field(default_factory=list)


def _p(desc, und, cant, pu):
    return (desc, und, cant, pu)


# --------------------------------------------------------------------------
# Alternativas
# --------------------------------------------------------------------------
_RB_ESC = [rb.ingreso_mensual(e) for e in rb.ESCENARIOS]
_CAPEX_A = rb.capex()[-1]
_OPEX_A = sum(rb.opex_anual(_CAPEX_A, True).values())

OPCIONES = [
    Opcion(
        "A", "Estacionamiento techado (anteproyecto actual)", "Estac. techado",
        "28 plazas techadas con estructura metálica, 5 motos y 2 mototaxis; guardián contratado.",
        [Fase("Estacionamiento techado", 0, [], tuple(_RB_ESC), opex_fijo=_OPEX_A, rampa=tuple(rb.RAMPA), vida=30,
              reposiciones=[(rb.MANT_MAYOR_ANIO, rb.MANT_MAYOR * _CAPEX_A)], capex_fijo=_CAPEX_A)],
        "medio", "media: la estructura metálica se puede desmontar, pero ocupa todo el lote", "media (guardián, cobranza)",
        ["Es el proyecto de las láminas A-01 a E-04. Ingresos y gastos idénticos a rentabilidad.py (con guardián).",
         "Si lo opera el propietario o un familiar, la TIR base sube a ≈ 11 %."]),
    Opcion(
        "B", "Estacionamiento descubierto de bajo costo", "Estac. descubierto",
        "Afirmado, cerco de malla, caseta y portones; 28 plazas a la intemperie. Uso de transición mientras se decide.",
        [Fase("Estacionamiento descubierto", 0, [
            _p("Afirmado compactado e=0.20 m con bombeo", "m²", 680, 40.0),
            _p("Cerco de malla galvanizada h=2.0 m en frentes", "ml", 44, 120.0),
            _p("Portones de malla 3.0 m (ingreso y salida)", "und", 2, 2200.0),
            _p("Caseta prefabricada de control con SS.HH. básico", "und", 1, 9000.0),
            _p("Postes con reflector LED", "und", 3, 1800.0),
            _p("Cuneta de drenaje y descarga a la vía", "ml", 25, 180.0),
            _p("Señalización, topellantas y numeración", "glb", 1, 4000.0),
            _p("Licencia de funcionamiento, ITSE y trámites", "glb", 1, 3500.0)],
            (1800.0, rb.ingreso_mensual(rb.ESCENARIO_SIN_TECHO), 4000.0),
            opex_fijo=GUARDIAN + 1200 + 2000 + 1200 + 1000 + rb.NRUS_MES * 12 + 1200, rampa=tuple(rb.RAMPA), vida=10,
            reposiciones=[(6, 10000.0)])],
        "bajo", "alta: casi todo es reversible y deja el terreno libre", "media (guardián, cobranza)",
        ["Con lluvia de ≈ 2,000 mm al año se asume menor tarifa y ocupación que el techado (como en el escenario "
         "«sin techo» de rentabilidad.py).",
         "Sirve como fase 0 para medir la demanda real de estacionamiento antes de techar."]),
]

# Locales comerciales en los dos frentes (fase 1 del uso mixto)
_LOCALES = Fase(
    "Locales comerciales (1.er piso)", 0, [
        _p("Franja comercial de 1 piso y 8 m de fondo en albañilería confinada, con zapatas y columnas para 3 pisos, "
           "puertas enrollables y SS.HH. por local: esquina de 100 m², 3 locales de 39-48 m² al jirón y núcleo de "
           "escalera, SS.HH. y depósito de 26 m² junto a B", "m²", 260.6, 1350.0),
        _p("Estudio de suelos, expediente técnico y licencia (Modalidad C)", "glb", 1, 22000.0)],
    # esquina 100 m² a S/ 14/20/26 por m²; 3 locales (134.7 m²) a S/ 12/18/25 por m² al mes
    (100 * 14 + 134.7 * 12, 100 * 20 + 134.7 * 18, 100 * 26 + 134.7 * 25),
    ocupacion=(0.75, 0.85, 0.92), opex_fijo=2400 + 2000 + 1500, impuesto=IMP_ALQUILER, rampa=(0.6, 0.9), vida=50)

_COCHERA = Fase(
    "Cochera de abonados (fondo, descubierta)", 0, [
        _p("Afirmado compactado e=0.20 m con bombeo", "m²", 540, 40.0),
        _p("Drenaje del patio", "ml", 20, 220.0),
        _p("Portón corredizo automatizado de 6 m (ingreso y salida) con 40 controles", "und", 1, 12000.0),
        _p("Cerco de albañilería en el fondo C-D", "ml", 30, 330.0),
        _p("Iluminación LED y CCTV de 4 cámaras", "glb", 1, 7500.0),
        _p("Señalización, numeración y topellantas", "glb", 1, 2400.0)],
    (18 * 70.0, 18 * 90.0, 18 * 110.0), ocupacion=(0.6, 0.75, 0.9),
    opex_fijo=1000 + 1000 + rb.NRUS_MES * 12 + 600, rampa=(0.6, 0.85), vida=10, reposiciones=[(8, 8000.0)])

OPCIONES += [
    Opcion(
        "C", "Locales comerciales en los dos frentes + cochera de abonados", "Locales + cochera",
        "Franja comercial de 8 m de fondo sobre el jirón y la esquina (local ancla de 100 m² + 3 locales de 39-48 m²), "
        "con estructura lista para 2 pisos más, y 18 plazas de abonados atrás con ingreso y salida por la calle "
        "lateral (portón automático de 6 m).",
        [_LOCALES, _COCHERA],
        "medio", "alta: deja pagada la estructura para crecer en altura cuando el mercado lo pida",
        "baja (alquiler pasivo, contratos anuales)",
        ["El local de esquina es el candidato a inquilino ancla: farmacia, caja municipal o microfinanciera, "
         "ferretería, agencia de una cooperativa cafetalera.",
         "La cochera funciona sin guardián: abonados mensuales con control remoto y cámaras."]),
    Opcion(
        "D", "Uso mixto completo: C + 2 pisos de minidepartamentos (año 3)", "Mixto + deptos",
        "Fase 1 igual a C. En el año 3, cuando opere el hospital, 2 pisos con 8 minidepartamentos de 1 dormitorio "
        "para personal de salud y del sector público.",
        [_LOCALES, _COCHERA, Fase(
            "2 pisos de minidepartamentos", 3, [
                _p("2 pisos sobre los locales: 8 minidepartamentos de 1 dormitorio (≈ 45 m² útiles), escalera y pasillo",
                   "m²", 521, 1450.0),
                _p("Expediente y licencia de ampliación", "glb", 1, 15000.0)],
            (8 * 450.0, 8 * 600.0, 8 * 750.0), ocupacion=(0.7, 0.85, 0.92),
            opex_fijo=5000 + 7500 + 1500 + 1600, impuesto=IMP_ALQUILER, rampa=(0.6, 0.9), vida=50)],
        "medio-alto", "alta (usa los aires, pero es la forma final del inmueble)", "media (10 inquilinos)",
        ["Rentas de minidepartamento estimadas por debajo de Chachapoyas (S/ 1,100-1,400 por departamento de 2 dormitorios).",
         "Mivivienda y Techo Propio no financian construir para alquilar: la fase 2 se pagaría con ahorros, "
         "utilidades de la fase 1 o crédito hipotecario/comercial (≈ 13-14 % en cajas)."]),
    Opcion(
        "E", "Uso mixto con consultorios: C + 1 piso de consultorios (año 2)", "Mixto + consultorios",
        "Fase 1 igual a C. En el año 2, un piso con 7 consultorios para alquilar a médicos, odontólogos, "
        "laboratorio u óptica, aprovechando la llegada del nuevo hospital II-1.",
        [_LOCALES, _COCHERA, Fase(
            "1 piso de consultorios", 2, [
                _p("1 piso sobre los locales: 7 consultorios de 15-20 m² con lavatorio, sala de espera y SS.HH.",
                   "m²", 260.6, 1500.0),
                _p("Expediente y licencia de ampliación", "glb", 1, 12000.0)],
            (7 * 400.0, 7 * 550.0, 7 * 700.0), ocupacion=(0.6, 0.8, 0.9),
            opex_fijo=2400 + 4000 + 1000 + 1200, impuesto=IMP_ALQUILER, rampa=(0.5, 0.85), vida=50)],
        "medio-alto", "alta", "media",
        ["Depende de que el hospital abra pronto y de su distancia al terreno: confirmar antes de construir."]),
    Opcion(
        "F", "Cancha sintética techada (fútbol 5)", "Cancha techada",
        "Cancha de 25 × 15 m (la mayor que cabe), techada por la lluvia, con vestuarios y caseta.",
        [Fase("Cancha sintética techada", 0, [
            _p("Base granular, losa de nivelación y drenaje", "m²", 450, 70.0),
            _p("Grass sintético instalado (25 × 15 m + bandas)", "m²", 400, 115.0),
            _p("Estructura metálica y cobertura TR-4 sobre la cancha", "m²", 570, 330.0),
            _p("Mallas perimetrales, arcos y redes", "glb", 1, 9000.0),
            _p("Iluminación LED (8 kW)", "glb", 1, 14000.0),
            _p("Vestuarios, SS.HH. y caseta (albañilería)", "m²", 40, 1300.0),
            _p("Cerco de albañilería en frentes y portones", "ml", 50, 330.0),
            _p("Expediente y licencias", "glb", 1, 15000.0)],
            # horas vendidas por día × tarifa × 30 días
            (2.5 * 50 * 30, 3.5 * 55 * 30, 5.0 * 60 * 30),
            opex_fijo=GUARDIAN + 8000 + 4000 + 2000 + 1500 + rb.NRUS_MES * 12 + 1200, rampa=(0.7, 0.9), vida=30,
            reposiciones=[(9, 400 * 115.0 * 1.1), (18, 400 * 115.0 * 1.1)])],
        "medio-alto", "baja: ocupa todo el lote y tapa el frente comercial al jirón", "alta (horarios nocturnos, encargado)",
        ["En Iquitos 19 canchas cobraban la misma tarifa y el 40 % de usuarios la consideraba cara: el mercado se satura rápido.",
         "Juego nocturno con luces y ruido junto a un vecino: riesgo de quejas y de condiciones en la licencia."]),
    Opcion(
        "G", "Local de eventos (salón de recepciones)", "Local de eventos",
        "Salón techado de 420 m² con cocina de servicio, SS.HH., mobiliario y patio de ingreso.",
        [Fase("Local de eventos", 0, [
            _p("Salón de 420 m²: estructura metálica, muros, piso cerámico, cielo raso y acústica básica", "m²", 420, 950.0),
            _p("Cocina de servicio, SS.HH. y depósito", "m²", 50, 1400.0),
            _p("Mobiliario, sonido e iluminación decorativa", "glb", 1, 30000.0),
            _p("Patio de ingreso afirmado", "m²", 300, 40.0),
            _p("Expediente, licencias, ITSE y aforo", "glb", 1, 18000.0)],
            (2.5 * 1200.0, 4 * 1500.0, 6 * 1800.0), opex_fijo=4000 + 5800 + 2500 + 4000 + 6000, opex_var=0.20,
            impuesto=0.10, rampa=(0.6, 0.85), vida=40)],
        "alto", "media", "alta (agenda, limpieza, vecinos)",
        ["Ingreso muy estacional (fiestas patronales, promociones, matrimonios) y competencia de locales comunales."]),
    Opcion(
        "H", "Hostal de 16 habitaciones (3 pisos)", "Hostal",
        "Edificio de 3 pisos con 16 habitaciones con baño y recepción.",
        [Fase("Hostal", 0, [
            _p("Edificio de 3 pisos para hostal (750 m² techados)", "m²", 750, 1700.0),
            _p("Equipamiento de habitaciones y recepción", "und", 16, 6000.0),
            _p("Expediente, licencia y categorización MINCETUR", "glb", 1, 30000.0)],
            (16 * 65 * 30.0, 16 * 75 * 30.0, 16 * 85 * 30.0), ocupacion=(0.25, 0.35, 0.45),
            opex_fijo=3 * GUARDIAN + 14000 + 15400 + 4000 + 12000 + 3000, opex_var=0.25, impuesto=0.12,
            rampa=(0.5, 0.8), vida=50)],
        "alto", "media", "muy alta (operación 24 h)",
        ["El 94 % de los visitantes de la provincia son de la misma provincia y el 91 % se aloja con familiares; "
         "la ocupación de hospedajes en Amazonas ronda el 20-23 %."]),
    Opcion(
        "K", "Terminal o paradero de vans y colectivos", "Terminal de vans",
        "Patio de maniobras de concreto, andenes techados, 4 boleterías, sala de espera y SS.HH.",
        [Fase("Terminal de vans", 0, [
            _p("Pavimento de concreto para patio de maniobras", "m²", 480, 130.0),
            _p("Techado metálico de andenes", "m²", 150, 400.0),
            _p("Sala de espera, 4 boleterías y SS.HH.", "m²", 120, 1300.0),
            _p("Cerco, portones y señalización", "glb", 1, 20000.0),
            _p("Estudio de impacto vial, habilitación técnica MTC y licencias", "glb", 1, 25000.0)],
            # boleterías + cobro por salida (salidas por día × S/ por salida × 30)
            (4 * 400 + 12 * 3 * 30.0, 4 * 600 + 20 * 4 * 30.0, 4 * 800 + 28 * 5 * 30.0),
            opex_fijo=GUARDIAN + 6000 + 4000 + 3500 + 2000 + 2500, impuesto=0.0, rampa=(0.6, 0.85), vida=40)],
        "alto", "media", "alta (autorizaciones, empresas de transporte)",
        ["Hay 4 empresas autorizadas en la ruta a Chachapoyas y no se halló un terminal formal, pero el negocio "
         "depende de la municipalidad y la DRTC y congestiona la vía principal."]),
    Opcion(
        "J", "Alquilar el terreno sin construir a un operador", "Alquiler del terreno",
        "Arrendar el lote completo (depósito de materiales, concesionario de motos, paradero, feria) con contrato de "
        "3-10 años; el inquilino hace sus mejoras.",
        [Fase("Alquiler del terreno", 0, [], (1500.0, 2400.0, 4000.0), opex_fijo=400, impuesto=IMP_ALQUILER,
              rampa=(1.0, 1.0), vida=1, capex_fijo=0.0)],
        "medio", "media: contratos de varios años congelan el terreno", "muy baja",
        ["Supone S/ 1.8-4.9 por m² al mes; en Moyobamba (ciudad mucho mayor) se piden ≈ S/ 10 por m². "
         "Encontrar un inquilino para 820 m² en Mendoza es incierto."]),
]

OPC = {o.clave: o for o in OPCIONES}
AREA_LOCALES = 234.7          # m² alquilables de la franja comercial (sin el núcleo de servicios)
ORDEN = ["C", "E", "D", "A", "B", "F", "G", "K", "H", "J"]


# --------------------------------------------------------------------------
# Flujo de caja y métricas
# --------------------------------------------------------------------------
def flujo(op: Opcion, esc=1, tasa_crec=CRECIMIENTO):
    """Filas por año 0..HORIZONTE con inversión, ingresos, gastos, impuestos, reposiciones y valor residual."""
    filas = []
    acum = 0.0
    for t in range(HORIZONTE + 1):
        inv = ing = opx = imp = rep = res = 0.0
        crec = (1 + tasa_crec) ** max(t - 1, 0)
        for f in op.fases:
            if t == f.anio:
                inv -= f.capex(esc)
            k = t - f.anio
            if k >= 1:
                r = f.rampa[k - 1] if k <= len(f.rampa) else 1.0
                cobrado = f.ingreso[esc] * 12 * f.ocupacion[esc] * r * crec
                ing += cobrado
                opx -= f.opex_fijo * crec + f.opex_var * cobrado
                imp -= f.impuesto * cobrado
            for (dk, monto) in f.reposiciones:
                if k == dk:
                    rep -= monto * crec * FACTOR_COSTO[esc]
            if t == HORIZONTE and f.vida > 1:
                res += f.capex(esc) * max(0.0, 1 - (HORIZONTE - f.anio) / f.vida)
        neto = inv + ing + opx + imp + rep + res
        acum += neto
        filas.append(dict(anio=t, inversion=inv, ingresos=ing, opex=opx, impuestos=imp, reposiciones=rep,
                          residual=res, neto=neto, acum=acum))
    return filas


def recuperacion(filas):
    for a, b in zip(filas, filas[1:]):
        if a["acum"] < 0 <= b["acum"]:
            sin_res = b["neto"] - b["residual"]
            if sin_res <= 0:
                return None
            return a["anio"] + (-a["acum"]) / sin_res
    return 0.0 if filas and filas[0]["acum"] >= 0 else None


def metricas(op: Opcion, esc=1):
    fl = flujo(op, esc)
    netos = [f["neto"] for f in fl]
    capex = sum(f.capex(esc) for f in op.fases)
    neto_reg = sum(f.neto_regimen(esc) for f in op.fases)
    terreno = AREA_LOTE * VALOR_M2[1]
    presente = sum(f["neto"] - f["inversion"] for f in fl[1:4]) / 3     # utilidad promedio de los años 1-3 (sin inversiones)
    construido = sum(f.capex(esc) * max(0.0, 1 - (HORIZONTE - f.anio) / f.vida) for f in op.fases if f.vida > 1)
    return dict(
        clave=op.clave, nombre=op.nombre, corto=op.corto, capex=capex, capex_inicial=sum(f.capex(esc) for f in op.fases if f.anio == 0),
        neto_regimen=neto_reg, neto_mes=neto_reg / 12, presente=presente,
        rend_capex=(neto_reg / capex) if capex > 0 else None,
        rend_total=neto_reg / (capex + terreno),
        van=rb.van(netos, TASA), tir=rb.tir(netos) if capex > 0 else None, payback=recuperacion(fl) if capex > 0 else 0.0,
        tir_terreno=tir_con_terreno(netos, terreno),
        valor20=terreno * (1 + PLUSVALIA) ** HORIZONTE + construido, flujo=fl)


def tir_con_terreno(netos, terreno, plusvalia=PLUSVALIA):
    """TIR del propietario contando el terreno como capital: lo «aporta» hoy a valor de mercado y lo
    recupera valorizado en el año 20. Se compara con vender y depositar (≈ 5.7 % neto)."""
    f = list(netos)
    f[0] -= terreno
    f[-1] += terreno * (1 + plusvalia) ** HORIZONTE
    return rb.tir(f)


def venta_terreno(esc=1):
    precio = AREA_LOTE * VALOR_M2[esc]
    renta = precio * DEPOSITO * (1 - IMP_ALQUILER)
    return dict(precio=precio, renta_anual=renta, renta_mes=renta / 12)


def umbral_ingreso(op: Opcion, fase_idx: int, esc=1):
    """Ingreso mensual potencial de una fase que hace VAN(fase) = 0 al 10 % (bisección)."""
    import copy
    base = copy.deepcopy(op)
    fase = base.fases[fase_idx]
    solo = Opcion(op.clave, op.nombre, op.corto, "", [fase], op.riesgo, op.futuro, op.gestion)

    def van_con(x):
        ing = list(fase.ingreso)
        ing[esc] = x
        fase.ingreso = tuple(ing)
        return rb.van([f["neto"] for f in flujo(solo, esc)], TASA)

    lo, hi = 0.0, fase.ingreso[esc] * 6 + 1000
    for _ in range(80):
        mid = (lo + hi) / 2
        if van_con(mid) < 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def sensibilidad_locales(rentas=(10, 12, 14, 16, 18, 20, 22, 25, 30)):
    """VAN de la alternativa C según la renta promedio de los locales (S/ por m² al mes)."""
    import copy
    out = []
    base_m2 = OPC["C"].fases[0].ingreso[1] / AREA_LOCALES
    for r in rentas:
        op = copy.deepcopy(OPC["C"])
        ing = list(op.fases[0].ingreso)
        ing[1] = ing[1] * r / base_m2
        op.fases[0].ingreso = tuple(ing)
        m = metricas(op, 1)
        out.append((r, m["van"], m["tir"]))
    return out


def tabla_comparativa(esc=1):
    return [metricas(OPC[k], esc) for k in ORDEN]


# --------------------------------------------------------------------------
# Fuentes y validación en campo (resumen de la investigación, oct-2026)
# --------------------------------------------------------------------------
FUENTES = [
    ("Población", "Ciudad de Mendoza: 5,130 hab. (Censo 2017) y 3,356 en 2007; provincia: 29,998 hab. (2017); "
     "la provincia creció 1.3 % anual entre 2017 y 2025 (Censos 2025). Estimado 2026: 6,400-7,300 hab. en la ciudad.",
     "INEI (citypopulation.de); INEI, nota de prensa de los Censos 2025", "2017 / 2026", "media"),
    ("Eje comercial", "Agencia del Banco de la Nación en Jr. Toribio Rodríguez de Mendoza N.º 309: el jirón es el eje "
     "comercial e institucional.", "Banco de la Nación (ubicador de agencias)", "2025", "alta"),
    ("Hospital", "Nuevo Hospital María Auxiliadora II-1 (CUI 2195952), más de S/ 100 MM, 89.9 % de avance en abril de 2026; "
     "la Contraloría advirtió riesgos de energización y de personal.", "GORE Amazonas, Contraloría, InfoObras",
     "abr-2026", "alta"),
    ("Carretera", "PE-8B Chachapoyas–Rodríguez de Mendoza: 76.9 km asfaltados y 10 puentes (≈ S/ 369 MM), aún en "
     "estudio definitivo.", "MTC / Provías Nacional (CUI 2546400)", "2023-2025", "alta"),
    ("Turismo", "El 94 % de los visitantes de la provincia son de la misma provincia y el 91 % se aloja con "
     "familiares; ocupación de hospedajes de Amazonas ≈ 19-23 %; arribos 2024: 382,622 (−10.8 %).",
     "Tesis UNALM; MINCETUR", "2023-2025", "media"),
    ("Transporte", "4 empresas autorizadas por la DRTC en rutas Mendoza–Chachapoyas; no se halló terminal formal.",
     "DRTC Amazonas (resoluciones de autorización)", "2022-2024", "alta"),
    ("Alquiler de locales", "Chachapoyas, Jr. Amazonas: S/ 54-98 por m² al mes en locales de 25-55 m² y S/ 24 en 127 m²; "
     "Moyobamba: S/ 29-40; Tarapoto: S/ 28 (466 m² para financieras).", "Avisos en portales inmobiliarios",
     "oct-2026", "media"),
    ("Alquiler de locales (Mendoza)", "Estimado: S/ 12-30 por m² al mes en el jirón principal y S/ 6-15 en calles "
     "secundarias (sin avisos publicados en Mendoza).", "Estimación por comparables", "oct-2026", "baja"),
    ("Cuartos y departamentos", "Chachapoyas: cuarto con baño S/ 380-480; departamento de 2 dormitorios S/ 1,100-1,400. "
     "Estimado para Mendoza: minidepartamento S/ 400-650.", "Avisos; estimación por comparables", "oct-2026", "baja"),
    ("Valor del terreno", "Chachapoyas: lote céntrico a ≈ S/ 955 por m²; tasación en Huambo (misma provincia) "
     "≈ S/ 680 por m² en 2019. Estimado para el lote: S/ 500-1,000 por m².", "Avisos; tasación REPEV", "2019-2026", "baja"),
    ("Costo de construcción", "Albañilería confinada S/ 1,200-1,800 por m² (referencia nacional 2026); estimado para "
     "Mendoza: local de 1 piso S/ 950-1,250 y 2-3 pisos S/ 1,100-1,750 según acabados.",
     "Guías de costos 2026; RM 277-2025-VIVIENDA (valores unitarios)", "2026", "baja"),
    ("Cancha sintética", "Cancha de ≈ 700 m² en Lima: S/ 130-166 mil sin techo; cancha techada en Espinar: S/ 375 mil. "
     "Tarifas: Iquitos S/ 80 por hora; estimado para Mendoza S/ 50-70.", "Proveedores; Antapaccay; tesis", "2022-2026", "media"),
    ("Tributos", "Alquiler como persona natural: 5 % efectivo sobre lo cobrado, sin IGV; impuesto predial 0.2 % / 0.6 % / "
     "1.0 % por tramos de autovalúo; UIT 2026 = S/ 5,500.", "SUNAT; TUO Ley de Tributación Municipal", "2026", "alta"),
    ("Financiamiento", "Hipotecario bancario 7.2-7.9 % TEA; cajas 12.7-14.3 %; crédito microempresa 47-59 %. "
     "Mivivienda y Techo Propio no financian construir para alquilar.", "SBS; cajas municipales; Fondo Mivivienda",
     "2026", "media"),
    ("Grifo", "Exige 50 m de distancia a colegios, iglesias y mercados, más el informe técnico de Osinergmin: "
     "probablemente inviable en el centro.", "D.S. 054-93-EM; Osinergmin", "vigente", "media"),
]

VALIDAR = [
    ("Alquiler real de locales en el Jr. Rodríguez de Mendoza",
     "Recorrer 2-3 cuadras, anotar carteles «se alquila» y preguntar a 8-10 inquilinos cuánto pagan, cuántos m² "
     "tienen y qué garantía dejaron. Es el dato que más cambia el resultado."),
    ("Interés de un inquilino ancla para la esquina",
     "Conversar con farmacias de cadena, cajas municipales (Piura, Sullana, Trujillo, Arequipa), Mibanco, "
     "cooperativas cafetaleras y ferreterías; pedir una carta de intención antes de construir."),
    ("Certificado de Parámetros Urbanísticos y Edificatorios",
     "Pedirlo a la Municipalidad Provincial de Rodríguez de Mendoza: confirma usos permitidos, altura máxima, "
     "retiros y estacionamientos exigidos (decide si caben 3 pisos)."),
    ("Fecha de apertura y ubicación del nuevo hospital",
     "Consultar InfoObras (CUI 2195952), la DIRESA Amazonas o la obra: define la demanda de consultorios, "
     "minidepartamentos y estacionamiento."),
    ("Tasación del terreno",
     "Pedir una tasación a un perito REPEV (≈ S/ 500-1,000) y revisar compraventas recientes en notarías o SUNARP."),
    ("Costo real de obra",
     "Pedir 2-3 cotizaciones a contratistas de Mendoza o Chachapoyas para casco y acabado económico."),
    ("Zona sísmica y estudio de suelos",
     "Confirmar en la E.030 vigente si Rodríguez de Mendoza es zona 2 o 3 y hacer el estudio de mecánica de suelos "
     "antes de dimensionar zapatas para 3 pisos."),
]


# --------------------------------------------------------------------------
# Hoja de cálculo con fórmulas
# --------------------------------------------------------------------------
def exportar_xlsx(ruta):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter as L
    from openpyxl.worksheet.datavalidation import DataValidation

    wb = Workbook()
    azul = PatternFill("solid", fgColor="DCE6F1")
    gris = PatternFill("solid", fgColor="EDEDED")
    amarillo = PatternFill("solid", fgColor="FFF2CC")
    verde = PatternFill("solid", fgColor="E2EFDA")
    negrita = Font(bold=True)
    titulo = Font(bold=True, size=14)
    fino = Side(style="thin", color="999999")
    borde = Border(left=fino, right=fino, top=fino, bottom=fino)
    soles = '"S/ "#,##0'
    pct = "0.0%"

    def caja(c, fill=None, fmt=None, bold=False):
        c.border = borde
        if fill:
            c.fill = fill
        if fmt:
            c.number_format = fmt
        if bold:
            c.font = negrita
        return c

    # ---------------- Supuestos globales
    ws = wb.active
    ws.title = "Supuestos"
    ws["A1"] = "SUPUESTOS GENERALES (celdas amarillas = editables)"
    ws["A1"].font = titulo
    gl = [
        ("Escenario (1 = pesimista, 2 = base, 3 = optimista)", 2, None, "esc"),
        ("Tasa de descuento anual", TASA, pct, "tasa"),
        ("Crecimiento anual de rentas, tarifas y gastos", CRECIMIENTO, pct, "crec"),
        ("Supervisión e imprevistos de obra", IMPREVISTOS, pct, "imprev"),
        ("Factor de costo de obra - pesimista", FACTOR_COSTO[0], "0.00", "fc1"),
        ("Factor de costo de obra - base", FACTOR_COSTO[1], "0.00", "fc2"),
        ("Factor de costo de obra - optimista", FACTOR_COSTO[2], "0.00", "fc3"),
        ("Área del terreno (m²)", AREA_LOTE, "#,##0.0", "area"),
        ("Valor del terreno (S/ por m²) - requiere tasación", VALOR_M2[1], soles, "vm2"),
        ("Valorización anual del terreno", PLUSVALIA, pct, "plusv"),
        ("Rendimiento de un depósito a plazo (alternativa a vender)", DEPOSITO, pct, "dep"),
        ("Impuesto al alquiler (renta de 1.ª categoría, efectivo)", IMP_ALQUILER, pct, "impalq"),
    ]
    R = {}
    for i, (et, v, fmt, k) in enumerate(gl):
        r = 3 + i
        ws.cell(r, 1, et)
        caja(ws.cell(r, 2, v), amarillo, fmt)
        R[k] = f"Supuestos!$B${r}"
    dv = DataValidation(type="list", formula1='"1,2,3"', allow_blank=False)
    ws.add_data_validation(dv)
    dv.add("B3")
    r = 3 + len(gl) + 1
    ws.cell(r, 1, "Valor del terreno (S/)").font = negrita
    caja(ws.cell(r, 2, f"={R['area']}*{R['vm2']}"), verde, soles, True)
    R["terreno"] = f"Supuestos!$B${r}"
    ws.cell(r + 1, 1, "Factor de costo del escenario elegido")
    caja(ws.cell(r + 1, 2, f"=CHOOSE({R['esc']},{R['fc1']},{R['fc2']},{R['fc3']})"), verde, "0.00")
    R["fc"] = f"Supuestos!$B${r + 1}"
    ws.cell(r + 3, 1, "Cómo usar: cambie el escenario o cualquier celda amarilla (aquí o en cada hoja de alternativa); "
                      "la hoja «Comparación» se recalcula sola.").font = Font(italic=True, color="555555")
    ws.column_dimensions["A"].width = 62
    ws.column_dimensions["B"].width = 16

    # ---------------- Hojas por alternativa
    anios = list(range(HORIZONTE + 1))
    col0 = 3                      # columna C = año 0
    kpi = {}
    for op in [OPC[k] for k in ORDEN]:
        sh = wb.create_sheet(f"{op.clave} {op.corto}"[:31])
        sh["A1"] = f"{op.clave}. {op.nombre}"
        sh["A1"].font = titulo
        sh["A2"] = op.resumen
        sh["A2"].alignment = Alignment(wrap_text=True)
        sh.merge_cells("A2:L2")
        sh.row_dimensions[2].height = 30
        fila = 4
        info_fases = []
        for fi, f in enumerate(op.fases):
            sh.cell(fila, 1, f"Fase {fi + 1}: {f.nombre}").font = negrita
            sh.cell(fila, 1).fill = gris
            fila += 1
            if f.capex_fijo is None:
                for j, t in enumerate(["Partida", "Und.", "Cantidad", "P. unitario", "Parcial"], 1):
                    caja(sh.cell(fila, j, t), azul, bold=True)
                fila += 1
                p0 = fila
                for (d, u, c, pu) in f.partidas:
                    sh.cell(fila, 1, d).alignment = Alignment(wrap_text=True)
                    sh.cell(fila, 2, u)
                    caja(sh.cell(fila, 3, c), amarillo, "#,##0.0")
                    caja(sh.cell(fila, 4, pu), amarillo, soles)
                    caja(sh.cell(fila, 5, f"=C{fila}*D{fila}"), None, soles)
                    fila += 1
                sh.cell(fila, 4, "Inversión (con imprevistos y factor de escenario)")
                caja(sh.cell(fila, 5, f"=SUM(E{p0}:E{fila - 1})*(1+{R['imprev']})*{R['fc']}"), verde, soles, True)
            else:
                sh.cell(fila, 4, "Inversión (calculada en su propio modelo, por factor de escenario)")
                caja(sh.cell(fila, 5, f"={f.capex_fijo}*{R['fc']}"), verde, soles, True)
            cap = f"$E${fila}"
            fila += 1
            params = [
                ("Año de inversión (opera desde el año siguiente)", f.anio, "0", "anio"),
                ("Ingreso bruto potencial S/ por mes - pesimista", f.ingreso[0], soles, "i1"),
                ("Ingreso bruto potencial S/ por mes - base", f.ingreso[1], soles, "i2"),
                ("Ingreso bruto potencial S/ por mes - optimista", f.ingreso[2], soles, "i3"),
                ("Ocupación cobrada - pesimista", f.ocupacion[0], pct, "o1"),
                ("Ocupación cobrada - base", f.ocupacion[1], pct, "o2"),
                ("Ocupación cobrada - optimista", f.ocupacion[2], pct, "o3"),
                ("Gastos fijos S/ por año (personal, energía, mantenimiento, seguro, predial)", f.opex_fijo, soles, "of"),
                ("Gastos variables (% del ingreso cobrado)", f.opex_var, pct, "ov"),
                ("Impuestos (% del ingreso cobrado)", f.impuesto, pct, "im"),
                ("Ingreso relativo 1.er año de operación", f.rampa[0], pct, "r1"),
                ("Ingreso relativo 2.º año de operación", f.rampa[1], pct, "r2"),
                ("Vida útil para valor residual (años)", f.vida, "0", "vida"),
            ]
            for n, (dk, monto) in enumerate(f.reposiciones[:2]):
                params.append((f"Reposición {n + 1}: años después de invertir", dk, "0", f"rk{n}"))
                params.append((f"Reposición {n + 1}: monto a precios de hoy", monto, soles, f"rm{n}"))
            ref = {"cap": cap}
            for (et, v, fmt, k) in params:
                sh.cell(fila, 4, et)
                caja(sh.cell(fila, 5, v), amarillo, fmt)
                ref[k] = f"$E${fila}"
                fila += 1
            info_fases.append((f, ref))
            fila += 1

        # Flujo
        sh.cell(fila, 1, "FLUJO DE CAJA (S/ nominales)").font = negrita
        fila += 1
        caja(sh.cell(fila, 1, "Concepto / año"), azul, bold=True)
        for t in anios:
            caja(sh.cell(fila, col0 + t, t), azul, bold=True)
        fila_anio = fila
        fila += 1
        filas_tot = {}
        conceptos = ["Inversión", "Ingresos cobrados", "Gastos", "Impuestos", "Reposiciones", "Valor residual (año 20)"]
        filas_det = {c: [] for c in conceptos}
        for fi, (f, ref) in enumerate(info_fases):
            esc_ing = f"CHOOSE({R['esc']},{ref['i1']},{ref['i2']},{ref['i3']})"
            esc_ocu = f"CHOOSE({R['esc']},{ref['o1']},{ref['o2']},{ref['o3']})"
            for c in conceptos:
                sh.cell(fila, 1, f"  {c} - fase {fi + 1}").font = Font(color="666666")
                for t in anios:
                    A = f"{L(col0 + t)}${fila_anio}"
                    k = f"({A}-{ref['anio']})"
                    crec = f"(1+{R['crec']})^MAX({A}-1,0)"
                    if c == "Inversión":
                        fx = f"=IF({A}={ref['anio']},-{ref['cap']},0)"
                    elif c == "Ingresos cobrados":
                        fx = (f"=IF({k}>=1,{esc_ing}*12*{esc_ocu}*IF({k}=1,{ref['r1']},IF({k}=2,{ref['r2']},1))*{crec},0)")
                    elif c == "Gastos":
                        fx = f"=IF({k}>=1,-{ref['of']}*{crec}-{ref['ov']}*{L(col0 + t)}{fila - 1},0)"
                    elif c == "Impuestos":
                        fx = f"=-{ref['im']}*{L(col0 + t)}{fila - 2}"
                    elif c == "Reposiciones":
                        partes = [f"IF({k}={ref[f'rk{n}']},-{ref[f'rm{n}']}*{crec}*{R['fc']},0)"
                                  for n in range(min(2, len(f.reposiciones)))]
                        fx = "=" + ("+".join(partes) if partes else "0")
                    else:
                        fx = (f"=IF(AND({A}={HORIZONTE},{ref['vida']}>1),{ref['cap']}*MAX(0,1-({HORIZONTE}-{ref['anio']})/{ref['vida']}),0)")
                    caja(sh.cell(fila, col0 + t, fx), None, soles)
                filas_det[c].append(fila)
                fila += 1
        for c in conceptos:
            sh.cell(fila, 1, c).font = negrita
            for t in anios:
                col = L(col0 + t)
                caja(sh.cell(fila, col0 + t, "=" + "+".join(f"{col}{r}" for r in filas_det[c])), gris, soles)
            filas_tot[c] = fila
            fila += 1
        sh.cell(fila, 1, "FLUJO NETO").font = negrita
        for t in anios:
            col = L(col0 + t)
            caja(sh.cell(fila, col0 + t, "=" + "+".join(f"{col}{filas_tot[c]}" for c in conceptos)), verde, soles, True)
        f_neto = fila
        fila += 1
        sh.cell(fila, 1, "Flujo acumulado").font = negrita
        for t in anios:
            col = L(col0 + t)
            fx = f"={col}{f_neto}" if t == 0 else f"={L(col0 + t - 1)}{fila}+{col}{f_neto}"
            caja(sh.cell(fila, col0 + t, fx), None, soles)
        f_acum = fila
        fila += 1
        sh.cell(fila, 1, "Flujo del propietario contando el terreno (lo aporta hoy y lo recupera valorizado)").font = negrita
        for t in anios:
            col = L(col0 + t)
            extra = f"-{R['terreno']}" if t == 0 else (f"+{R['terreno']}*(1+{R['plusv']})^{HORIZONTE}" if t == HORIZONTE else "")
            caja(sh.cell(fila, col0 + t, f"={col}{f_neto}{extra}"), None, soles)
        f_ter = fila
        fila += 2
        rng = f"{L(col0)}{f_neto}:{L(col0 + HORIZONTE)}{f_neto}"
        rng1 = f"{L(col0 + 1)}{f_neto}:{L(col0 + HORIZONTE)}{f_neto}"
        res = [
            ("Inversión total", "=-" + f"SUM({L(col0)}{filas_tot['Inversión']}:{L(col0 + HORIZONTE)}{filas_tot['Inversión']})", soles),
            ("VAN al " + f"{TASA:.0%}", f"={L(col0)}{f_neto}+NPV({R['tasa']},{rng1})", soles),
            ("TIR", f'=IFERROR(IRR({rng}),"no aplica")', pct),
            ("Año en que se recupera la inversión (acumulado ≥ 0)",
             f'=IFERROR(INDEX({L(col0)}{fila_anio}:{L(col0 + HORIZONTE)}{fila_anio},MATCH(TRUE,INDEX({L(col0)}{f_acum}:{L(col0 + HORIZONTE)}{f_acum}>=0,0),0)),"no se recupera")', "0"),
            ("Utilidad neta del año 5 (S/ nominales)", f"={L(col0 + 5)}{f_neto}-{L(col0 + 5)}{filas_tot['Inversión']}", soles),
            ("TIR contando el terreno", f'=IFERROR(IRR({L(col0)}{f_ter}:{L(col0 + HORIZONTE)}{f_ter}),"no aplica")', pct),
        ]
        kpi[op.clave] = {}
        for (et, fx, fmt) in res:
            sh.cell(fila, 1, et).font = negrita
            caja(sh.cell(fila, col0, fx), verde, fmt, True)
            kpi[op.clave][et] = f"'{sh.title}'!${L(col0)}${fila}"
            fila += 1
        sh.column_dimensions["A"].width = 58
        sh.column_dimensions["B"].width = 7
        for t in anios:
            sh.column_dimensions[L(col0 + t)].width = 12
        sh.column_dimensions["D"].width = 14
        sh.column_dimensions["E"].width = 14
        sh.freeze_panes = "B4"

    # ---------------- Comparación
    wc = wb.create_sheet("Comparación", 1)
    wc["A1"] = "COMPARACIÓN DE ALTERNATIVAS (escenario elegido en «Supuestos»)"
    wc["A1"].font = titulo
    cab = ["Alt.", "Alternativa", "Inversión total", "VAN al 10 %", "TIR", "Recupera en el año",
           "Utilidad neta año 5", "Rinde sobre (terreno + inversión)", "TIR contando el terreno", "Riesgo", "Futuro",
           "Gestión"]
    for j, t in enumerate(cab, 1):
        caja(wc.cell(3, j, t), azul, bold=True)
        wc.cell(3, j).alignment = Alignment(wrap_text=True, vertical="center")
    wc.row_dimensions[3].height = 32
    for i, k in enumerate(ORDEN):
        op = OPC[k]
        r = 4 + i
        wc.cell(r, 1, k)
        wc.cell(r, 2, op.nombre)
        caja(wc.cell(r, 3, f"={kpi[k]['Inversión total']}"), None, soles)
        caja(wc.cell(r, 4, f"={kpi[k]['VAN al ' + f'{TASA:.0%}']}"), None, soles)
        caja(wc.cell(r, 5, f"={kpi[k]['TIR']}"), None, pct)
        caja(wc.cell(r, 6, f"={kpi[k]['Año en que se recupera la inversión (acumulado ≥ 0)']}"), None, "0")
        caja(wc.cell(r, 7, f"={kpi[k]['Utilidad neta del año 5 (S/ nominales)']}"), None, soles)
        caja(wc.cell(r, 8, f"=G{r}/((1+{R['crec']})^4)/(C{r}+{R['terreno']})"), None, pct)
        caja(wc.cell(r, 9, f"={kpi[k]['TIR contando el terreno']}"), None, pct)
        wc.cell(r, 10, op.riesgo)
        wc.cell(r, 11, op.futuro)
        wc.cell(r, 12, op.gestion)
        for j in (1, 2, 10, 11, 12):
            wc.cell(r, j).border = borde
            wc.cell(r, j).alignment = Alignment(wrap_text=True, vertical="top")
    r = 4 + len(ORDEN) + 1
    wc.cell(r, 2, "Vender el terreno hoy (referencia)").font = negrita
    caja(wc.cell(r, 3, f"={R['terreno']}"), verde, soles, True)
    wc.cell(r, 4, "Precio de venta estimado; depositado al")
    caja(wc.cell(r, 5, f"={R['dep']}"), None, pct)
    wc.cell(r, 6, "rendiría por año:")
    caja(wc.cell(r, 7, f"={R['terreno']}*{R['dep']}*(1-{R['impalq']})"), verde, soles, True)
    caja(wc.cell(r, 8, f"={R['dep']}*(1-{R['impalq']})"), None, pct)
    caja(wc.cell(r, 9, f"={R['dep']}*(1-{R['impalq']})"), None, pct)
    wc.cell(r + 2, 2, "Lectura: «Rinde sobre (terreno + inversión)» compara la utilidad del año 5 (a precios de hoy) con "
                      "todo el capital comprometido, incluido el valor del terreno. «TIR contando el terreno» trata el "
                      "lote como si se aportara hoy a valor de mercado y se recuperara valorizado en el año 20: si es "
                      "menor que vender y depositar (fila de referencia), la alternativa no paga el terreno.").alignment = Alignment(wrap_text=True)
    wc.merge_cells(start_row=r + 2, start_column=2, end_row=r + 2, end_column=12)
    wc.row_dimensions[r + 2].height = 58
    for col, w in zip("ABCDEFGHIJKL", (5, 50, 14, 14, 9, 11, 14, 14, 12, 10, 34, 24)):
        wc.column_dimensions[col].width = w

    # ---------------- Fuentes y validación
    wf = wb.create_sheet("Fuentes")
    wf["A1"] = "DATOS DE MERCADO Y FUENTES (investigación oct-2026)"
    wf["A1"].font = titulo
    for j, t in enumerate(["Tema", "Dato", "Fuente", "Fecha", "Confianza"], 1):
        caja(wf.cell(3, j, t), azul, bold=True)
    for i, fila_f in enumerate(FUENTES):
        for j, v in enumerate(fila_f, 1):
            c = wf.cell(4 + i, j, v)
            c.alignment = Alignment(wrap_text=True, vertical="top")
            c.border = borde
    r = 4 + len(FUENTES) + 2
    wf.cell(r, 1, "QUÉ VALIDAR EN CAMPO ANTES DE INVERTIR").font = negrita
    for i, (q, como) in enumerate(VALIDAR):
        wf.cell(r + 1 + i, 1, q).alignment = Alignment(wrap_text=True, vertical="top")
        wf.cell(r + 1 + i, 2, como).alignment = Alignment(wrap_text=True, vertical="top")
    for col, w in zip("ABCDE", (28, 80, 36, 12, 11)):
        wf.column_dimensions[col].width = w
    wb.save(ruta)


if __name__ == "__main__":
    import sys
    for esc in (1, 0, 2):
        print(f"\n== Escenario {ESCENARIOS[esc]} ==")
        print(f"{'Alt':4}{'Inversión':>12}{'Neto/mes':>10}{'Presente':>11}{'VAN':>12}{'TIR':>8}{'Recup.':>8}{'R.total':>8}{'TIR+T':>8}")
        for m in tabla_comparativa(esc):
            tir = f"{m['tir'] * 100:6.1f}%" if m["tir"] is not None else "   n.a."
            pb = f"{m['payback']:6.1f}" if m["payback"] is not None else "   no"
            print(f"{m['clave']:4}{m['capex']:12,.0f}{m['neto_mes']:10,.0f}{m['presente']:11,.0f}{m['van']:12,.0f}{tir:>8}{pb:>8}"
                  f"{m['rend_total'] * 100:7.1f}%{m['tir_terreno'] * 100:7.1f}%  {m['corto']}")
        v = venta_terreno(esc)
        print(f"Venta del terreno: S/ {v['precio']:,.0f} -> depositado rinde S/ {v['renta_mes']:,.0f} al mes")
    print("\nUmbral de ingreso (VAN fase = 0):")
    print(" minideptos D:", round(umbral_ingreso(OPC['D'], 2) / 8), "S/ por depto potencial (ocupación base 85 %)")
    print(" consultorios E:", round(umbral_ingreso(OPC['E'], 2) / 7), "S/ por consultorio (ocupación 80 %)")
    print(" cancha F:", round(umbral_ingreso(OPC['F'], 0) / 30 / 55, 2), "h/día a S/ 55")
    print(" locales C:", round(umbral_ingreso(OPC['C'], 0) / AREA_LOCALES, 1), "S/ por m² promedio")
    print("\nSensibilidad C:", [(r, round(v), round(t * 100, 1)) for r, v, t in sensibilidad_locales()])
    if len(sys.argv) > 1:
        exportar_xlsx(sys.argv[1])
        print("xlsx:", sys.argv[1])
