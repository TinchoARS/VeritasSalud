import hashlib
import pickle
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn._loss import _loss as perdidas_compiladas_de_sklearn

from my_actor.errores import ModeloInvalido
from my_actor.esquema import CLASES_DE_INGRESO, ESQUEMA

MODELO_PATH = Path(__file__).resolve().parent.parent / 'modelos' / 'modelo.pkl'
CARACTERES_HASH_VERSION = 12
MODULOS_PERMITIDOS = ('sklearn.', 'numpy', 'scipy.', 'collections', 'copyreg')
BUILTINS_PERMITIDOS = frozenset({'slice', 'set', 'frozenset', 'complex', 'bytearray'})
MODULO_COMPILADO_DE_PERDIDAS = '_loss'
PREFIJO_DE_PERDIDAS_COMPILADAS = 'Cy'
CANTIDAD_DE_CORTES = len(CLASES_DE_INGRESO) - 1


@dataclass(frozen=True)
class ModeloCargado:
    estimador: Any
    features: tuple[str, ...]
    version: str
    cortes: tuple[float, ...] | None = None


@dataclass(frozen=True)
class ContenidoDelPickle:
    estimador: Any
    features: Sequence[str] | None
    version: str | None
    cortes: object | None


class LectorDeModelo(pickle.Unpickler):
    def find_class(self, modulo: str, nombre: str) -> Any:
        if modulo == 'builtins' and nombre in BUILTINS_PERMITIDOS:
            return super().find_class(modulo, nombre)
        if modulo.startswith(MODULOS_PERMITIDOS):
            return super().find_class(modulo, nombre)
        if modulo == MODULO_COMPILADO_DE_PERDIDAS and nombre.startswith(PREFIJO_DE_PERDIDAS_COMPILADAS):
            return getattr(perdidas_compiladas_de_sklearn, nombre)
        raise pickle.UnpicklingError(f'{modulo}.{nombre} no está permitido en el pickle del modelo')


def cargar_modelo(ruta: Path = MODELO_PATH, features_esperadas: Sequence[str] | None = None) -> ModeloCargado:
    if not ruta.is_file():
        raise ModeloInvalido(f'No se encontró el modelo en modelos/{ruta.name}')
    contenido = desempaquetar(leer_pickle(ruta))
    estimador = validar_estimador(contenido.estimador)
    return ModeloCargado(
        estimador=estimador,
        features=validar_features(estimador, contenido.features, features_esperadas or ESQUEMA.features),
        version=contenido.version or hash_de_archivo(ruta),
        cortes=validar_salida(estimador, contenido.cortes),
    )


def leer_pickle(ruta: Path) -> object:
    try:
        with ruta.open('rb') as archivo:
            return LectorDeModelo(archivo).load()
    except Exception as error:
        raise ModeloInvalido(f'No se pudo leer el pickle: {type(error).__name__}: {error}') from error


def desempaquetar(contenido: object) -> ContenidoDelPickle:
    if isinstance(contenido, Mapping):
        version = contenido.get('version')
        return ContenidoDelPickle(
            estimador=contenido.get('modelo'),
            features=contenido.get('features'),
            version=None if version is None else str(version),
            cortes=contenido.get('cortes'),
        )
    return ContenidoDelPickle(contenido, getattr(contenido, 'feature_names_in_', None), None, None)


def validar_estimador(estimador: Any) -> Any:
    if not callable(getattr(estimador, 'predict', None)):
        raise ModeloInvalido('El pickle no contiene un estimador con predict()')
    return estimador


def validar_salida(estimador: Any, cortes: object | None) -> tuple[float, ...] | None:
    if cortes is None:
        validar_clases(estimador)
        return None
    return validar_cortes(cortes)


def validar_clases(estimador: Any) -> None:
    clases = getattr(estimador, 'classes_', None)
    if clases is not None and not {a_valor_nativo(clase) for clase in clases} <= set(CLASES_DE_INGRESO):
        raise ModeloInvalido(f'El modelo debe predecir las clases de ingreso {CLASES_DE_INGRESO}')


def validar_cortes(cortes: object) -> tuple[float, ...]:
    try:
        valores = tuple(float(corte) for corte in cortes)
    except (TypeError, ValueError) as error:
        raise ModeloInvalido('Los cortes del modelo deben ser números') from error
    if len(valores) != CANTIDAD_DE_CORTES or list(valores) != sorted(set(valores)):
        raise ModeloInvalido(f'El modelo debe traer {CANTIDAD_DE_CORTES} cortes crecientes')
    return valores


def validar_features(
    estimador: Any, features_declaradas: Sequence[str] | None, features_esperadas: Sequence[str]
) -> tuple[str, ...]:
    if features_declaradas is None:
        return validar_cantidad_de_features(estimador, tuple(features_esperadas))
    declaradas = tuple(str(feature) for feature in features_declaradas)
    faltantes = sorted(set(declaradas) - set(features_esperadas))
    sobrantes = sorted(set(features_esperadas) - set(declaradas))
    if faltantes or sobrantes:
        raise ModeloInvalido(
            f'Features del modelo y del esquema no coinciden. '
            f'El preprocesamiento no genera: {faltantes}. El modelo no usa: {sobrantes}'
        )
    return declaradas


def validar_cantidad_de_features(estimador: Any, features_esperadas: tuple[str, ...]) -> tuple[str, ...]:
    cantidad_del_modelo = getattr(estimador, 'n_features_in_', None)
    if cantidad_del_modelo is not None and cantidad_del_modelo != len(features_esperadas):
        raise ModeloInvalido(
            f'El modelo espera {cantidad_del_modelo} features y el preprocesamiento genera {len(features_esperadas)}'
        )
    return features_esperadas


def hash_de_archivo(ruta: Path) -> str:
    return hashlib.sha256(ruta.read_bytes()).hexdigest()[:CARACTERES_HASH_VERSION]


def predecir(modelo: ModeloCargado, filas: Sequence[Mapping[str, object]]) -> list[int]:
    tabla = pd.DataFrame(list(filas), columns=list(modelo.features))
    prediccion = modelo.estimador.predict(tabla)
    if modelo.cortes is None:
        return [int(clase) for clase in prediccion]
    return clasificar_por_cortes(prediccion, modelo.cortes)


def clasificar_por_cortes(prediccion: Sequence[float], cortes: Sequence[float]) -> list[int]:
    return [CLASES_DE_INGRESO[posicion] for posicion in np.digitize(prediccion, cortes)]


def a_valor_nativo(valor: object) -> object:
    return valor.item() if callable(getattr(valor, 'item', None)) else valor
