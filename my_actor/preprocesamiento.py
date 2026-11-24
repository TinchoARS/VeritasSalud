from __future__ import annotations

import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

from my_actor.errores import ValorInvalido
from my_actor.esquema import ESQUEMA, Campo, Derivada, Esquema, Proporcion, TipoCampo
from my_actor.normalizacion import (
    convertir_categoria,
    convertir_codigo,
    convertir_entero,
    convertir_numero,
    es_vacio,
    normalizar_texto,
)

type Valor = float | str | None

CONVERSORES: dict[TipoCampo, Callable[[object, Campo], float | str]] = {
    TipoCampo.NUMERO: lambda valor, _campo: convertir_numero(valor),
    TipoCampo.ENTERO: lambda valor, _campo: convertir_entero(valor),
    TipoCampo.CODIGO: lambda valor, campo: convertir_codigo(valor, campo.opciones),
    TipoCampo.CATEGORIA: lambda valor, campo: convertir_categoria(valor, campo.opciones),
}


@dataclass(frozen=True)
class ErrorDeCampo:
    campo: str
    motivo: str


@dataclass(frozen=True)
class RespuestaProcesada:
    valores: dict[str, Valor]
    errores: tuple[ErrorDeCampo, ...]

    @property
    def es_valida(self) -> bool:
        return not self.errores


def preprocesar_respuestas(respuestas: Mapping[str, object], esquema: Esquema = ESQUEMA) -> RespuestaProcesada:
    unificadas = unificar_claves(respuestas, esquema.campos)
    valores: dict[str, Valor] = {}
    errores: list[ErrorDeCampo] = []
    for campo in esquema.campos:
        try:
            valores[campo.clave] = resolver_valor(campo, unificadas)
        except ValorInvalido as error:
            errores.append(ErrorDeCampo(campo.clave, str(error)))
    errores.extend(validar_proporciones(valores, esquema.proporciones))
    return RespuestaProcesada(valores, tuple(errores))


def unificar_claves(respuestas: Mapping[str, object], campos: Sequence[Campo]) -> dict[str, object]:
    clave_por_pregunta = {
        normalizar_texto(nombre): campo.clave for campo in campos for nombre in campo.nombres_aceptados
    }
    unificadas: dict[str, object] = {}
    for pregunta, valor in respuestas.items():
        clave = clave_por_pregunta.get(normalizar_texto(pregunta))
        if clave is not None and clave not in unificadas and not es_vacio(valor):
            unificadas[clave] = valor
    return unificadas


def resolver_valor(campo: Campo, unificadas: Mapping[str, object]) -> Valor:
    if campo.clave in unificadas:
        return convertir_valor(unificadas[campo.clave], campo)
    if campo.obligatorio:
        raise ValorInvalido('obligatorio sin respuesta')
    return None


def convertir_valor(valor: object, campo: Campo) -> float | str:
    convertido = CONVERSORES[campo.tipo](valor, campo)
    if isinstance(convertido, str):
        return convertido
    validar_rango(convertido, campo)
    return campo.recodificacion.get(convertido, convertido)


def validar_rango(valor: float, campo: Campo) -> None:
    if campo.minimo is not None and valor < campo.minimo:
        raise ValorInvalido(f'menor que el mínimo permitido ({campo.minimo:g})')
    if campo.maximo is not None and valor > campo.maximo:
        raise ValorInvalido(f'mayor que el máximo permitido ({campo.maximo:g})')


def validar_proporciones(valores: Mapping[str, Valor], proporciones: Sequence[Proporcion]) -> list[ErrorDeCampo]:
    return [
        ErrorDeCampo(proporcion.parte, f'no puede superar a {proporcion.total}')
        for proporcion in proporciones
        if supera_al_total(valores, proporcion)
    ]


def supera_al_total(valores: Mapping[str, Valor], proporcion: Proporcion) -> bool:
    parte, total = valores.get(proporcion.parte), valores.get(proporcion.total)
    return parte is not None and total is not None and parte > total


def calcular_proporcion(valores: Mapping[str, Valor], proporcion: Proporcion) -> float | None:
    parte, total = valores.get(proporcion.parte), valores.get(proporcion.total)
    if parte is None or not total:
        return None
    return parte / total


def calcular_derivada(valores: Mapping[str, Valor], derivada: Derivada) -> int | None:
    return derivada.valor_por_origen.get(valores.get(derivada.origen))


def a_features(valores: Mapping[str, Valor], esquema: Esquema = ESQUEMA) -> dict[str, float | str]:
    features: dict[str, Valor] = {clave: valores[clave] for clave in esquema.claves_directas}
    features.update({derivada.clave: calcular_derivada(valores, derivada) for derivada in esquema.derivadas})
    features.update({proporcion.clave: calcular_proporcion(valores, proporcion) for proporcion in esquema.proporciones})
    return {clave: math.nan if valor is None else valor for clave, valor in features.items()}
