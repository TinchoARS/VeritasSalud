from collections.abc import Iterator

from my_actor.entrada import leer_formularios
from my_actor.esquema import CLAVE_AGLOMERADO, ESQUEMA, Esquema
from my_actor.modelo import ModeloCargado, predecir
from my_actor.preprocesamiento import RespuestaProcesada, a_features, preprocesar_respuestas
from my_actor.salidas import armar_rechazo, armar_resultado, describir_ubicacion


def procesar(datos_entrada: object, modelo: ModeloCargado, esquema: Esquema = ESQUEMA) -> list[dict[str, object]]:
    formularios = leer_formularios(datos_entrada)
    procesadas = [preprocesar_respuestas(formulario.respuestas, esquema) for formulario in formularios]
    filas_validas = [a_features(procesada.valores, esquema) for procesada in procesadas if procesada.es_valida]
    clases = iter(predecir(modelo, filas_validas) if filas_validas else [])
    return [
        armar_salida(formulario.id_respuesta, procesada, clases, modelo.version)
        for formulario, procesada in zip(formularios, procesadas)
    ]


def armar_salida(
    id_respuesta: str, procesada: RespuestaProcesada, clases: Iterator[int], version_modelo: str
) -> dict[str, object]:
    ubicacion = describir_ubicacion(procesada.valores.get(CLAVE_AGLOMERADO))
    if procesada.es_valida:
        return armar_resultado(id_respuesta, next(clases), ubicacion, version_modelo)
    return armar_rechazo(id_respuesta, procesada.errores, ubicacion, version_modelo)
