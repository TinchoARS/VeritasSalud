from __future__ import annotations

import json

import pytest

from my_actor.entrada import MAXIMO_FORMULARIOS_POR_EJECUCION, Formulario, leer_formularios
from my_actor.errores import EntradaInvalida


def test_leer_formularios_devuelve_un_formulario_por_respuesta() -> None:
    formularios = leer_formularios({'formularios': [{'id_respuesta': 7, 'respuestas': {'Edad': '30'}}]})
    assert formularios == [Formulario(id_respuesta='7', respuestas={'Edad': '30'})]


def test_leer_formularios_acepta_respuestas_como_json_en_texto() -> None:
    texto = json.dumps({'Edad': '30'})
    formularios = leer_formularios({'formularios': [{'id_respuesta': 'a', 'respuestas': texto}]})
    assert formularios[0].respuestas == {'Edad': '30'}


@pytest.mark.parametrize(
    'datos_entrada',
    [
        None,
        [],
        {},
        {'formularios': []},
        {'formularios': 'no-es-lista'},
        {'formularios': ['no-es-objeto']},
        {'formularios': [{'respuestas': {}}]},
        {'formularios': [{'id_respuesta': '  ', 'respuestas': {}}]},
        {'formularios': [{'id_respuesta': True, 'respuestas': {}}]},
        {'formularios': [{'id_respuesta': 'a'}]},
        {'formularios': [{'id_respuesta': 'a', 'respuestas': '{no es json'}]},
        {'formularios': [{'id_respuesta': 'a', 'respuestas': [1, 2]}]},
    ],
)
def test_leer_formularios_rechaza_input_mal_formado(datos_entrada: object) -> None:
    with pytest.raises(EntradaInvalida):
        leer_formularios(datos_entrada)


def test_leer_formularios_limita_la_cantidad_por_ejecucion() -> None:
    formularios = [{'id_respuesta': str(numero), 'respuestas': {}} for numero in range(MAXIMO_FORMULARIOS_POR_EJECUCION + 1)]
    with pytest.raises(EntradaInvalida):
        leer_formularios({'formularios': formularios})
