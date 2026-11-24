from __future__ import annotations

import pickle
from pathlib import Path

import pandas as pd
import pytest
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.tree import DecisionTreeClassifier

from my_actor.esquema import Campo, Esquema, TipoCampo
from my_actor.modelo import ModeloCargado, cargar_modelo

CAMPOS_DE_PRUEBA: tuple[Campo, ...] = (
    Campo('edad', TipoCampo.ENTERO, alias=('Edad (años)',), minimo=10, maximo=100),
    Campo(
        'nivel',
        TipoCampo.CODIGO,
        alias=('Nivel educativo',),
        opciones={'primario': 1, 'secundario': 2, 'universitario': 3, 'facultad': 3},
    ),
    Campo('ingreso', TipoCampo.NUMERO, alias=('Ingreso mensual',), minimo=0),
    Campo('region', TipoCampo.ENTERO, alias=('Región',), obligatorio=False, minimo=1, maximo=2),
)

ESQUEMA_DE_PRUEBA = Esquema(CAMPOS_DE_PRUEBA)
FEATURES_DE_PRUEBA = ESQUEMA_DE_PRUEBA.features

FILAS_DE_ENTRENAMIENTO = [
    {'edad': 25, 'nivel': 1, 'ingreso': 300000.0, 'region': 2},
    {'edad': 67, 'nivel': 3, 'ingreso': 900000.0, 'region': 1},
    {'edad': 31, 'nivel': 2, 'ingreso': 250000.0, 'region': 2},
    {'edad': 72, 'nivel': 3, 'ingreso': 1200000.0, 'region': 1},
]
CLASES_DE_ENTRENAMIENTO = [1, 3, 1, 3]
INGRESOS_DE_ENTRENAMIENTO = [10.0, 30.0, 12.0, 32.0]
CORTES_DE_PRUEBA = [15.0, 25.0]


def entrenar_pipeline_de_prueba() -> Pipeline:
    pipeline = Pipeline(
        [('imputador', SimpleImputer(strategy='median')), ('clasificador', DecisionTreeClassifier(random_state=0))]
    )
    pipeline.fit(pd.DataFrame(FILAS_DE_ENTRENAMIENTO, columns=list(FEATURES_DE_PRUEBA)), CLASES_DE_ENTRENAMIENTO)
    return pipeline


def entrenar_regresor_de_prueba() -> Pipeline:
    pipeline = Pipeline(
        [
            ('imputador', SimpleImputer(strategy='median')),
            ('regresor', GradientBoostingRegressor(n_estimators=20, max_depth=1, random_state=0)),
        ]
    )
    pipeline.fit(pd.DataFrame(FILAS_DE_ENTRENAMIENTO, columns=list(FEATURES_DE_PRUEBA)), INGRESOS_DE_ENTRENAMIENTO)
    return pipeline


def guardar_pickle(contenido: object, ruta: Path) -> Path:
    with ruta.open('wb') as archivo:
        pickle.dump(contenido, archivo)
    return ruta


@pytest.fixture(scope='session')
def pipeline_de_prueba() -> Pipeline:
    return entrenar_pipeline_de_prueba()


@pytest.fixture(scope='session')
def regresor_de_prueba() -> Pipeline:
    return entrenar_regresor_de_prueba()


@pytest.fixture
def ruta_paquete_con_cortes(tmp_path: Path, regresor_de_prueba: Pipeline) -> Path:
    paquete = {'modelo': regresor_de_prueba, 'features': list(FEATURES_DE_PRUEBA), 'cortes': CORTES_DE_PRUEBA}
    return guardar_pickle(paquete, tmp_path / 'regresor.pkl')


@pytest.fixture
def ruta_paquete(tmp_path: Path, pipeline_de_prueba: Pipeline) -> Path:
    paquete = {'modelo': pipeline_de_prueba, 'features': list(FEATURES_DE_PRUEBA), 'version': 'prueba-1'}
    return guardar_pickle(paquete, tmp_path / 'paquete.pkl')


@pytest.fixture
def ruta_estimador_suelto(tmp_path: Path, pipeline_de_prueba: Pipeline) -> Path:
    return guardar_pickle(pipeline_de_prueba, tmp_path / 'estimador.pkl')


@pytest.fixture
def modelo_de_prueba(ruta_paquete: Path) -> ModeloCargado:
    return cargar_modelo(ruta_paquete, FEATURES_DE_PRUEBA)


@pytest.fixture
def respuestas_validas() -> dict[str, object]:
    return {
        'Marca temporal': '20/11/2026 10:15:00',
        'Nombre y apellido': 'Ana Pérez',
        'Edad (años)': '34',
        'Nivel educativo': ' Facultad ',
        'Ingreso mensual': '$ 450.000,50',
    }


@pytest.fixture
def input_de_make(respuestas_validas: dict[str, object]) -> dict[str, object]:
    return {
        'formularios': [
            {'id_respuesta': 'fila-2', 'respuestas': respuestas_validas},
            {'id_respuesta': 'fila-3', 'respuestas': {'Edad (años)': 'treinta', 'Nivel educativo': 'doctorado'}},
        ]
    }
