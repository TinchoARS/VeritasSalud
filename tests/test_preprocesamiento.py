import math

import pytest

from my_actor.esquema import (
    AGLOMERADOS,
    CODIGOS_AGLOMERADO,
    ESQUEMA,
    Campo,
    Derivada,
    Esquema,
    Proporcion,
    TipoCampo,
)
from my_actor.normalizacion import normalizar_texto
from my_actor.preprocesamiento import ErrorDeCampo, a_features, preprocesar_respuestas, unificar_claves
from my_actor.salidas import describir_ubicacion
from tests.conftest import CAMPOS_DE_PRUEBA, ESQUEMA_DE_PRUEBA, FEATURES_DE_PRUEBA

ESQUEMA_CON_PROPORCION = Esquema(
    (
        Campo('edad', TipoCampo.ENTERO),
        Campo('ocupados', TipoCampo.ENTERO, obligatorio=False, minimo=1),
        Campo('miembros', TipoCampo.ENTERO, obligatorio=False, minimo=1),
    ),
    (Proporcion('ratio', parte='ocupados', total='miembros'),),
)

ESQUEMA_CON_DERIVADA = Esquema(
    (Campo('ciudad', TipoCampo.CODIGO, opciones={'norte': 1, 'sur': 2}, recodificacion={2: 9}),),
    derivadas=(Derivada('nivel', origen='ciudad', valor_por_origen={1: 5, 9: 3}),),
)

FORMULARIO_REAL_COMPLETO = {
    'Cobertura de salud': 'Obra social',
    'Edad': '27',
    'Nivel educativo': 'Universitario completo',
    '¿Tu empleo está registrado?': 'Sí',
    'Sexo': 'Mujer',
    '¿Cuántas personas trabajan junto a usted en su ocupación principal?': 'De 6 a 40',
    '¿Cuántas horas trabajaste la semana pasada en tu ocupación principal?': '40',
    '¿Qué calificación tiene tu ocupación?': 'Técnica',
    'Ciudad': 'Gran Rosario',
    '¿Alquilás la vivienda donde vivís?': 'Sí',
}


def test_unificar_claves_mapea_preguntas_del_formulario_a_claves_internas() -> None:
    unificadas = unificar_claves({'EDAD (AÑOS)': '30', 'nivel educativo': 'primario', 'Marca temporal': 'x'}, CAMPOS_DE_PRUEBA)
    assert unificadas == {'edad': '30', 'nivel': 'primario'}


def test_unificar_claves_ignora_respuestas_vacias_y_conserva_la_primera_con_valor() -> None:
    unificadas = unificar_claves({'edad': '', 'Edad (años)': '41'}, CAMPOS_DE_PRUEBA)
    assert unificadas == {'edad': '41'}


def test_preprocesar_respuestas_convierte_y_deja_opcionales_sin_valor(respuestas_validas: dict[str, object]) -> None:
    procesada = preprocesar_respuestas(respuestas_validas, ESQUEMA_DE_PRUEBA)
    assert procesada.es_valida
    assert procesada.valores == {'edad': 34, 'nivel': 3, 'ingreso': 450000.5, 'region': None}


def test_preprocesar_respuestas_junta_todos_los_errores_sin_exponer_valores() -> None:
    procesada = preprocesar_respuestas(
        {'Edad (años)': '200', 'Nivel educativo': 'doctorado', 'Región': '5'}, ESQUEMA_DE_PRUEBA
    )
    assert not procesada.es_valida
    assert procesada.errores == (
        ErrorDeCampo('edad', 'mayor que el máximo permitido (100)'),
        ErrorDeCampo('nivel', 'opción no reconocida'),
        ErrorDeCampo('ingreso', 'obligatorio sin respuesta'),
        ErrorDeCampo('region', 'mayor que el máximo permitido (2)'),
    )
    assert all('doctorado' not in error.motivo and '200' not in error.motivo for error in procesada.errores)


def test_a_features_respeta_el_orden_y_convierte_faltantes_en_nan(respuestas_validas: dict[str, object]) -> None:
    features = a_features(preprocesar_respuestas(respuestas_validas, ESQUEMA_DE_PRUEBA).valores, ESQUEMA_DE_PRUEBA)
    assert tuple(features) == FEATURES_DE_PRUEBA
    assert features['edad'] == 34
    assert math.isnan(features['region'])


def test_la_proporcion_reemplaza_a_sus_campos_en_las_features() -> None:
    procesada = preprocesar_respuestas({'edad': 30, 'ocupados': 1, 'miembros': 4}, ESQUEMA_CON_PROPORCION)
    assert ESQUEMA_CON_PROPORCION.features == ('edad', 'ratio')
    assert a_features(procesada.valores, ESQUEMA_CON_PROPORCION) == {'edad': 30, 'ratio': 0.25}


def test_la_proporcion_sin_alguna_de_sus_partes_queda_en_nan() -> None:
    procesada = preprocesar_respuestas({'edad': 30, 'ocupados': 1}, ESQUEMA_CON_PROPORCION)
    assert procesada.es_valida
    assert math.isnan(a_features(procesada.valores, ESQUEMA_CON_PROPORCION)['ratio'])


def test_la_parte_no_puede_superar_al_total() -> None:
    procesada = preprocesar_respuestas({'edad': 30, 'ocupados': 5, 'miembros': 3}, ESQUEMA_CON_PROPORCION)
    assert procesada.errores == (ErrorDeCampo('ocupados', 'no puede superar a miembros'),)


def test_el_esquema_real_genera_las_features_del_modelo_entrenado_en_su_orden() -> None:
    assert ESQUEMA.features == (
        'cobertura_salud',
        'edad',
        'nivel_educativo',
        'formalidad_empleo',
        'sexo',
        'tamano_establecimiento',
        'horas_trabajo',
        'calificacion_ocupacion',
        'AGLOMERADO',
        'inquilino',
    )


def test_el_esquema_real_arma_la_fila_del_modelo_desde_el_formulario() -> None:
    procesada = preprocesar_respuestas(FORMULARIO_REAL_COMPLETO)
    assert procesada.es_valida
    assert a_features(procesada.valores) == {
        'cobertura_salud': 'obra_social',
        'edad': 27,
        'nivel_educativo': 6,
        'formalidad_empleo': 1,
        'sexo': 2,
        'tamano_establecimiento': 2,
        'horas_trabajo': 40.0,
        'calificacion_ocupacion': 3,
        'AGLOMERADO': 4,
        'inquilino': 1,
    }


@pytest.mark.parametrize(
    ('respuestas', 'esperado'),
    [
        ({'Cobertura de salud': 'PAMI'}, {'cobertura_salud': 'obra_social'}),
        ({'cobertura_salud': 'sin_cobertura'}, {'cobertura_salud': 'sin_cobertura'}),
        ({'¿Qué cobertura de salud tenés?': 'No tengo'}, {'cobertura_salud': 'sin_cobertura'}),
        ({'¿Tu empleo está registrado?': 'Sí'}, {'formalidad_empleo': 1}),
        ({'Formalidad del empleo': 'En negro'}, {'formalidad_empleo': 2}),
        ({'Nivel educativo': 'Universitario completo'}, {'nivel_educativo': 6}),
        ({'Nivel educativo': 'Superior y universitario incompleto'}, {'nivel_educativo': 5}),
        ({'Nivel educativo': 'Primario incompleto (incluye educación especial)'}, {'nivel_educativo': 1}),
        ({'Sexo': 'Varón'}, {'sexo': 1}),
        ({'¿Cuál es tu sexo?': 'MUJER'}, {'sexo': 2}),
        ({'sexo': '1'}, {'sexo': 1}),
        ({'¿Cuántas personas trabajan junto a usted en su ocupación principal?': 'Hasta 5'}, {'tamano_establecimiento': 1}),
        ({'Tamaño del establecimiento': 'de 6 a 40 personas'}, {'tamano_establecimiento': 2}),
        ({'tamano_establecimiento': 'Más de 40'}, {'tamano_establecimiento': 3}),
        ({'¿Cuántas horas trabajaste la semana pasada en tu ocupación principal?': '37,5'}, {'horas_trabajo': 37.5}),
        ({'Horas de trabajo': '45'}, {'horas_trabajo': 45.0}),
        ({'¿Qué calificación tiene tu ocupación?': 'Profesional'}, {'calificacion_ocupacion': 4}),
        ({'calificacion_ocupacion': 'Técnico'}, {'calificacion_ocupacion': 3}),
        ({'calificacion_ocupacion': 'Operario'}, {'calificacion_ocupacion': 2}),
        ({'calificacion_ocupacion': 'No calificada'}, {'calificacion_ocupacion': 1}),
        ({'¿Alquilás la vivienda donde vivís?': 'Sí'}, {'inquilino': 1}),
        ({'Inquilino': 'No'}, {'inquilino': 0}),
        ({'inquilino': '0'}, {'inquilino': 0}),
    ],
)
def test_el_esquema_real_traduce_respuestas_a_codigos_eph(respuestas: dict[str, object], esperado: dict[str, object]) -> None:
    valores = preprocesar_respuestas(respuestas).valores
    assert {clave: valores[clave] for clave in esperado} == esperado


def test_el_esquema_real_junta_los_errores_de_todo_el_formulario() -> None:
    formulario = {
        **FORMULARIO_REAL_COMPLETO,
        'Cobertura de salud': 'Seguro privado',
        'Sexo': 'Otro',
        '¿Qué calificación tiene tu ocupación?': 'Gerente',
    }
    errores = preprocesar_respuestas(formulario).errores
    assert errores == (
        ErrorDeCampo('cobertura_salud', 'opción no reconocida'),
        ErrorDeCampo('sexo', 'opción no reconocida'),
        ErrorDeCampo('calificacion_ocupacion', 'opción no reconocida'),
    )


@pytest.mark.parametrize(
    ('horas', 'motivo'),
    [('0', 'menor que el mínimo permitido (1)'), ('169', 'mayor que el máximo permitido (168)')],
)
def test_las_horas_no_pueden_superar_las_de_una_semana(horas: str, motivo: str) -> None:
    pregunta = '¿Cuántas horas trabajaste la semana pasada en tu ocupación principal?'
    errores = preprocesar_respuestas({**FORMULARIO_REAL_COMPLETO, pregunta: horas}).errores
    assert errores == (ErrorDeCampo('horas_trabajo', motivo),)


@pytest.mark.parametrize('valor', ['Inquilino', '2', 'Tal vez'])
def test_inquilino_solo_acepta_si_o_no(valor: str) -> None:
    errores = preprocesar_respuestas({**FORMULARIO_REAL_COMPLETO, '¿Alquilás la vivienda donde vivís?': valor}).errores
    assert errores == (ErrorDeCampo('inquilino', 'opción no reconocida'),)


@pytest.mark.parametrize('valor', ['0', '9', '25'])
def test_el_tamano_del_establecimiento_solo_acepta_los_tres_tramos(valor: str) -> None:
    pregunta = '¿Cuántas personas trabajan junto a usted en su ocupación principal?'
    errores = preprocesar_respuestas({**FORMULARIO_REAL_COMPLETO, pregunta: valor}).errores
    assert errores == (ErrorDeCampo('tamano_establecimiento', 'opción no reconocida'),)


@pytest.mark.parametrize(
    ('respuestas', 'codigo'),
    [
        ({'Región': 'Capital Federal'}, 32),
        ({'Ciudad': 'conurbano'}, 33),
        ({'¿En qué ciudad vivís?': 'San Miguel de Tucumán'}, 29),
        ({'aglomerado': 'agl_04_gran_rosario'}, 4),
        ({'aglomerado': 'RIO GRANDE'}, 31),
        ({'aglomerado': '93'}, 93),
        ({'aglomerado': 13}, 13),
    ],
)
def test_el_aglomerado_se_reconoce_por_nombre_alias_columna_o_codigo(respuestas: dict[str, object], codigo: int) -> None:
    assert preprocesar_respuestas(respuestas).valores['AGLOMERADO'] == codigo


@pytest.mark.parametrize('valor', ['Buenos Aires', 'Atlántida', '11'])
def test_el_aglomerado_desconocido_es_un_error(valor: str) -> None:
    errores = preprocesar_respuestas({**FORMULARIO_REAL_COMPLETO, 'Ciudad': valor}).errores
    assert errores == (ErrorDeCampo('AGLOMERADO', 'opción no reconocida'),)


def test_el_aglomerado_es_obligatorio_porque_lo_usa_el_modelo() -> None:
    sin_ciudad = {pregunta: valor for pregunta, valor in FORMULARIO_REAL_COMPLETO.items() if pregunta != 'Ciudad'}
    assert preprocesar_respuestas(sin_ciudad).errores == (ErrorDeCampo('AGLOMERADO', 'obligatorio sin respuesta'),)
    assert 'AGLOMERADO' in ESQUEMA.features


@pytest.mark.parametrize(
    ('edad', 'motivo'),
    [('17', 'menor que el mínimo permitido (18)'), ('31', 'mayor que el máximo permitido (30)')],
)
def test_la_edad_queda_en_la_franja_del_entrenamiento(edad: str, motivo: str) -> None:
    errores = preprocesar_respuestas({**FORMULARIO_REAL_COMPLETO, 'Edad': edad}).errores
    assert errores == (ErrorDeCampo('edad', motivo),)


@pytest.mark.parametrize(
    ('ciudad', 'esperado'),
    [('Norte', {'ciudad': 1, 'nivel': 5}), ('2', {'ciudad': 9, 'nivel': 3})],
)
def test_la_derivada_y_la_recodificacion_arman_features_desde_otro_campo(ciudad: str, esperado: dict[str, int]) -> None:
    procesada = preprocesar_respuestas({'ciudad': ciudad}, ESQUEMA_CON_DERIVADA)
    assert ESQUEMA_CON_DERIVADA.features == ('ciudad', 'nivel')
    assert a_features(procesada.valores, ESQUEMA_CON_DERIVADA) == esperado


def test_la_derivada_sin_origen_queda_en_nan() -> None:
    esquema = Esquema(
        (Campo('ciudad', TipoCampo.CODIGO, obligatorio=False, opciones={'norte': 1}),),
        derivadas=(Derivada('nivel', origen='ciudad', valor_por_origen={1: 5}),),
    )
    assert math.isnan(a_features(preprocesar_respuestas({}, esquema).valores, esquema)['nivel'])


def test_las_etiquetas_de_aglomerado_no_se_pisan_al_normalizarlas() -> None:
    normalizadas = [normalizar_texto(etiqueta) for etiqueta in CODIGOS_AGLOMERADO]
    assert len(normalizadas) == len(set(normalizadas))
    assert len(AGLOMERADOS) == 32


def test_describir_ubicacion_devuelve_codigo_nombre_y_region() -> None:
    assert describir_ubicacion(91) == {'aglomerado': 91, 'aglomerado_nombre': 'Rawson - Trelew', 'region': 'Patagonia'}
    assert describir_ubicacion(None) == {'aglomerado': None, 'aglomerado_nombre': None, 'region': None}
