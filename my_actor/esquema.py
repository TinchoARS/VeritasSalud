from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum


class TipoCampo(Enum):
    NUMERO = 'numero'
    ENTERO = 'entero'
    CODIGO = 'codigo'
    CATEGORIA = 'categoria'


@dataclass(frozen=True)
class Campo:
    clave: str
    tipo: TipoCampo
    alias: tuple[str, ...] = ()
    obligatorio: bool = True
    opciones: Mapping[str, int | str] = field(default_factory=dict, hash=False)
    minimo: float | None = None
    maximo: float | None = None
    recodificacion: Mapping[int, int] = field(default_factory=dict, hash=False)

    @property
    def nombres_aceptados(self) -> tuple[str, ...]:
        return (self.clave, *self.alias)


@dataclass(frozen=True)
class Proporcion:
    clave: str
    parte: str
    total: str


@dataclass(frozen=True)
class Derivada:
    clave: str
    origen: str
    valor_por_origen: Mapping[int, int] = field(hash=False)


@dataclass(frozen=True)
class Esquema:
    campos: tuple[Campo, ...]
    proporciones: tuple[Proporcion, ...] = ()
    derivadas: tuple[Derivada, ...] = ()

    @property
    def claves_directas(self) -> tuple[str, ...]:
        usadas = {clave for proporcion in self.proporciones for clave in (proporcion.parte, proporcion.total)}
        return tuple(campo.clave for campo in self.campos if campo.clave not in usadas)

    @property
    def features(self) -> tuple[str, ...]:
        return (
            *self.claves_directas,
            *(derivada.clave for derivada in self.derivadas),
            *(proporcion.clave for proporcion in self.proporciones),
        )


CATEGORIAS_COBERTURA_SALUD = {
    'obra social': 'obra_social',
    'pami': 'obra_social',
    'prepaga': 'prepaga',
    'mutual': 'prepaga',
    'prepaga o mutual': 'prepaga',
    'sin cobertura': 'sin_cobertura',
    'ninguna': 'sin_cobertura',
    'no tengo': 'sin_cobertura',
    'solo hospital publico': 'sin_cobertura',
}

CODIGOS_NIVEL_EDUCATIVO = {
    'primario incompleto': 1,
    'primario incompleto (incluye educación especial)': 1,
    'educación especial': 1,
    'primario completo': 2,
    'secundario incompleto': 3,
    'secundario completo': 4,
    'superior y universitario incompleto': 5,
    'superior universitario incompleto': 5,
    'universitario incompleto': 5,
    'terciario incompleto': 5,
    'superior y universitario completo': 6,
    'superior universitario completo': 6,
    'universitario completo': 6,
    'terciario completo': 6,
    'sin instruccion': 7,
    'sin estudios': 7,
}

CODIGOS_FORMALIDAD_EMPLEO = {
    'registrado': 1,
    'formal': 1,
    'en blanco': 1,
    'con aportes': 1,
    'si': 1,
    'no registrado': 2,
    'informal': 2,
    'en negro': 2,
    'sin aportes': 2,
    'no': 2,
}

CODIGOS_SEXO = {
    'varon': 1,
    'hombre': 1,
    'masculino': 1,
    'mujer': 2,
    'femenino': 2,
}

CODIGOS_TAMANO_ESTABLECIMIENTO = {
    'hasta 5': 1,
    'hasta 5 personas': 1,
    'de 6 a 40': 2,
    'de 6 a 40 personas': 2,
    'mas de 40': 3,
    'mas de 40 personas': 3,
}

CODIGOS_CALIFICACION_OCUPACION = {
    'no calificada': 1,
    'profesion no calificada': 1,
    'ocupacion no calificada': 1,
    'operario': 2,
    'operativa': 2,
    'tecnico': 3,
    'tecnica': 3,
    'profesional': 4,
}

CODIGOS_INQUILINO = {
    'si': 1,
    'no': 0,
}

HORAS_MINIMAS = 1
HORAS_POR_SEMANA = 168


@dataclass(frozen=True)
class Aglomerado:
    codigo: int
    nombre: str
    region: str
    nivel_region: int
    columna_de_planes: str
    alias: tuple[str, ...] = ()

    @property
    def etiquetas(self) -> tuple[str, ...]:
        return (self.nombre, self.columna_de_planes, *self.alias)


AGLOMERADOS: tuple[Aglomerado, ...] = (
    Aglomerado(2, 'Gran La Plata', 'Pampeana', 2, 'agl_02_gran_la_plata', ('La Plata',)),
    Aglomerado(3, 'Bahía Blanca - Cerri', 'Pampeana', 5, 'agl_03_bahia_blanca_cerri', ('Bahía Blanca', 'Cerri')),
    Aglomerado(4, 'Gran Rosario', 'Pampeana', 5, 'agl_04_gran_rosario', ('Rosario',)),
    Aglomerado(5, 'Gran Santa Fe', 'Pampeana', 5, 'agl_05_gran_santa_fe', ('Santa Fe', 'Ciudad de Santa Fe')),
    Aglomerado(6, 'Gran Paraná', 'Pampeana', 4, 'agl_06_gran_parana', ('Paraná',)),
    Aglomerado(7, 'Posadas', 'NEA', 1, 'agl_07_posadas'),
    Aglomerado(8, 'Gran Resistencia', 'NEA', 2, 'agl_08_gran_resistencia', ('Resistencia',)),
    Aglomerado(
        9,
        'Comodoro Rivadavia - Rada Tilly',
        'Patagonia',
        4,
        'agl_09_comodoro_rivadavia',
        ('Comodoro Rivadavia', 'Comodoro', 'Rada Tilly'),
    ),
    Aglomerado(10, 'Gran Mendoza', 'Cuyo', 1, 'agl_10_gran_mendoza', ('Mendoza',)),
    Aglomerado(12, 'Corrientes', 'NEA', 2, 'agl_12_corrientes'),
    Aglomerado(13, 'Gran Córdoba', 'Pampeana', 5, 'agl_13_gran_cordoba', ('Córdoba', 'Ciudad de Córdoba')),
    Aglomerado(14, 'Concordia', 'Pampeana', 1, 'agl_14_concordia'),
    Aglomerado(15, 'Formosa', 'NEA', 1, 'agl_15_formosa'),
    Aglomerado(17, 'Neuquén - Plottier', 'Patagonia', 5, 'agl_17_neuquen_plottier', ('Neuquén', 'Plottier')),
    Aglomerado(
        18,
        'Santiago del Estero - La Banda',
        'NOA',
        2,
        'agl_18_santiago_del_estero',
        ('Santiago del Estero', 'La Banda'),
    ),
    Aglomerado(19, 'Jujuy - Palpalá', 'NOA', 2, 'agl_19_jujuy_palpala', ('Jujuy', 'San Salvador de Jujuy', 'Palpalá')),
    Aglomerado(20, 'Río Gallegos', 'Patagonia', 5, 'agl_20_rio_gallegos'),
    Aglomerado(
        22, 'Gran Catamarca', 'NOA', 1, 'agl_22_gran_catamarca', ('Catamarca', 'San Fernando del Valle de Catamarca')
    ),
    Aglomerado(23, 'Gran Salta', 'NOA', 1, 'agl_23_gran_salta', ('Salta',)),
    Aglomerado(25, 'La Rioja', 'NOA', 2, 'agl_25_la_rioja'),
    Aglomerado(26, 'Gran San Luis', 'Cuyo', 3, 'agl_26_gran_san_luis', ('San Luis',)),
    Aglomerado(27, 'Gran San Juan', 'Cuyo', 1, 'agl_27_gran_san_juan', ('San Juan',)),
    Aglomerado(
        29,
        'Gran Tucumán - Tafí Viejo',
        'NOA',
        1,
        'agl_29_gran_tucuman',
        ('Tucumán', 'San Miguel de Tucumán', 'Tafí Viejo'),
    ),
    Aglomerado(30, 'Santa Rosa - Toay', 'Pampeana', 4, 'agl_30_santa_rosa_toay', ('Santa Rosa', 'Toay')),
    Aglomerado(31, 'Ushuaia - Río Grande', 'Patagonia', 5, 'agl_31_ushuaia_rio_grande', ('Ushuaia', 'Río Grande')),
    Aglomerado(
        32,
        'Ciudad Autónoma de Buenos Aires',
        'GBA',
        5,
        'agl_32_caba',
        ('CABA', 'Capital Federal', 'Ciudad de Buenos Aires'),
    ),
    Aglomerado(
        33,
        'Partidos del GBA',
        'GBA',
        3,
        'agl_33_gba_partidos',
        ('GBA', 'Gran Buenos Aires', 'Conurbano', 'Conurbano bonaerense'),
    ),
    Aglomerado(34, 'Mar del Plata', 'Pampeana', 4, 'agl_34_mar_del_plata', ('Mar del Plata - Batán',)),
    Aglomerado(36, 'Río Cuarto', 'Pampeana', 5, 'agl_36_rio_cuarto'),
    Aglomerado(
        38,
        'San Nicolás - Villa Constitución',
        'Pampeana',
        4,
        'agl_38_san_nicolas_villa_constitucion',
        ('San Nicolás', 'Villa Constitución'),
    ),
    Aglomerado(91, 'Rawson - Trelew', 'Patagonia', 5, 'agl_91_rawson_trelew', ('Rawson', 'Trelew')),
    Aglomerado(
        93,
        'Viedma - Carmen de Patagones',
        'Patagonia',
        4,
        'agl_93_viedma_carmen_de_patagones',
        ('Viedma', 'Carmen de Patagones'),
    ),
)

AGLOMERADO_POR_CODIGO = {aglomerado.codigo: aglomerado for aglomerado in AGLOMERADOS}
CODIGOS_AGLOMERADO = {etiqueta: aglomerado.codigo for aglomerado in AGLOMERADOS for etiqueta in aglomerado.etiquetas}
CLAVE_AGLOMERADO = 'AGLOMERADO'
CLASES_DE_INGRESO = (1, 2, 3)
INGRESO_MINIMO = 0
LIMITES_DE_INGRESO = (600_000, 1_200_000)
EDAD_MINIMA = 18
EDAD_MAXIMA = 30

CAMPOS: tuple[Campo, ...] = (
    Campo(
        'cobertura_salud',
        TipoCampo.CATEGORIA,
        alias=('Cobertura de salud', '¿Qué cobertura de salud tenés?'),
        opciones=CATEGORIAS_COBERTURA_SALUD,
    ),
    Campo('edad', TipoCampo.ENTERO, alias=('Edad', '¿Cuántos años tenés?'), minimo=EDAD_MINIMA, maximo=EDAD_MAXIMA),
    Campo(
        'nivel_educativo',
        TipoCampo.CODIGO,
        alias=('Nivel educativo', '¿Cuál es tu máximo nivel educativo alcanzado?'),
        opciones=CODIGOS_NIVEL_EDUCATIVO,
    ),
    Campo(
        'formalidad_empleo',
        TipoCampo.CODIGO,
        alias=('Formalidad del empleo', '¿Tu empleo está registrado?', '¿Te hacen aportes jubilatorios?'),
        opciones=CODIGOS_FORMALIDAD_EMPLEO,
    ),
    Campo('sexo', TipoCampo.CODIGO, alias=('Sexo', '¿Cuál es tu sexo?'), opciones=CODIGOS_SEXO),
    Campo(
        'tamano_establecimiento',
        TipoCampo.CODIGO,
        alias=(
            'Tamaño del establecimiento',
            '¿Cuántas personas trabajan junto a usted en su ocupación principal?',
            '¿Cuántas personas trabajan en tu lugar de trabajo?',
        ),
        opciones=CODIGOS_TAMANO_ESTABLECIMIENTO,
    ),
    Campo(
        'horas_trabajo',
        TipoCampo.NUMERO,
        alias=(
            'Horas de trabajo',
            '¿Cuántas horas trabajaste la semana pasada en tu ocupación principal?',
            '¿Cuántas horas por semana trabajás?',
        ),
        minimo=HORAS_MINIMAS,
        maximo=HORAS_POR_SEMANA,
    ),
    Campo(
        'calificacion_ocupacion',
        TipoCampo.CODIGO,
        alias=('Calificación de la ocupación', '¿Qué calificación tiene tu ocupación?'),
        opciones=CODIGOS_CALIFICACION_OCUPACION,
    ),
    Campo(
        CLAVE_AGLOMERADO,
        TipoCampo.CODIGO,
        alias=('Región', 'Ciudad', '¿En qué ciudad vivís?', '¿En qué región vivís?'),
        opciones=CODIGOS_AGLOMERADO,
    ),
    Campo(
        'inquilino',
        TipoCampo.CODIGO,
        alias=('Inquilino', '¿Alquilás la vivienda donde vivís?', '¿Sos inquilino?'),
        opciones=CODIGOS_INQUILINO,
    ),
)

ESQUEMA = Esquema(CAMPOS)
