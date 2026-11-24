from __future__ import annotations

import io
import os
import pickle
from pathlib import Path

import numpy as np
import pytest
from sklearn.pipeline import Pipeline

from my_actor.errores import ModeloInvalido
from my_actor.modelo import (
    MODELO_PATH,
    MODULO_COMPILADO_DE_PERDIDAS,
    LectorDeModelo,
    ModeloCargado,
    cargar_modelo,
    clasificar_por_cortes,
    predecir,
)
from tests.conftest import CORTES_DE_PRUEBA, FEATURES_DE_PRUEBA, FILAS_DE_ENTRENAMIENTO, guardar_pickle


class PickleMalicioso:
    def __reduce__(self) -> tuple[object, tuple[str]]:
        return os.system, ('echo inseguro',)


def test_modelo_path_apunta_al_pickle_del_repositorio() -> None:
    assert MODELO_PATH.parts[-2:] == ('modelos', 'modelo.pkl')


def test_cargar_modelo_desde_paquete_usa_features_y_version_declaradas(ruta_paquete: Path) -> None:
    modelo = cargar_modelo(ruta_paquete, FEATURES_DE_PRUEBA)
    assert modelo.features == FEATURES_DE_PRUEBA
    assert modelo.version == 'prueba-1'


def test_cargar_modelo_desde_estimador_suelto_usa_feature_names_in_y_hash(ruta_estimador_suelto: Path) -> None:
    modelo = cargar_modelo(ruta_estimador_suelto, FEATURES_DE_PRUEBA)
    assert modelo.features == FEATURES_DE_PRUEBA
    assert len(modelo.version) == 12


def test_cargar_modelo_respeta_el_orden_de_columnas_del_modelo(tmp_path: Path, pipeline_de_prueba: Pipeline) -> None:
    orden_del_modelo = list(reversed(FEATURES_DE_PRUEBA))
    ruta = guardar_pickle({'modelo': pipeline_de_prueba, 'features': orden_del_modelo}, tmp_path / 'paquete.pkl')
    assert cargar_modelo(ruta, FEATURES_DE_PRUEBA).features == tuple(orden_del_modelo)


def test_cargar_modelo_falla_si_no_existe_el_archivo(tmp_path: Path) -> None:
    with pytest.raises(ModeloInvalido):
        cargar_modelo(tmp_path / 'inexistente.pkl', FEATURES_DE_PRUEBA)


def test_cargar_modelo_falla_si_el_archivo_no_es_un_pickle(tmp_path: Path) -> None:
    ruta = tmp_path / 'roto.pkl'
    ruta.write_bytes(b'no soy un pickle')
    with pytest.raises(ModeloInvalido):
        cargar_modelo(ruta, FEATURES_DE_PRUEBA)


def test_cargar_modelo_bloquea_pickles_que_ejecutan_codigo(tmp_path: Path) -> None:
    ruta = guardar_pickle(PickleMalicioso(), tmp_path / 'malicioso.pkl')
    with pytest.raises(ModeloInvalido, match='no está permitido'):
        cargar_modelo(ruta, FEATURES_DE_PRUEBA)


def test_cargar_modelo_falla_si_no_hay_estimador(tmp_path: Path) -> None:
    ruta = guardar_pickle({'features': list(FEATURES_DE_PRUEBA)}, tmp_path / 'sin_estimador.pkl')
    with pytest.raises(ModeloInvalido, match='predict'):
        cargar_modelo(ruta, FEATURES_DE_PRUEBA)


def test_cargar_modelo_falla_si_las_features_no_coinciden_con_el_esquema(ruta_paquete: Path) -> None:
    with pytest.raises(ModeloInvalido, match='no coinciden'):
        cargar_modelo(ruta_paquete, (*FEATURES_DE_PRUEBA, 'feature_nueva'))


def test_cargar_modelo_falla_si_no_predice_clases_de_ingreso(tmp_path: Path, pipeline_de_prueba: Pipeline) -> None:
    clases_originales = pipeline_de_prueba.classes_
    pipeline_de_prueba.steps[-1][1].classes_ = np.array(['bajo', 'alto'])
    try:
        ruta = guardar_pickle(pipeline_de_prueba, tmp_path / 'clases.pkl')
    finally:
        pipeline_de_prueba.steps[-1][1].classes_ = clases_originales
    with pytest.raises(ModeloInvalido, match='clases de ingreso'):
        cargar_modelo(ruta, FEATURES_DE_PRUEBA)


def test_predecir_devuelve_clases_enteras(modelo_de_prueba: ModeloCargado) -> None:
    clases = predecir(modelo_de_prueba, FILAS_DE_ENTRENAMIENTO[:2])
    assert clases == [1, 3]
    assert all(type(clase) is int for clase in clases)


def test_predecir_no_necesita_predict_proba(modelo_de_prueba: ModeloCargado) -> None:
    class EstimadorSinProbabilidades:
        def predict(self, tabla: object) -> list[int]:
            return [1] * len(tabla)

    modelo = ModeloCargado(EstimadorSinProbabilidades(), modelo_de_prueba.features, 'x')
    assert predecir(modelo, FILAS_DE_ENTRENAMIENTO[:1]) == [1]


def test_cargar_modelo_con_cortes_clasifica_la_prediccion_del_regresor(ruta_paquete_con_cortes: Path) -> None:
    modelo = cargar_modelo(ruta_paquete_con_cortes, FEATURES_DE_PRUEBA)
    assert modelo.cortes == tuple(CORTES_DE_PRUEBA)
    clases = predecir(modelo, FILAS_DE_ENTRENAMIENTO[:2])
    assert clases == [1, 3]
    assert all(type(clase) is int for clase in clases)


def test_el_regresor_guarda_su_perdida_en_el_modulo_compilado_de_sklearn(ruta_paquete_con_cortes: Path) -> None:
    assert MODULO_COMPILADO_DE_PERDIDAS.encode() in ruta_paquete_con_cortes.read_bytes()
    assert cargar_modelo(ruta_paquete_con_cortes, FEATURES_DE_PRUEBA).cortes is not None


@pytest.mark.parametrize('nombre', ['__builtins__', 'np'])
def test_del_modulo_compilado_de_perdidas_solo_se_aceptan_las_perdidas(nombre: str) -> None:
    with pytest.raises(pickle.UnpicklingError, match='no está permitido'):
        LectorDeModelo(io.BytesIO()).find_class(MODULO_COMPILADO_DE_PERDIDAS, nombre)


@pytest.mark.parametrize('cortes', [[15.0], [25.0, 15.0], [15.0, 15.0], ['bajo', 'alto'], 7])
def test_cargar_modelo_falla_si_los_cortes_no_son_validos(
    tmp_path: Path, regresor_de_prueba: Pipeline, cortes: object
) -> None:
    paquete = {'modelo': regresor_de_prueba, 'features': list(FEATURES_DE_PRUEBA), 'cortes': cortes}
    ruta = guardar_pickle(paquete, tmp_path / 'cortes.pkl')
    with pytest.raises(ModeloInvalido, match='cortes'):
        cargar_modelo(ruta, FEATURES_DE_PRUEBA)


def test_clasificar_por_cortes_pone_el_valor_del_corte_en_la_clase_de_arriba() -> None:
    assert clasificar_por_cortes([10.0, 15.0, 20.0, 25.0, 40.0], CORTES_DE_PRUEBA) == [1, 2, 2, 3, 3]
