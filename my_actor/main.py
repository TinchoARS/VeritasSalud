from apify import Actor, Event

from my_actor.errores import EntradaInvalida, ModeloInvalido
from my_actor.modelo import cargar_modelo
from my_actor.procesamiento import procesar
from my_actor.salidas import resumir


async def al_abortar() -> None:
    await Actor.exit()


async def main() -> None:
    async with Actor:
        Actor.on(Event.ABORTING, al_abortar)
        try:
            modelo = cargar_modelo()
            resultados = procesar(await Actor.get_input(), modelo)
        except (EntradaInvalida, ModeloInvalido) as error:
            await Actor.fail(status_message=str(error))
            return
        await Actor.push_data(resultados)
        resumen = resumir(resultados)
        await Actor.set_value('RESUMEN', resumen)
        await Actor.set_status_message(f'{resumen["validos"]} de {resumen["total"]} formularios procesados')
