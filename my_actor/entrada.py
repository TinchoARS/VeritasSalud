import json
from collections.abc import Mapping
from dataclasses import dataclass

from my_actor.errores import EntradaInvalida

MAXIMO_FORMULARIOS_POR_EJECUCION = 1000


@dataclass(frozen=True)
class Formulario:
    id_respuesta: str
    respuestas: dict[str, object]


def leer_formularios(datos_entrada: object) -> list[Formulario]:
    if not isinstance(datos_entrada, Mapping):
        raise EntradaInvalida('El input debe ser un objeto JSON')
    formularios = datos_entrada.get('formularios')
    if not isinstance(formularios, list) or not formularios:
        raise EntradaInvalida("'formularios' debe ser una lista con al menos un formulario")
    if len(formularios) > MAXIMO_FORMULARIOS_POR_EJECUCION:
        raise EntradaInvalida(f"'formularios' admite hasta {MAXIMO_FORMULARIOS_POR_EJECUCION} elementos")
    return [leer_formulario(formulario, posicion) for posicion, formulario in enumerate(formularios)]


def leer_formulario(formulario: object, posicion: int) -> Formulario:
    if not isinstance(formulario, Mapping):
        raise EntradaInvalida(f'formularios[{posicion}] debe ser un objeto')
    return Formulario(
        id_respuesta=leer_id_respuesta(formulario.get('id_respuesta'), posicion),
        respuestas=leer_respuestas(formulario.get('respuestas'), posicion),
    )


def leer_id_respuesta(id_respuesta: object, posicion: int) -> str:
    if isinstance(id_respuesta, bool) or not isinstance(id_respuesta, str | int) or not str(id_respuesta).strip():
        raise EntradaInvalida(f'formularios[{posicion}].id_respuesta es obligatorio (texto o número)')
    return str(id_respuesta).strip()


def leer_respuestas(respuestas: object, posicion: int) -> dict[str, object]:
    if isinstance(respuestas, str):
        respuestas = decodificar_json(respuestas, posicion)
    if not isinstance(respuestas, Mapping):
        raise EntradaInvalida(f'formularios[{posicion}].respuestas debe ser un objeto con las respuestas del formulario')
    return {str(pregunta): valor for pregunta, valor in respuestas.items()}


def decodificar_json(texto: str, posicion: int) -> object:
    try:
        return json.loads(texto)
    except json.JSONDecodeError as error:
        raise EntradaInvalida(f'formularios[{posicion}].respuestas no es un JSON válido') from error
