import pytest

from my_actor.errores import ValorInvalido
from my_actor.normalizacion import convertir_categoria, convertir_codigo, convertir_entero, convertir_numero, es_vacio, normalizar_texto

CODIGOS = {'primario completo': 2, 'secundario completo': 4, 'sin instruccion': 7}
CATEGORIAS = {'obra social': 'obra_social', 'pami': 'obra_social', 'prepaga': 'prepaga'}


@pytest.mark.parametrize(
    ('texto', 'esperado'),
    [
        ('¿Cuántos años tenés?', 'cuantos anos tenes'),
        ('  Relación   de Dependencia ', 'relacion de dependencia'),
        ('SIN-INSTRUCCIÓN', 'sin instruccion'),
    ],
)
def test_normalizar_texto_quita_acentos_signos_y_mayusculas(texto: str, esperado: str) -> None:
    assert normalizar_texto(texto) == esperado


@pytest.mark.parametrize('valor', [None, '', '   '])
def test_es_vacio_detecta_respuestas_sin_contenido(valor: object) -> None:
    assert es_vacio(valor)


@pytest.mark.parametrize('valor', [0, False, 'no'])
def test_es_vacio_no_confunde_ceros_ni_negativas(valor: object) -> None:
    assert not es_vacio(valor)


@pytest.mark.parametrize(
    ('valor', 'esperado'),
    [
        (42, 42.0),
        (3.5, 3.5),
        ('1234', 1234.0),
        ('1.234,56', 1234.56),
        ('1,234.56', 1234.56),
        ('$ 150.000', 150000.0),
        ('1.500', 1500.0),
        ('12.5', 12.5),
        ('2,75', 2.75),
        ('1.234.567', 1234567.0),
        ('-10', -10.0),
    ],
)
def test_convertir_numero_acepta_formatos_argentinos_e_internacionales(valor: object, esperado: float) -> None:
    assert convertir_numero(valor) == pytest.approx(esperado)


@pytest.mark.parametrize('valor', ['abc', '', True, None, ['1']])
def test_convertir_numero_rechaza_valores_no_numericos(valor: object) -> None:
    with pytest.raises(ValorInvalido):
        convertir_numero(valor)


def test_convertir_entero_rechaza_decimales() -> None:
    assert convertir_entero('34') == 34
    with pytest.raises(ValorInvalido):
        convertir_entero('34,5')


@pytest.mark.parametrize(
    ('valor', 'esperado'),
    [('Secundario Completo', 4), ('  SIN INSTRUCCIÓN ', 7), ('4', 4), (2, 2), (7.0, 7)],
)
def test_convertir_codigo_acepta_etiqueta_o_codigo_numerico(valor: object, esperado: int) -> None:
    assert convertir_codigo(valor, CODIGOS) == esperado


@pytest.mark.parametrize('valor', ['doctorado', '5', 3, True])
def test_convertir_codigo_rechaza_etiquetas_y_codigos_desconocidos(valor: object) -> None:
    with pytest.raises(ValorInvalido):
        convertir_codigo(valor, CODIGOS)


@pytest.mark.parametrize(('valor', 'esperado'), [('Obra Social', 'obra_social'), ('obra_social', 'obra_social'), (' PAMI ', 'obra_social')])
def test_convertir_categoria_acepta_etiquetas_sin_importar_formato(valor: object, esperado: str) -> None:
    assert convertir_categoria(valor, CATEGORIAS) == esperado


@pytest.mark.parametrize('valor', ['seguro', '1', 1])
def test_convertir_categoria_no_acepta_codigos_numericos(valor: object) -> None:
    with pytest.raises(ValorInvalido):
        convertir_categoria(valor, CATEGORIAS)
