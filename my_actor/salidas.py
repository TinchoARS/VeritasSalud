from __future__ import annotations

from collections.abc import Mapping, Sequence

from my_actor.esquema import AGLOMERADO_POR_CODIGO, CLASES_DE_INGRESO, INGRESO_MINIMO, LIMITES_DE_INGRESO
from my_actor.preprocesamiento import ErrorDeCampo

ESTADO_OK = 'ok'
ESTADO_INVALIDO = 'invalido'
SIN_UBICACION: Mapping[str, object] = {'aglomerado': None, 'aglomerado_nombre': None, 'region': None}
BORDES_DE_CLASE: tuple[int | None, ...] = (INGRESO_MINIMO, *LIMITES_DE_INGRESO, None)


def armar_resultado(
    id_respuesta: str, clase_ingreso: int, ubicacion: Mapping[str, object], version_modelo: str
) -> dict[str, object]:
    ingreso_desde, ingreso_hasta = rango_de_ingreso(clase_ingreso)
    return {
        'id_respuesta': id_respuesta,
        'estado': ESTADO_OK,
        'clase_ingreso': clase_ingreso,
        'ingreso_desde': ingreso_desde,
        'ingreso_hasta': ingreso_hasta,
        **ubicacion,
        'errores': [],
        'version_modelo': version_modelo,
    }


def armar_rechazo(
    id_respuesta: str, errores: Sequence[ErrorDeCampo], ubicacion: Mapping[str, object], version_modelo: str
) -> dict[str, object]:
    return {
        'id_respuesta': id_respuesta,
        'estado': ESTADO_INVALIDO,
        'clase_ingreso': None,
        'ingreso_desde': None,
        'ingreso_hasta': None,
        **ubicacion,
        'errores': [{'campo': error.campo, 'motivo': error.motivo} for error in errores],
        'version_modelo': version_modelo,
    }


def rango_de_ingreso(clase_ingreso: int) -> tuple[int | None, int | None]:
    posicion = CLASES_DE_INGRESO.index(clase_ingreso)
    return BORDES_DE_CLASE[posicion], BORDES_DE_CLASE[posicion + 1]


def describir_ubicacion(codigo_aglomerado: object) -> dict[str, object]:
    aglomerado = AGLOMERADO_POR_CODIGO.get(codigo_aglomerado)
    if aglomerado is None:
        return dict(SIN_UBICACION)
    return {'aglomerado': aglomerado.codigo, 'aglomerado_nombre': aglomerado.nombre, 'region': aglomerado.region}


def resumir(resultados: Sequence[dict[str, object]]) -> dict[str, object]:
    validos = sum(resultado['estado'] == ESTADO_OK for resultado in resultados)
    return {
        'total': len(resultados),
        'validos': validos,
        'invalidos': len(resultados) - validos,
        'version_modelo': resultados[0]['version_modelo'] if resultados else None,
    }
