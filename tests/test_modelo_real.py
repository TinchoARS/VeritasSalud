from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from my_actor.esquema import (
    CLASES_DE_INGRESO,
    CODIGOS_CALIFICACION_OCUPACION,
    CODIGOS_INQUILINO,
    CODIGOS_SEXO,
    CODIGOS_TAMANO_ESTABLECIMIENTO,
    EDAD_MAXIMA,
    EDAD_MINIMA,
    LIMITES_DE_INGRESO,
)
from my_actor.modelo import ModeloCargado, cargar_modelo, predecir
from my_actor.procesamiento import procesar

PERFIL_DE_INGRESO_ALTO = {
    'Cobertura de salud': 'Prepaga',
    'Edad': '29',
    'Nivel educativo': 'Universitario completo',
    '¿Tu empleo está registrado?': 'Sí',
    'Sexo': 'Varón',
    '¿Cuántas personas trabajan junto a usted en su ocupación principal?': 'Más de 40',
    '¿Cuántas horas trabajaste la semana pasada en tu ocupación principal?': '48',
    '¿Qué calificación tiene tu ocupación?': 'Profesional',
    '¿En qué ciudad vivís?': 'Capital Federal',
    '¿Alquilás la vivienda donde vivís?': 'No',
}

PERFIL_DE_INGRESO_BAJO = {
    'cobertura_salud': 'Sin cobertura',
    'edad': 19,
    'nivel_educativo': 'Secundario incompleto',
    'formalidad_empleo': 'No registrado',
    'sexo': 'Mujer',
    'tamano_establecimiento': 'Hasta 5',
    'horas_trabajo': 10,
    'calificacion_ocupacion': 'No calificada',
    'aglomerado': 'Resistencia',
    'inquilino': 'Sí',
}

MUESTRA_DE_ENTRENAMIENTO = Path(__file__).parent / 'datos' / 'muestra_eph_nuevo.csv'
TAMANO = 'tamano_establecimiento'
TAMANO_SIN_RESPUESTA_EN_LA_EPH = 0
PRIMERA_CLASE_DEL_NOTEBOOK = 1
CAMPOS_CON_CODIGO = {
    'sexo': CODIGOS_SEXO,
    TAMANO: CODIGOS_TAMANO_ESTABLECIMIENTO,
    'calificacion_ocupacion': CODIGOS_CALIFICACION_OCUPACION,
    'inquilino': CODIGOS_INQUILINO,
}


def leer_muestra_de_entrenamiento() -> pd.DataFrame:
    return pd.read_csv(MUESTRA_DE_ENTRENAMIENTO)


def etiqueta_del_codigo(codigos: dict[str, int], codigo: int) -> str:
    return next(etiqueta for etiqueta, valor in codigos.items() if valor == codigo)


def fila_a_formulario(fila: pd.Series, tamano_si_no_respondio: int) -> dict[str, object]:
    respuestas = fila.to_dict()
    if int(fila[TAMANO]) == TAMANO_SIN_RESPUESTA_EN_LA_EPH:
        respuestas[TAMANO] = tamano_si_no_respondio
    for campo, codigos in CAMPOS_CON_CODIGO.items():
        respuestas[campo] = etiqueta_del_codigo(codigos, int(respuestas[campo]))
    return respuestas


def predecir_muestra(modelo_real: ModeloCargado, tamano_si_no_respondio: int) -> list[dict[str, object]]:
    muestra = leer_muestra_de_entrenamiento()
    formularios = [
        {'id_respuesta': str(indice), 'respuestas': fila_a_formulario(fila, tamano_si_no_respondio)}
        for indice, fila in muestra.iterrows()
    ]
    return procesar({'formularios': formularios}, modelo_real)


@pytest.fixture(scope='module')
def modelo_real() -> ModeloCargado:
    return cargar_modelo()


def test_el_modelo_del_repositorio_carga_y_coincide_con_el_esquema(modelo_real: ModeloCargado) -> None:
    assert len(modelo_real.features) == 10
    assert modelo_real.cortes is not None and len(modelo_real.cortes) == len(CLASES_DE_INGRESO) - 1


def test_el_modelo_real_ordena_perfiles_opuestos_en_clases_extremas(modelo_real: ModeloCargado) -> None:
    entrada = {
        'formularios': [
            {'id_respuesta': 'alto', 'respuestas': PERFIL_DE_INGRESO_ALTO},
            {'id_respuesta': 'bajo', 'respuestas': PERFIL_DE_INGRESO_BAJO},
        ]
    }
    alto, bajo = procesar(entrada, modelo_real)
    assert (alto['clase_ingreso'], alto['ingreso_desde'], alto['ingreso_hasta']) == (3, 1_200_000, None)
    assert (bajo['clase_ingreso'], bajo['ingreso_desde'], bajo['ingreso_hasta']) == (1, 0, 600_000)
    assert all(type(resultado['clase_ingreso']) is int for resultado in (alto, bajo))
    assert (alto['aglomerado'], alto['aglomerado_nombre'], alto['region']) == (32, 'Ciudad Autónoma de Buenos Aires', 'GBA')
    assert (bajo['aglomerado'], bajo['aglomerado_nombre'], bajo['region']) == (8, 'Gran Resistencia', 'NEA')


@pytest.mark.parametrize('tamano_si_no_respondio', [1, 2, 3])
def test_el_preprocesamiento_reproduce_las_filas_de_la_muestra(
    modelo_real: ModeloCargado, tamano_si_no_respondio: int
) -> None:
    muestra = leer_muestra_de_entrenamiento()
    esperadas = predecir(modelo_real, muestra[list(modelo_real.features)].to_dict('records'))
    resultados = predecir_muestra(modelo_real, tamano_si_no_respondio)
    assert all(resultado['estado'] == 'ok' for resultado in resultados)
    assert [resultado['clase_ingreso'] for resultado in resultados] == esperadas
    assert set(esperadas) == set(CLASES_DE_INGRESO)


def a_clase_como_el_notebook(modelo_real: ModeloCargado, muestra: pd.DataFrame) -> list[int]:
    logaritmo_del_ingreso = modelo_real.estimador.predict(muestra[list(modelo_real.features)])
    return (np.digitize(logaritmo_del_ingreso, modelo_real.cortes) + PRIMERA_CLASE_DEL_NOTEBOOK).tolist()


def test_la_clase_sale_de_los_cortes_del_pickle_aplicados_al_logaritmo_predicho(modelo_real: ModeloCargado) -> None:
    resultados = predecir_muestra(modelo_real, CODIGOS_TAMANO_ESTABLECIMIENTO['hasta 5'])
    esperadas = a_clase_como_el_notebook(modelo_real, leer_muestra_de_entrenamiento())
    assert [resultado['clase_ingreso'] for resultado in resultados] == esperadas


def test_los_cortes_del_pickle_estan_en_la_escala_del_logaritmo_del_ingreso(modelo_real: ModeloCargado) -> None:
    corte_inferior, corte_superior = np.expm1(modelo_real.cortes)
    limite_inferior, limite_superior = LIMITES_DE_INGRESO
    assert corte_inferior < limite_inferior
    assert corte_superior == pytest.approx(limite_superior, abs=1)


def test_el_tamano_del_establecimiento_no_cambia_la_prediccion(modelo_real: ModeloCargado) -> None:
    filas = leer_muestra_de_entrenamiento()[list(modelo_real.features)].to_dict('records')
    predicciones_por_tamano = [
        predecir(modelo_real, [fila | {TAMANO: tamano} for fila in filas]) for tamano in (0, *CODIGOS_TAMANO_ESTABLECIMIENTO.values())
    ]
    assert all(prediccion == predicciones_por_tamano[0] for prediccion in predicciones_por_tamano)


def test_la_muestra_cubre_las_coberturas_y_la_franja_de_edad_del_entrenamiento() -> None:
    muestra = leer_muestra_de_entrenamiento()
    assert set(muestra['cobertura_salud']) == {'obra_social', 'prepaga', 'sin_cobertura'}
    assert muestra['edad'].between(EDAD_MINIMA, EDAD_MAXIMA).all()
