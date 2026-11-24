import re
import unicodedata
from collections.abc import Mapping

from my_actor.errores import ValorInvalido

PATRON_MILES_CON_PUNTO = re.compile(r'-?\d{1,3}(\.\d{3})+')
PATRON_CARACTERES_NO_NUMERICOS = re.compile(r'[^\d,.\-]')
PATRON_NO_ALFANUMERICO = re.compile(r'[^a-z0-9]+')


def normalizar_texto(texto: str) -> str:
    sin_acentos = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('ascii')
    return PATRON_NO_ALFANUMERICO.sub(' ', sin_acentos.lower()).strip()


def es_vacio(valor: object) -> bool:
    if valor is None:
        return True
    if isinstance(valor, str):
        return not valor.strip()
    return False


def convertir_numero(valor: object) -> float:
    if isinstance(valor, bool):
        raise ValorInvalido('no es un número')
    if isinstance(valor, int | float):
        return float(valor)
    if not isinstance(valor, str):
        raise ValorInvalido('no es un número')
    try:
        return float(unificar_separador_decimal(PATRON_CARACTERES_NO_NUMERICOS.sub('', valor)))
    except ValueError as error:
        raise ValorInvalido('no es un número') from error


def unificar_separador_decimal(numero: str) -> str:
    if ',' in numero and '.' in numero:
        separador_miles = '.' if numero.rfind(',') > numero.rfind('.') else ','
        return numero.replace(separador_miles, '').replace(',', '.')
    if numero.count(',') > 1:
        return numero.replace(',', '')
    if ',' in numero:
        return numero.replace(',', '.')
    if numero.count('.') > 1 or PATRON_MILES_CON_PUNTO.fullmatch(numero):
        return numero.replace('.', '')
    return numero


def convertir_entero(valor: object) -> int:
    numero = convertir_numero(valor)
    if not numero.is_integer():
        raise ValorInvalido('no es un número entero')
    return int(numero)


def convertir_codigo(valor: object, codigos: Mapping[str, int]) -> int:
    codigo = buscar_opcion(valor, codigos)
    if codigo is not None:
        return codigo
    if es_codigo_numerico(valor, set(codigos.values())):
        return convertir_entero(valor)
    raise ValorInvalido('opción no reconocida')


def convertir_categoria(valor: object, categorias: Mapping[str, str]) -> str:
    categoria = buscar_opcion(valor, categorias)
    if categoria is None:
        raise ValorInvalido('opción no reconocida')
    return categoria


def buscar_opcion[T](valor: object, opciones: Mapping[str, T]) -> T | None:
    opcion_por_texto = {normalizar_texto(etiqueta): opcion for etiqueta, opcion in opciones.items()}
    return opcion_por_texto.get(normalizar_texto(str(valor)))


def es_codigo_numerico(valor: object, codigos_validos: set[int]) -> bool:
    try:
        return convertir_entero(valor) in codigos_validos
    except ValorInvalido:
        return False
