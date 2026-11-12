"""
Alternativas de uso del terreno: qué hacer con el lote para maximizar la ganancia
presente y futura. Compara el estacionamiento del anteproyecto con locales
comerciales (completos o solo la esquina), cochera de abonados, uso mixto con
pisos superiores, cancha sintética, local de eventos, hostal, terminal de vans,
arrendar el lote o ceder la esquina en derecho de superficie, y vender el terreno.

Montos en soles (S/) de octubre de 2026, con IGV. Las rentas, tarifas y costos
vienen de la investigación de mercado (ver `FUENTES` y la hoja «Fuentes» del
Excel) y de una revisión adversarial posterior que los ajustó a una ciudad de
≈ 6,500 habitantes: casi no hay precios publicados de Mendoza, así que son
estimaciones por comparables (Chachapoyas, Moyobamba, Bagua Grande, Lima) que
deben validarse en campo antes de invertir.

Cada alternativa se arma por fases (año de inversión, partidas, ingresos y
gastos). El flujo a 20 años usa la misma tasa (10 %), crecimiento (3 %) y
criterios que `rentabilidad.py`.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field

import geometria as g
import rentabilidad as rb

TASA = rb.TASA                    # 10 % anual
CRECIMIENTO = rb.CRECIMIENTO      # 3 % anual en rentas, tarifas, gastos y costos de obra
HORIZONTE = rb.HORIZONTE          # 20 años
IMPREVISTOS = 0.10                # supervisión e imprevistos sobre obras valorizadas a precio de contratista
AREA_LOTE = round(g.LOTE.area, 1)
ESCENARIOS = ("Pesimista", "Base", "Optimista")
VALOR_M2 = (400.0, 600.0, 850.0)          # S/ por m² de terreno (lote grande: descuento frente a lotes chicos) - requiere tasación
PLUSVALIA = (0.03, 0.045, 0.06)           # valorización anual del terreno (nominal) por escenario
DEPOSITO = 0.06                   # depósito a plazo en caja municipal (referencial, 5.2-7.1 % en 2026)
IMP_INTERES = 0.0                 # intereses de depósitos de personas naturales: exonerados (art. 19 LIR; verificar vigencia)
IMP_ALQUILER = 0.05               # renta de primera categoría: 5 % efectivo sobre el alquiler cobrado
GUARDIAN = rb.SUELDO_RMV * rb.FACTOR_LABORAL * 12   # un trabajador a sueldo mínimo con cargas (S/ por año)
FACTOR_COSTO = (1.15, 1.00, 0.92)        # sobrecosto / ahorro de obra por escenario
PU_FRANJA = 1500.0                # S/ por m²: 1.er piso en pórticos/dual de C.A. diseñado para 3 pisos (zona sísmica 3 hasta verificar)
AREA_LOCALES = 234.7              # m² alquilables de la franja comercial (esquina 100 + 3 locales 134.7)
PLAZAS_COCHERA = 18               # plazas del anteproyecto que quedan detrás de la franja comercial


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
        """Inversión a precios de hoy (la de fases futuras se ajusta por crecimiento en el flujo)."""
        if self.capex_fijo is not None:
            return self.capex_fijo * FACTOR_COSTO[esc]
        sub = sum(c * p for _, _, c, p in self.partidas)
        return sub * (1 + IMPREVISTOS) * FACTOR_COSTO[esc]

    def capex_nominal(self, esc=1):
        return self.capex(esc) * (1 + CRECIMIENTO) ** max(self.anio - 1, 0)

    def neto_regimen(self, esc=1):
        """Flujo neto anual en régimen (después de la rampa), a precios de hoy, con las reposiciones prorrateadas."""
        cobrado = self.ingreso[esc] * 12 * self.ocupacion[esc]
        repos = sum(m for _, m in self.reposiciones) * FACTOR_COSTO[esc] / HORIZONTE
        return cobrado * (1 - self.opex_var - self.impuesto) - self.opex_fijo - repos

    def anio_regimen(self):
        return self.anio + len(self.rampa) + 1


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
    capital: str = "propio"   # propio / sin capital


def _p(desc, und, cant, pu):
    return (desc, und, cant, pu)


# --------------------------------------------------------------------------
# Piezas reutilizables
# --------------------------------------------------------------------------
def _cochera(plazas_rentables: int, nombre="Cochera de abonados (fondo, descubierta)", anio=0):
    """Cochera sin personal (abonados mensuales con control remoto y cámaras). La demanda de abonados es
    8 / 12 / 16 a S/ 60 / 75 / 90 al mes, limitada por las plazas que no se asignan a los locales."""
    demanda = (8, 12, 16)
    tarifa = (60.0, 75.0, 90.0)
    ingreso = tuple(min(d, plazas_rentables) * t for d, t in zip(demanda, tarifa))
    return Fase(nombre, anio, [
        _p("Afirmado compactado e=0.20 m con bombeo", "m²", 540, 40.0),
        _p("Drenaje del patio", "ml", 20, 220.0),
        _p("Portón telescópico automatizado de 6.5 m con 40 controles + puerta peatonal", "glb", 1, 15500.0),
        _p("Cerco de albañilería en el fondo C-D", "ml", 30, 330.0),
        _p("Iluminación LED y CCTV de 4 cámaras", "glb", 1, 7500.0),
        _p("Señalización, numeración y topellantas", "glb", 1, 2400.0)],
        ingreso, ocupacion=(0.6, 0.7, 0.8), opex_fijo=1000 + 1000 + rb.NRUS_MES * 12 + 600, rampa=(0.6, 0.85),
        vida=10, reposiciones=[(10, 33330.0)])


def _esquina(anio=0):
    return Fase("Local de esquina (100 m²)", anio, [
        _p("Local de esquina de 100 m² en pórticos de C.A. diseñados para 3 pisos, puertas enrollables y SS.HH.",
           "m²", 100, PU_FRANJA),
        _p("Estudio de suelos, proyecto y licencia", "glb", 1, 20000.0)],
        (1000.0, 1300.0, 2000.0), ocupacion=(0.7, 0.8, 0.9), opex_fijo=1000 + 900 + 600,
        impuesto=IMP_ALQUILER, rampa=(0.5, 0.8), vida=50)


def _locales_jiron(anio=0):
    return Fase("3 locales al jirón + núcleo de escalera", anio, [
        _p("3 locales de 39-48 m² (134.7 m²) y núcleo de escalera, SS.HH. y depósito de 26 m² junto a B, en pórticos "
           "de C.A. diseñados para 3 pisos", "m²", 160.6, PU_FRANJA),
        _p("Ampliación del proyecto y licencia", "glb", 1, 12000.0)],
        tuple(134.7 * r for r in (12.0, 15.0, 18.0)), ocupacion=(0.7, 0.8, 0.9), opex_fijo=1400 + 1300 + 900,
        impuesto=IMP_ALQUILER, rampa=(0.5, 0.8), vida=50)


_RB_PART, _RB_SUB = rb.capex()[0], rb.capex()[1]
_CAPEX_A = _RB_SUB * (1 + IMPREVISTOS)        # mismo recargo que el resto (la memoria usa 10 % GG + 7 % imprevistos)
# Demanda de estacionamiento en Mendoza (la misma para A, B y la cochera): abonados de auto, autos de rotación por
# día (requieren personal) y motos, en los escenarios pesimista / base / optimista.
DEMANDA_ABONADOS = (8, 12, 18)
DEMANDA_TICKETS = (6, 9, 14)
DEMANDA_MOTOS = (3, 5, 7)
_ING_A = tuple(a * 120 + t * 4.5 * 30 + m * 40 for a, t, m in zip(DEMANDA_ABONADOS, DEMANDA_TICKETS, DEMANDA_MOTOS))
_ING_B = tuple(a * 85 + t * 3.5 * 30 + m * 35 for a, t, m in zip((6, 10, 14), (5, 7, 11), (3, 4, 6)))
_OPEX_A = sum(rb.opex_anual(rb.capex()[-1], True).values())

OPCIONES = [
    Opcion(
        "J", "Arrendar el lote completo a un operador", "Arrendar el lote",
        "Contrato de 3-10 años con reajuste anual y garantía (depósito de materiales, concesionario o taller de motos, "
        "paradero, feria); el inquilino hace sus mejoras.",
        [Fase("Arriendo del lote", 0, [], (600.0, 1000.0, 1800.0), ocupacion=(0.6, 0.75, 0.9), opex_fijo=400,
              impuesto=IMP_ALQUILER, rampa=(0.5, 1.0), vida=1, capex_fijo=0.0)],
        "medio", "media: un contrato largo congela el lote (pactar salida anticipada con aviso)", "muy baja",
        ["Supone S/ 600-1,800 al mes por los 820 m² (S/ 0.7-2.2 por m²) con 10-40 % del tiempo sin inquilino. "
         "En Mendoza no se encontraron avisos de lotes en alquiler: la existencia de un interesado es la incógnita."],
        capital="sin capital"),
    Opcion(
        "L", "Ceder la esquina en derecho de superficie (el inquilino construye)", "Esquina cedida",
        "Una cadena, caja, cooperativa o comercio construye su local en la esquina (build-to-suit o derecho de "
        "superficie a 10-20 años) y paga renta por el suelo. El fondo queda libre para arrendarlo o para una "
        "cochera si se prevenden abonos.",
        [Fase("Derecho de superficie en la esquina", 0, [], (560.0, 800.0, 1200.0), ocupacion=(0.95, 0.95, 0.95),
              opex_fijo=300, impuesto=IMP_ALQUILER, rampa=(0.5, 1.0), vida=1, capex_fijo=0.0)],
        "medio", "alta: al vencer el plazo la edificación queda para el propietario", "baja",
        ["Renta del suelo ≈ 6 % anual del valor de ≈ 150-200 m² de terreno. Requiere un inquilino solvente que quiera "
         "construir: confirmar el interés antes de contar con este ingreso."],
        capital="sin capital"),
    Opcion(
        "C1", "Local de esquina + cochera de abonados", "Esquina + cochera",
        "Solo el local ancla de 100 m² en la esquina (estructura para 3 pisos) y la cochera del fondo; los 3 locales "
        "del jirón quedan para una etapa posterior.",
        [_esquina(), _cochera(16)],
        "medio", "alta: la esquina queda lista para crecer y el resto del frente sigue libre", "baja",
        ["Construir la esquina solo con un contrato firmado: con un inquilino a la renta del mercado local "
         "(S/ 1,300 al mes) no paga el 10 %."]),
    Opcion(
        "C", "Locales en la esquina y el jirón + cochera de abonados", "Locales + cochera",
        "Franja comercial de 8 m de fondo sobre el jirón y la esquina (ancla de 100 m² + 3 locales de 39-48 m²), "
        "estructura para 2 pisos más y 12 plazas de abonados atrás (las otras 6 quedan para los locales), con "
        "ingreso y salida por la calle lateral.",
        [_esquina(), _locales_jiron(), _cochera(12)],
        "medio-alto", "alta: deja la estructura lista para crecer en altura", "baja (alquiler pasivo)",
        ["Los 3 locales del jirón solo pagan el 10 % con rentas de S/ 19-24 por m² (≈ S/ 870-1,080 por un local de "
         "45 m²); la renta local estimada es S/ 12-18."]),
    Opcion(
        "E", "C + 1 piso de consultorios (año 2)", "C + consultorios",
        "Fase 1 igual a C. En el año 2, un piso con 7 consultorios, ascensor y SS.HH. accesible para médicos, "
        "odontólogos, laboratorio u óptica.",
        [_esquina(), _locales_jiron(), _cochera(12), Fase(
            "1 piso de consultorios", 2, [
                _p("1 piso sobre los locales: 7 consultorios de 15-20 m² con lavatorio, sala de espera y SS.HH. accesible",
                   "m²", 260.6, 1650.0),
                _p("Ascensor de 2 paradas con pozo", "glb", 1, 85000.0),
                _p("Proyecto y licencia (Modalidad D por uso salud)", "glb", 1, 18000.0)],
            (7 * 300.0, 7 * 400.0, 7 * 500.0), ocupacion=(0.6, 0.7, 0.85),
            opex_fijo=2400 + 4000 + 1000 + 1200 + 3000, impuesto=IMP_ALQUILER, rampa=(0.5, 0.85), vida=50)],
        "alto", "media", "media",
        ["Uso salud: Modalidad D, ruta accesible (ascensor) y categoría A2 (U = 1.5) en la E.030; la estructura de la "
         "etapa 1 tendría que diseñarse para eso. El nuevo hospital reemplaza al actual y su ubicación aún no se conoce."]),
    Opcion(
        "D", "C + 2 pisos de minidepartamentos (año 3)", "C + minideptos",
        "Fase 1 igual a C. En el año 3, 2 pisos con 8 minidepartamentos de 1 dormitorio para personal de salud y del "
        "sector público.",
        [_esquina(), _locales_jiron(), _cochera(12), Fase(
            "2 pisos de minidepartamentos", 3, [
                _p("2 pisos sobre los locales: 8 minidepartamentos de 1 dormitorio (≈ 45 m² útiles), escalera y pasillo",
                   "m²", 521, 1650.0),
                _p("Expediente y licencia de ampliación", "glb", 1, 15000.0)],
            (8 * 400.0, 8 * 500.0, 8 * 600.0), ocupacion=(0.7, 0.85, 0.92),
            opex_fijo=5000 + 7500 + 1500 + 1600, impuesto=IMP_ALQUILER, rampa=(0.6, 0.9), vida=50)],
        "alto", "media", "media (8 inquilinos)",
        ["Un minidepartamento a S/ 500 al mes (rango local estimado S/ 400-650) frente a un costo de obra de "
         "≈ S/ 100 mil por unidad. Mivivienda y Techo Propio no financian construir para alquilar."]),
    Opcion(
        "A", "Estacionamiento techado (anteproyecto actual)", "Estac. techado",
        "28 plazas techadas con estructura metálica, 5 motos y 2 mototaxis; guardián contratado.",
        [Fase("Estacionamiento techado", 0, [], _ING_A, opex_fijo=_OPEX_A, rampa=tuple(rb.RAMPA), vida=30,
              reposiciones=[(rb.MANT_MAYOR_ANIO, rb.MANT_MAYOR * _CAPEX_A)], capex_fijo=_CAPEX_A)],
        "medio", "media: la estructura metálica se puede desmontar, pero ocupa todo el lote", "media (guardián, cobranza)",
        ["Demanda base de 12 abonados a S/ 120, 9 autos de rotación al día a S/ 4.50 y 5 motos a S/ 40 (la memoria "
         "del anteproyecto suponía 18 abonados); gastos de rentabilidad.py con guardián y el mismo 10 % de "
         "imprevistos que el resto. Operarlo en familia ahorra ≈ S/ 15 mil al año de sueldo."]),
    Opcion(
        "B", "Estacionamiento descubierto de bajo costo", "Estac. descubierto",
        "Afirmado, cerco de malla, caseta y portones; 28 plazas a la intemperie, con guardián. Demanda base: 10 "
        "abonados a S/ 85, 7 autos de rotación al día a S/ 3.50 y 4 motos a S/ 35.",
        [Fase("Estacionamiento descubierto", 0, [
            _p("Afirmado compactado e=0.20 m con bombeo", "m²", 680, 40.0),
            _p("Cerco de malla galvanizada h=2.0 m en frentes", "ml", 44, 120.0),
            _p("Portones de malla 3.0 m (ingreso y salida)", "und", 2, 2200.0),
            _p("Caseta prefabricada de control con SS.HH. básico", "und", 1, 9000.0),
            _p("Postes con reflector LED", "und", 3, 1800.0),
            _p("Cuneta de drenaje y descarga a la vía", "ml", 25, 180.0),
            _p("Señalización, topellantas y numeración", "glb", 1, 4000.0),
            _p("Licencia de funcionamiento, ITSE y trámites", "glb", 1, 3500.0)],
            _ING_B,
            opex_fijo=GUARDIAN + 1200 + 2000 + 1200 + 1000 + rb.NRUS_MES * 12 + 1200, rampa=tuple(rb.RAMPA), vida=10,
            reposiciones=[(6, 10000.0), (12, 28600.0)])],
        "medio", "alta: casi todo es reversible", "media (guardián, cobranza)",
        ["No sirve como «puente» de pocos meses: si luego se construyen locales se pierden ≈ S/ 40 mil (cerco, "
         "portones, caseta y afirmado bajo la franja)."]),
    Opcion(
        "F", "Cancha sintética techada (fulbito)", "Cancha techada",
        "Cancha recreativa de 25 × 15 m (sin franja de seguridad; con franja de 1 m ≈ 25 × 14), techada por la lluvia, "
        "con vestuarios y caseta.",
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
            (2.0 * 45 * 30, 2.5 * 50 * 30, 3.5 * 55 * 30),
            opex_fijo=GUARDIAN + 6000 + 4000 + 2000 + 1500 + rb.NRUS_MES * 12 + 1200, rampa=(0.7, 0.9), vida=30,
            reposiciones=[(9, 400 * 115.0 * 1.1), (18, 400 * 115.0 * 1.1)])],
        "alto", "baja: ocupa todo el lote y tapa el frente comercial al jirón", "alta (horarios nocturnos, encargado)",
        ["No cumple el ancho mínimo de futsal (16 m). Hay losas municipales gratuitas y tarifas municipales de "
         "S/ 22-30 por hora; juego nocturno con luces y ruido junto a un vecino."]),
    Opcion(
        "G", "Local de eventos (salón de recepciones)", "Local de eventos",
        "Salón techado de 420 m² con cocina de servicio, SS.HH., mobiliario y patio de ingreso.",
        [Fase("Local de eventos", 0, [
            _p("Salón de 420 m²: estructura metálica, muros, piso cerámico, cielo raso y acústica básica", "m²", 420, 950.0),
            _p("Cocina de servicio, SS.HH. y depósito", "m²", 50, 1400.0),
            _p("Mobiliario, sonido e iluminación decorativa", "glb", 1, 30000.0),
            _p("Patio de ingreso afirmado", "m²", 300, 40.0),
            _p("Expediente, licencias, ITSE previa y aforo", "glb", 1, 18000.0)],
            (1.5 * 800.0, 2.5 * 1200.0, 4 * 1500.0), opex_fijo=4000 + 5800 + 2500 + 4000 + 6000, opex_var=0.20,
            impuesto=0.10, rampa=(0.6, 0.85), vida=40)],
        "alto", "media", "alta (agenda, limpieza, vecinos)",
        ["Aforo de 280-420 personas: ITSE previa, dos salidas y una dotación de estacionamiento (15-40 plazas) que "
         "probablemente no cabe en el lote. Compite con locales comunales."]),
    Opcion(
        "K", "Terminal o paradero de vans y colectivos", "Terminal de vans",
        "Patio de maniobras de concreto, andenes techados, 4 boleterías, sala de espera y SS.HH.",
        [Fase("Terminal de vans", 0, [
            _p("Pavimento de concreto para patio de maniobras", "m²", 480, 130.0),
            _p("Techado metálico de andenes", "m²", 150, 400.0),
            _p("Sala de espera, 4 boleterías y SS.HH.", "m²", 120, 1300.0),
            _p("Cerco, portones y señalización", "glb", 1, 20000.0),
            _p("Estudio de impacto vial, habilitación técnica MTC y licencias (Modalidad D)", "glb", 1, 25000.0)],
            # boleterías + cobro por salida (salidas por día × S/ por salida × 30)
            (4 * 400 + 12 * 3 * 30.0, 4 * 600 + 20 * 4 * 30.0, 4 * 800 + 28 * 5 * 30.0),
            opex_fijo=GUARDIAN + 6000 + 4000 + 3500 + 2000 + 2500 + rb.NRUS_MES * 12, impuesto=0.03,
            rampa=(0.6, 0.85), vida=40)],
        "alto", "media", "alta (autorizaciones, empresas de transporte)",
        ["4 empresas autorizadas en la ruta a Chachapoyas y sin terminal formal, pero exige habilitación técnica del "
         "MTC, estudio vial y congestiona la vía principal."]),
    Opcion(
        "H", "Hostal de 16 habitaciones (3 pisos)", "Hostal",
        "Edificio de 3 pisos con 16 habitaciones con baño y recepción.",
        [Fase("Hostal", 0, [
            _p("Edificio de 3 pisos para hostal (750 m² techados)", "m²", 750, 1700.0),
            _p("Equipamiento de habitaciones y recepción", "und", 16, 6000.0),
            _p("Expediente, licencia (Modalidad D) y categorización MINCETUR", "glb", 1, 30000.0)],
            (16 * 65 * 30.0, 16 * 75 * 30.0, 16 * 85 * 30.0), ocupacion=(0.25, 0.35, 0.45),
            opex_fijo=3 * GUARDIAN + 14000 + 15400 + 4000 + 12000 + 3000, opex_var=0.25, impuesto=0.15,
            rampa=(0.5, 0.8), vida=50)],
        "alto", "media", "muy alta (operación 24 h)",
        ["El 94 % de los visitantes de la provincia son de la misma provincia y el 91 % se aloja con familiares; "
         "la ocupación de hospedajes en Amazonas ronda el 20-23 %. El IGV reducido de hospedaje vuelve a 18 % en 2028."]),
]

OPC = {o.clave: o for o in OPCIONES}


# --------------------------------------------------------------------------
# Flujo de caja y métricas
# --------------------------------------------------------------------------
def flujo(op: Opcion, esc=1, tasa_crec=CRECIMIENTO):
    """Filas por año 0..HORIZONTE con inversión, ingresos, gastos, impuestos, reposiciones y valor residual."""
    filas = []
    acum = acum_sr = 0.0
    for t in range(HORIZONTE + 1):
        inv = ing = opx = imp = rep = res = 0.0
        crec = (1 + tasa_crec) ** max(t - 1, 0)
        for f in op.fases:
            if t == f.anio:
                inv -= f.capex_nominal(esc)
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
                res += f.capex_nominal(esc) * max(0.0, 1 - (HORIZONTE - f.anio) / f.vida)
        neto = inv + ing + opx + imp + rep + res
        acum += neto
        acum_sr += neto - res
        filas.append(dict(anio=t, inversion=inv, ingresos=ing, opex=opx, impuestos=imp, reposiciones=rep,
                          residual=res, neto=neto, acum=acum, acum_sr=acum_sr))
    return filas


def recuperacion(filas):
    """Años para recuperar la inversión con la caja acumulada SIN valor residual; None si no ocurre en el horizonte."""
    if filas[0]["acum_sr"] >= 0 and all(f["inversion"] == 0 for f in filas):
        return 0.0
    for a, b in zip(filas, filas[1:]):
        if a["acum_sr"] < 0 <= b["acum_sr"]:
            paso = b["neto"] - b["residual"]
            return a["anio"] + (-a["acum_sr"]) / paso if paso > 0 else None
    return None


def tir_con_terreno(netos, terreno, plusvalia):
    """TIR del propietario contando el terreno como capital: lo «aporta» hoy a valor de mercado y lo
    recupera valorizado en el año 20. Se compara con vender y depositar."""
    f = list(netos)
    f[0] -= terreno
    f[-1] += terreno * (1 + plusvalia) ** HORIZONTE
    return rb.tir(f)


def terreno(esc=1):
    return AREA_LOTE * VALOR_M2[esc]


def metricas(op: Opcion, esc=1):
    fl = flujo(op, esc)
    netos = [f["neto"] for f in fl]
    capex = sum(f.capex_nominal(esc) for f in op.fases)
    neto_reg = sum(f.neto_regimen(esc) for f in op.fases)
    t0 = terreno(esc)
    presente = sum(f["neto"] - f["inversion"] for f in fl[1:4]) / 3     # caja promedio de los años 1-3 (sin inversiones)
    construido = sum(f.capex_nominal(esc) * max(0.0, 1 - (HORIZONTE - f.anio) / f.vida) for f in op.fases if f.vida > 1)
    van_sr = rb.van([f["neto"] - f["residual"] for f in fl], TASA)
    return dict(
        clave=op.clave, nombre=op.nombre, corto=op.corto, capex=capex,
        capex_inicial=sum(f.capex(esc) for f in op.fases if f.anio == 0),
        neto_regimen=neto_reg, neto_mes=neto_reg / 12, presente=presente,
        anio_regimen=max(f.anio_regimen() for f in op.fases),
        van=rb.van(netos, TASA), van_sin_residual=van_sr,
        tir=rb.tir(netos) if capex > 0 else None, payback=recuperacion(fl) if capex > 0 else 0.0,
        tir_terreno=tir_con_terreno(netos, t0, PLUSVALIA[esc]),
        valor20=t0 * (1 + PLUSVALIA[esc]) ** HORIZONTE + construido, flujo=fl)


def deposito_neto():
    return DEPOSITO * (1 - IMP_INTERES)


def venta_terreno(esc=1):
    precio = terreno(esc)
    renta = precio * deposito_neto()
    return dict(precio=precio, renta_anual=renta, renta_mes=renta / 12)


def _opcion_de(fases, clave="X"):
    return Opcion(clave, clave, clave, "", fases, "", "", "")


def umbral_ingreso(op: Opcion, fase_idx: int, esc=1, ocupacion=None, rampa=None):
    """Ingreso mensual potencial de una fase que hace VAN(fase sola) = 0 al 10 % (bisección).
    Con `ocupacion`/`rampa` se evalúa, por ejemplo, un contrato firmado (ocupación 0.95)."""
    fase = copy.deepcopy(op.fases[fase_idx])
    if ocupacion is not None:
        fase.ocupacion = (ocupacion,) * 3
    if rampa is not None:
        fase.rampa = rampa
    solo = _opcion_de([fase])

    def van_con(x):
        ing = list(fase.ingreso)
        ing[esc] = x
        fase.ingreso = tuple(ing)
        return rb.van([f["neto"] for f in flujo(solo, esc)], TASA)

    lo, hi = 0.0, max(fase.ingreso) * 8 + 5000
    for _ in range(90):
        mid = (lo + hi) / 2
        if van_con(mid) < 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def umbrales(esc=1):
    """Ingresos a partir de los cuales cada decisión paga el 10 % anual (escenario base)."""
    C, E, D, A, F = OPC["C"], OPC["E"], OPC["D"], OPC["A"], OPC["F"]
    e_rb = rb.ESCENARIOS[1]
    tickets_motos = e_rb.tickets_dia * e_rb.ticket_prom * 30 + e_rb.motos * e_rb.tarifa_moto
    return dict(
        esquina_mercado=umbral_ingreso(C, 0, esc),                                       # S/ al mes con 80 % de ocupación
        esquina_contrato=umbral_ingreso(C, 0, esc, ocupacion=0.95, rampa=(0.9, 1.0)),   # contrato firmado
        locales_m2=umbral_ingreso(C, 1, esc) / 134.7,
        locales_m2_contrato=umbral_ingreso(C, 1, esc, ocupacion=0.95, rampa=(0.9, 1.0)) / 134.7,
        cochera_abonados=umbral_ingreso(C, 2, esc) / 75.0,
        consultorio=umbral_ingreso(E, 3, esc) / 7,
        minidepto=umbral_ingreso(D, 3, esc) / 8,
        cancha_horas=umbral_ingreso(F, 0, esc) / 30 / 50,
        abonados_A=(umbral_ingreso(A, 0, esc) - tickets_motos) / e_rb.tarifa_mensual,
    )


def arriendo_equivalente(clave, esc=1):
    """Renta mensual del lote completo (J) que iguala el VAN de la alternativa `clave`."""
    objetivo = metricas(OPC[clave], esc)["van"]
    j = copy.deepcopy(OPC["J"])
    lo, hi = 0.0, 20000.0
    for _ in range(80):
        mid = (lo + hi) / 2
        ing = list(j.fases[0].ingreso)
        ing[esc] = mid
        j.fases[0].ingreso = tuple(ing)
        if metricas(j, esc)["van"] < objetivo:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def tasacion_equilibrio(clave, esc=1):
    """Valor del terreno (S/ por m²) a partir del cual vender y depositar rinde más que la alternativa."""
    netos = [f["neto"] for f in flujo(OPC[clave], esc)]
    lo, hi = 50.0, 5000.0
    for _ in range(80):
        mid = (lo + hi) / 2
        t = tir_con_terreno(netos, AREA_LOTE * mid, PLUSVALIA[esc])
        if t is not None and t > deposito_neto():
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def sensibilidad_locales(rentas=tuple(range(10, 31))):
    """VAN de C y de sus 3 locales del jirón según la renta de esos locales (S/ por m² al mes), escenario base."""
    out = []
    for r in rentas:
        op = copy.deepcopy(OPC["C"])
        ing = list(op.fases[1].ingreso)
        ing[1] = 134.7 * r
        op.fases[1].ingreso = tuple(ing)
        out.append((r, metricas(op, 1)["van"], metricas(_opcion_de([op.fases[1]]), 1)["van"]))
    return out


def orden(esc=1):
    """Alternativas ordenadas por VAN en el escenario dado."""
    return sorted(OPC, key=lambda k: -metricas(OPC[k], esc)["van"])


ORDEN = orden(1)


def tabla_comparativa(esc=1):
    return [metricas(OPC[k], esc) for k in ORDEN]


# --------------------------------------------------------------------------
# Fuentes y validación en campo (resumen de la investigación, oct-2026)
# --------------------------------------------------------------------------
FUENTES = [
    ("Población", "Ciudad de Mendoza: 5,130 hab. (Censo 2017) y 3,356 en 2007; provincia: 29,998 hab. (2017); "
     "la provincia creció 1.3 % anual entre 2017 y 2025 (Censos 2025). Estimado 2026: 6,100-6,700 hab. en la ciudad.",
     "INEI (citypopulation.de); INEI, nota de prensa de los Censos 2025", "2017 / 2026", "media"),
    ("Eje comercial", "Agencia del Banco de la Nación en Jr. Toribio Rodríguez de Mendoza N.º 309: el jirón es el eje "
     "comercial e institucional.", "Banco de la Nación (ubicador de agencias)", "2025", "alta"),
    ("Hospital", "Nuevo local del Hospital María Auxiliadora II-1 (CUI 2195952, «Mejoramiento»): reemplaza al hospital "
     "que ya funciona en San Nicolás, con 26-54 camas; 96 % de avance hacia ago-2026, apertura probable en 2027; "
     "ubicación del nuevo sitio por verificar.", "MEF (DS 016-2017-EF), Contraloría, GORE Amazonas, prensa local",
     "2026", "media"),
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
    ("Alquiler de locales (Mendoza)", "Estimado: S/ 12-18 por m² al mes para locales de 40-50 m² en el jirón y "
     "S/ 10-20 para un local de 100 m² sin contrato (la renta por m² baja con el tamaño). Bagua Grande: S/ 600 por "
     "un local de 1.er piso. Sin avisos publicados en Mendoza.", "Estimación por comparables", "oct-2026", "baja"),
    ("Cuartos y departamentos", "Chachapoyas: cuarto con baño S/ 380-480; departamento de 2 dormitorios S/ 1,100-1,400. "
     "Estimado para Mendoza: minidepartamento S/ 400-650.", "Avisos; estimación por comparables", "oct-2026", "baja"),
    ("Valor del terreno", "Chachapoyas: lote céntrico de 204 m² a ≈ S/ 955 por m² (precio pedido); tasación en Huambo "
     "(misma provincia) ≈ S/ 680 por m² en 2019. Los lotes grandes se venden 20-40 % más baratos por m²: estimado "
     "para el lote S/ 400-850 por m².", "Avisos; tasación REPEV", "2019-2026", "baja"),
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
    ("Depósitos a plazo", "Cajas municipales 5.2-7.1 % TEA en 2026; el Fondo de Seguro de Depósitos cubre ≈ S/ 120 mil "
     "por entidad; intereses de personas naturales exonerados del impuesto a la renta (verificar vigencia).",
     "Andina; SBS; LIR art. 19", "2026", "media"),
    ("Estacionamientos exigidos", "La A.070 exige estacionamiento dentro del lote para comercio; sin PDU la cantidad la "
     "fija el certificado de parámetros (≈ 5-6 plazas para 235 m² de locales, más 1 accesible).",
     "RNE A.070 (RM 060-2021-VIVIENDA)", "2021", "media"),
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
     "retiros o ensanche del jirón y estacionamientos exigidos a los locales (decide cuántas plazas quedan para "
     "abonados y si caben 3 pisos)."),
    ("Abonados de cochera",
     "Antes de habilitar la cochera, inscribir al menos 10-12 abonados con 3 meses pagados por adelantado."),
    ("Ubicación del nuevo local del hospital y su personal adicional",
     "Es un reemplazo del hospital actual: averiguar en la DIRESA o en la obra (CUI 2195952) dónde queda, cuándo abre "
     "y cuánto personal nuevo llega. Si queda lejos, las boticas y consultorios se moverán hacia allá."),
    ("Interés por arrendar el lote o la esquina",
     "Ofrecer el lote completo y la esquina (derecho de superficie o build-to-suit) a ferreterías, concesionarios de "
     "motos, empresas de transporte, cajas, farmacias y cooperativas antes de construir: una oferta seria cambia la "
     "decisión."),
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
        ("Valor del terreno (S/ por m²) - pesimista", VALOR_M2[0], soles, "vm1"),
        ("Valor del terreno (S/ por m²) - base (requiere tasación)", VALOR_M2[1], soles, "vm2"),
        ("Valor del terreno (S/ por m²) - optimista", VALOR_M2[2], soles, "vm3"),
        ("Valorización anual del terreno - pesimista", PLUSVALIA[0], pct, "pl1"),
        ("Valorización anual del terreno - base", PLUSVALIA[1], pct, "pl2"),
        ("Valorización anual del terreno - optimista", PLUSVALIA[2], pct, "pl3"),
        ("Rendimiento de un depósito a plazo (alternativa a vender)", DEPOSITO, pct, "dep"),
        ("Impuesto a los intereses del depósito (exonerado para personas naturales; verificar)", IMP_INTERES, pct, "impint"),
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
    ws.cell(r, 1, "Valor del terreno del escenario elegido (S/)").font = negrita
    caja(ws.cell(r, 2, f"={R['area']}*CHOOSE({R['esc']},{R['vm1']},{R['vm2']},{R['vm3']})"), verde, soles, True)
    R["terreno"] = f"Supuestos!$B${r}"
    ws.cell(r + 1, 1, "Factor de costo del escenario elegido")
    caja(ws.cell(r + 1, 2, f"=CHOOSE({R['esc']},{R['fc1']},{R['fc2']},{R['fc3']})"), verde, "0.00")
    R["fc"] = f"Supuestos!$B${r + 1}"
    ws.cell(r + 2, 1, "Valorización del terreno del escenario elegido")
    caja(ws.cell(r + 2, 2, f"=CHOOSE({R['esc']},{R['pl1']},{R['pl2']},{R['pl3']})"), verde, pct)
    R["plusv"] = f"Supuestos!$B${r + 2}"
    ws.cell(r + 3, 1, "Depósito neto de impuestos")
    caja(ws.cell(r + 3, 2, f"={R['dep']}*(1-{R['impint']})"), verde, pct)
    R["depn"] = f"Supuestos!$B${r + 3}"
    ws.cell(r + 5, 1, "Cómo usar: cambie el escenario o cualquier celda amarilla (aquí o en cada hoja de alternativa); "
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
                    capn = f"{ref['cap']}*(1+{R['crec']})^MAX({ref['anio']}-1,0)"
                    if c == "Inversión":
                        fx = f"=IF({A}={ref['anio']},-{capn},0)"
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
                        fx = (f"=IF(AND({A}={HORIZONTE},{ref['vida']}>1),{capn}*MAX(0,1-({HORIZONTE}-{ref['anio']})/{ref['vida']}),0)")
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
        sh.cell(fila, 1, "Caja acumulada (sin valor residual)").font = negrita
        for t in anios:
            col = L(col0 + t)
            res_t = f"-{col}{filas_tot['Valor residual (año 20)']}"
            fx = f"={col}{f_neto}{res_t}" if t == 0 else f"={L(col0 + t - 1)}{fila}+{col}{f_neto}{res_t}"
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
            ("TIR", f'=IFERROR(IRR({rng}),IFERROR(IRR({rng},-0.05),"no aplica"))', pct),
            ("Año en que se recupera la inversión (acumulado ≥ 0)",
             f'=IF(-SUM({L(col0)}{filas_tot["Inversión"]}:{L(col0 + HORIZONTE)}{filas_tot["Inversión"]})=0,"sin inversión",IFERROR(INDEX({L(col0)}{fila_anio}:{L(col0 + HORIZONTE)}{fila_anio},MATCH(TRUE,INDEX({L(col0)}{f_acum}:{L(col0 + HORIZONTE)}{f_acum}>=0,0),0)),"no en 20 años"))', "0"),
            ("Caja neta del año 5 sin inversiones (S/ nominales)", f"={L(col0 + 5)}{f_neto}-{L(col0 + 5)}{filas_tot['Inversión']}", soles),
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
           "Caja neta año 5", "Rinde sobre (terreno + inversión)", "TIR contando el terreno", "Riesgo", "Futuro",
           "Gestión", "Capital"]
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
        caja(wc.cell(r, 7, f"={kpi[k]['Caja neta del año 5 sin inversiones (S/ nominales)']}"), None, soles)
        caja(wc.cell(r, 8, f"=G{r}/((1+{R['crec']})^4)/(C{r}+{R['terreno']})"), None, pct)
        wc.cell(r, 13, op.capital)
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
    caja(wc.cell(r, 7, f"={R['terreno']}*{R['depn']}"), verde, soles, True)
    caja(wc.cell(r, 8, f"={R['depn']}"), None, pct)
    caja(wc.cell(r, 9, f"={R['depn']}"), None, pct)
    wc.cell(r + 2, 2, "Orden: por VAN en el escenario base. «Rinde sobre (terreno + inversión)» compara la caja del año 5 (a precios de hoy) con "
                      "todo el capital comprometido, incluido el valor del terreno. «TIR contando el terreno» trata el "
                      "lote como si se aportara hoy a valor de mercado y se recuperara valorizado en el año 20: si es "
                      "menor que vender y depositar (fila de referencia), la alternativa no paga el terreno.").alignment = Alignment(wrap_text=True)
    wc.merge_cells(start_row=r + 2, start_column=2, end_row=r + 2, end_column=12)
    wc.row_dimensions[r + 2].height = 58
    for col, w in zip("ABCDEFGHIJKLM", (5, 50, 14, 14, 9, 13, 14, 14, 12, 10, 34, 24, 12)):
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
        print(f"{'Alt':4}{'Inversión':>12}{'Neto/mes':>10}{'Presente':>11}{'VAN':>12}{'TIR':>8}{'Recup.':>8}{'TIR+T':>8}")
        for m in tabla_comparativa(esc):
            tir = f"{m['tir'] * 100:6.1f}%" if m["tir"] is not None else "   n.a."
            pb = f"{m['payback']:6.1f}" if m["payback"] is not None else "   no"
            tt = f"{m['tir_terreno'] * 100:6.1f}%" if m["tir_terreno"] is not None else "   n.a."
            print(f"{m['clave']:4}{m['capex']:12,.0f}{m['neto_mes']:10,.0f}{m['presente']:11,.0f}{m['van']:12,.0f}{tir:>8}{pb:>8}"
                  f"{tt:>8}  {m['corto']}")
        v = venta_terreno(esc)
        print(f"Venta del terreno: S/ {v['precio']:,.0f} -> depositado rinde S/ {v['renta_mes']:,.0f} al mes")
    print("\nUmbrales (VAN = 0 al 10 %):", {k: round(v, 1) for k, v in umbrales().items()})
    print("Tasación a partir de la cual conviene vender (S/ por m²):", {k: round(tasacion_equilibrio(k)) for k in ("L", "J", "C1")})
    if len(sys.argv) > 1:
        exportar_xlsx(sys.argv[1])
        print("xlsx:", sys.argv[1])
