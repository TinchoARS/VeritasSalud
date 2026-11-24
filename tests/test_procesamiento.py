import pytest

from my_actor.errores import EntradaInvalida
from my_actor.modelo import ModeloCargado
from my_actor.procesamiento import procesar
from my_actor.salidas import ESTADO_INVALIDO, ESTADO_OK, rango_de_ingreso, resumir
from tests.conftest import ESQUEMA_DE_PRUEBA


def test_procesar_devuelve_un_resultado_por_formulario_en_el_mismo_orden(
    input_de_make: dict[str, object], modelo_de_prueba: ModeloCargado
) -> None:
    resultados = procesar(input_de_make, modelo_de_prueba, ESQUEMA_DE_PRUEBA)
    assert [resultado['id_respuesta'] for resultado in resultados] == ['fila-2', 'fila-3']
    assert [resultado['estado'] for resultado in resultados] == [ESTADO_OK, ESTADO_INVALIDO]


def test_procesar_predice_los_validos_y_explica_los_invalidos(
    input_de_make: dict[str, object], modelo_de_prueba: ModeloCargado
) -> None:
    valido, invalido = procesar(input_de_make, modelo_de_prueba, ESQUEMA_DE_PRUEBA)
    assert valido['clase_ingreso'] in {1, 3}
    assert (valido['ingreso_desde'], valido['ingreso_hasta']) == rango_de_ingreso(valido['clase_ingreso'])
    assert valido['version_modelo'] == 'prueba-1'
    assert invalido['clase_ingreso'] is invalido['ingreso_desde'] is invalido['ingreso_hasta'] is None
    assert {error['campo'] for error in invalido['errores']} == {'edad', 'nivel', 'ingreso'}


def test_procesar_no_publica_datos_personales(input_de_make: dict[str, object], modelo_de_prueba: ModeloCargado) -> None:
    resultados = procesar(input_de_make, modelo_de_prueba, ESQUEMA_DE_PRUEBA)
    assert 'Ana' not in str(resultados)
    assert list(resultados[0]) == [
        'id_respuesta',
        'estado',
        'clase_ingreso',
        'ingreso_desde',
        'ingreso_hasta',
        'aglomerado',
        'aglomerado_nombre',
        'region',
        'errores',
        'version_modelo',
    ]


def test_procesar_sin_formularios_validos_no_llama_al_modelo(modelo_de_prueba: ModeloCargado) -> None:
    resultados = procesar({'formularios': [{'id_respuesta': 'x', 'respuestas': {}}]}, modelo_de_prueba, ESQUEMA_DE_PRUEBA)
    assert resultados[0]['estado'] == ESTADO_INVALIDO


def test_procesar_propaga_input_mal_formado(modelo_de_prueba: ModeloCargado) -> None:
    with pytest.raises(EntradaInvalida):
        procesar({'otra_cosa': 1}, modelo_de_prueba, ESQUEMA_DE_PRUEBA)


def test_resumir_cuenta_validos_e_invalidos(input_de_make: dict[str, object], modelo_de_prueba: ModeloCargado) -> None:
    resumen = resumir(procesar(input_de_make, modelo_de_prueba, ESQUEMA_DE_PRUEBA))
    assert resumen == {'total': 2, 'validos': 1, 'invalidos': 1, 'version_modelo': 'prueba-1'}


@pytest.mark.parametrize(
    ('clase_ingreso', 'esperado'), [(1, (0, 600_000)), (2, (600_000, 1_200_000)), (3, (1_200_000, None))]
)
def test_rango_de_ingreso_traduce_la_clase_a_su_tramo_en_pesos(
    clase_ingreso: int, esperado: tuple[int, int | None]
) -> None:
    assert rango_de_ingreso(clase_ingreso) == esperado
