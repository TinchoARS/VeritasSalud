## ¿Qué hace ObraSocialApp?

**ObraSocialApp** estima la **clase de ingreso mensual** de una persona joven que trabaja (de **18 a 30 años**) a partir de las **10 respuestas de un formulario**. Usa un modelo de machine learning entrenado con la [Encuesta Permanente de Hogares (EPH) del INDEC](https://www.indec.gob.ar/indec/web/Institucional-Indec-BasesDeDatos) y devuelve, para cada respuesta:

- la **clase de ingreso** (1, 2 o 3) con su **tramo en pesos**;
- la **ciudad** (aglomerado EPH) y la **región** de la persona;
- si el formulario no se pudo procesar, **qué campos están mal y por qué**.

| Clase | Ingreso mensual de la ocupación principal |
|---|---|
| 1 | menos de $600.000 |
| 2 | de $600.000 a $1.200.000 |
| 3 | más de $1.200.000 |

El Actor **no hace scraping ni descarga nada**: recibe las respuestas como JSON (por ejemplo desde **Make**), las prepara y ejecuta el modelo. Tampoco guarda las respuestas.

## ¿Para qué sirve?

- **Clasificar automáticamente las respuestas de un Google Form**: Make lee las respuestas, llama al Actor y guarda el resultado en Drive, una planilla o un mail.
- **Ubicar a cada persona por ciudad y región**, para cruzar su clase de ingreso con la oferta de planes de salud disponible en su ciudad.
- **Validar el formulario**: cada respuesta mal cargada vuelve con la lista de campos a corregir, sin frenar al resto.
- **Aprovechar la plataforma Apify**: API para llamarlo desde cualquier sistema, integración nativa con Make, historial de ejecuciones y ejecución programada.

## ¿Qué datos devuelve?

| Campo | Tipo | Descripción |
|---|---|---|
| `id_respuesta` | texto | El identificador que mandaste con el formulario (por ejemplo, el número de fila) |
| `estado` | texto | `ok` si se pudo predecir, `invalido` si alguna respuesta no sirve |
| `clase_ingreso` | número | 1, 2 o 3 (vacío si es inválido) |
| `ingreso_desde` / `ingreso_hasta` | número | Tramo en pesos de la clase. La clase 3 no tiene techo (`ingreso_hasta` vacío) |
| `aglomerado` / `aglomerado_nombre` | número / texto | Código EPH y nombre de la ciudad |
| `region` | texto | Región EPH: GBA, Pampeana, NOA, NEA, Cuyo o Patagonia |
| `errores` | lista | Campos con problemas y el motivo, sin repetir lo que respondió la persona |
| `version_modelo` | texto | Identificador del modelo que hizo la predicción |

## Cómo usar ObraSocialApp desde Make

1. Armá el formulario con las 10 preguntas de la sección [Input](#input).
2. En Make, agregá el módulo **Apify → Run an Actor**, elegí `tinchoars/obrasocialapp` y activá la ejecución sincrónica.
3. En el input mandá `formularios`: una lista con un elemento por respuesta, cada uno con `id_respuesta` y `respuestas`.
4. Leé los resultados con **Apify → Get Dataset Items**, usando el `defaultDatasetId` de la ejecución.
5. Separá por `estado`: con `ok` usá `clase_ingreso` y el tramo; con `invalido` mirá `errores`.

Para probarlo sin Make, abrí la pestaña **Input** en la consola de Apify: ya trae un formulario de ejemplo cargado. Tocá **Start** y mirá el resultado en la pestaña **Output**.

## ¿Cuánto cuesta usar ObraSocialApp?

Se paga solo el consumo de la plataforma (unidades de cómputo). Una ejecución con 4 formularios tardó **7 segundos** y consumió **0,002 unidades de cómputo** con 1 GB de memoria: menos de un centavo de dólar. El plan gratuito de Apify incluye créditos mensuales que alcanzan para miles de ejecuciones como esa.

Casi todo ese tiempo es el arranque y la carga del modelo. Procesar 1 o 1000 formularios en la misma ejecución cuesta prácticamente lo mismo.

## Input

Mirá la pestaña **Input** para ver el formato completo. El input tiene un solo campo, `formularios`: una lista de hasta **1000** respuestas, cada una con:

- `id_respuesta`: texto o número que identifica la respuesta. Usá algo que no sea un dato personal (por ejemplo, el número de fila, no el mail).
- `respuestas`: un objeto pregunta → respuesta. Make a veces lo manda como texto JSON; también se acepta así.

### Las 10 preguntas del formulario

Todas son **obligatorias**.

| # | Pregunta (o clave interna) | Respuestas aceptadas |
|---|---|---|
| 1 | Cobertura de salud (`cobertura_salud`) | Obra social (o PAMI), Prepaga (o Mutual), Sin cobertura (o Ninguna, No tengo) |
| 2 | Edad (`edad`) | Número entero de 18 a 30 |
| 3 | Nivel educativo (`nivel_educativo`) | Sin instrucción, Primario incompleto, Primario completo, Secundario incompleto, Secundario completo, Universitario incompleto, Universitario completo (terciario también vale), o el código EPH 1–7 |
| 4 | ¿Tu empleo está registrado? (`formalidad_empleo`) | Sí / No (también Registrado / No registrado, En blanco / En negro, Formal / Informal) |
| 5 | Sexo (`sexo`) | Varón / Mujer |
| 6 | ¿Cuántas personas trabajan junto a usted en su ocupación principal? (`tamano_establecimiento`) | Hasta 5, De 6 a 40, Más de 40 |
| 7 | ¿Cuántas horas trabajaste la semana pasada en tu ocupación principal? (`horas_trabajo`) | Número de 1 a 168 (se aceptan decimales con coma o punto) |
| 8 | ¿Qué calificación tiene tu ocupación? (`calificacion_ocupacion`) | Profesional, Técnica, Operativa, No calificada |
| 9 | Ciudad (`aglomerado`) | Una de las [32 ciudades de la EPH](#ciudades-aceptadas), por nombre o código |
| 10 | ¿Alquilás la vivienda donde vivís? (`inquilino`) | Sí / No |

- Las preguntas se reconocen por su texto o por la clave interna, sin importar mayúsculas, acentos ni signos.
- Las columnas que no son de estas 10 preguntas (marca temporal, nombre, mail) se ignoran y no se guardan.

### Ejemplo de input

```json
{
  "formularios": [
    {
      "id_respuesta": "fila-2",
      "respuestas": {
        "Cobertura de salud": "Obra social",
        "Edad": "27",
        "Nivel educativo": "Universitario completo",
        "¿Tu empleo está registrado?": "Sí",
        "Sexo": "Mujer",
        "¿Cuántas personas trabajan junto a usted en su ocupación principal?": "De 6 a 40",
        "¿Cuántas horas trabajaste la semana pasada en tu ocupación principal?": "40",
        "¿Qué calificación tiene tu ocupación?": "Técnica",
        "Ciudad": "Gran Rosario",
        "¿Alquilás la vivienda donde vivís?": "Sí"
      }
    }
  ]
}
```

## Output

Cada formulario genera un ítem en el dataset, en el mismo orden en que llegó. Podés descargar el dataset en **JSON, CSV, Excel o HTML** desde la pestaña **Output** o por API.

```json
[
  {
    "id_respuesta": "fila-2",
    "estado": "ok",
    "clase_ingreso": 3,
    "ingreso_desde": 1200000,
    "ingreso_hasta": null,
    "aglomerado": 4,
    "aglomerado_nombre": "Gran Rosario",
    "region": "Pampeana",
    "errores": [],
    "version_modelo": "db5a69e676b8"
  },
  {
    "id_respuesta": "fila-5",
    "estado": "invalido",
    "clase_ingreso": null,
    "ingreso_desde": null,
    "ingreso_hasta": null,
    "aglomerado": 4,
    "aglomerado_nombre": "Gran Rosario",
    "region": "Pampeana",
    "errores": [
      { "campo": "cobertura_salud", "motivo": "opción no reconocida" },
      { "campo": "edad", "motivo": "mayor que el máximo permitido (30)" },
      { "campo": "sexo", "motivo": "obligatorio sin respuesta" }
    ],
    "version_modelo": "db5a69e676b8"
  }
]
```

Los motivos de error posibles son: `obligatorio sin respuesta`, `opción no reconocida`, `no es un número`, `no es un número entero`, `menor que el mínimo permitido (…)` y `mayor que el máximo permitido (…)`.

Además, el registro `RESUMEN` del key-value store guarda cuántos formularios fueron válidos e inválidos y qué versión del modelo se usó.

## Cómo calcula la clase de ingreso

- El modelo (Gradient Boosting) estima el **ingreso mensual de la ocupación principal** de la persona, no el del hogar.
- Esa estimación se compara con dos cortes guardados junto al modelo: **$582.267** y **$1.200.000**. El primero está un poco por debajo de $600.000 porque así el modelo distingue mejor la clase 2. El resultado informa igual los tramos nominales de la tabla de arriba.
- En la evaluación con datos de prueba, el modelo acertó la clase en el **68,9 %** de los casos.
- Lo que más pesa en la predicción son las horas trabajadas, si el empleo está registrado, la cobertura de salud y la ciudad.

### Limitaciones

- Sirve solo para **personas de 18 a 30 años que trabajan**. Otras edades se rechazan como inválidas.
- Los montos en pesos corresponden al **período de la encuesta** y no se ajustan por inflación.
- La pregunta de **cuántas personas trabajan junto a usted** no cambia el resultado: el modelo la requiere, pero no le da peso.
- Es una estimación estadística: en aproximadamente 3 de cada 10 casos la clase no coincide con la real.

## Privacidad y datos personales

- El Actor **no guarda las respuestas** del formulario. El dataset lleva solo el identificador, la clase, el tramo, la ciudad y la región.
- Los errores informan el **nombre del campo** y el motivo, nunca el valor que cargó la persona.
- Los logs no muestran respuestas.
- Recomendación: no uses como `id_respuesta` datos que identifiquen a la persona (mail, DNI, nombre).

## Preguntas frecuentes

### ¿Por qué un formulario salió `invalido`?

Mirá `errores`: dice qué pregunta falta o qué respuesta no se reconoce. Los casos más comunes son edad fuera de 18–30, una opción escrita distinto (por ejemplo «Seguro privado» en cobertura) o una ciudad que no está en la EPH. Un formulario inválido no frena a los demás.

### ¿Por qué falló la ejecución entera?

Solo falla si el input no tiene la forma esperada: falta `formularios`, viene vacío, tiene más de 1000 elementos, o algún elemento no trae `id_respuesta` o `respuestas`. El mensaje de estado de la ejecución dice cuál es el problema.

### ¿Puedo usarlo para personas mayores de 30 o que no trabajan?

No. El modelo se entrenó solo con jóvenes de 18 a 30 años con empleo; para otras personas la estimación no sería confiable.

### ¿Cómo lo llamo por API?

Con el endpoint sincrónico, que ejecuta el Actor y devuelve directamente los resultados. Reemplazá `$APIFY_TOKEN` por tu token (pestaña **API** de la consola):

```bash
curl -X POST "https://api.apify.com/v2/acts/tinchoars~obrasocialapp/run-sync-get-dataset-items" \
  -H "Authorization: Bearer $APIFY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"formularios": [{"id_respuesta": "fila-2", "respuestas": {"cobertura_salud": "Obra social", "edad": 27, "nivel_educativo": "Universitario completo", "formalidad_empleo": "Sí", "sexo": "Mujer", "tamano_establecimiento": "De 6 a 40", "horas_trabajo": 40, "calificacion_ocupacion": "Técnica", "aglomerado": "Gran Rosario", "inquilino": "Sí"}}]}'
```

### Consejos para gastar menos

- Mandá varias respuestas en una misma ejecución (hasta 1000): el costo casi no cambia.
- El Actor usa poca memoria (unos 125 MB). Podés bajarla a 512 MB en las opciones de ejecución.

### ¿Dónde reporto un problema?

En la pestaña **Issues** de este Actor.

## Ciudades aceptadas

Se acepta el nombre, cualquiera de los otros nombres de la tabla, el código EPH o la columna del catálogo de planes (por ejemplo `agl_04_gran_rosario`).

| Código | Ciudad | Región | También se acepta |
|---|---|---|---|
| 2 | Gran La Plata | Pampeana | La Plata |
| 3 | Bahía Blanca - Cerri | Pampeana | Bahía Blanca, Cerri |
| 4 | Gran Rosario | Pampeana | Rosario |
| 5 | Gran Santa Fe | Pampeana | Santa Fe, Ciudad de Santa Fe |
| 6 | Gran Paraná | Pampeana | Paraná |
| 7 | Posadas | NEA | |
| 8 | Gran Resistencia | NEA | Resistencia |
| 9 | Comodoro Rivadavia - Rada Tilly | Patagonia | Comodoro Rivadavia, Comodoro, Rada Tilly |
| 10 | Gran Mendoza | Cuyo | Mendoza |
| 12 | Corrientes | NEA | |
| 13 | Gran Córdoba | Pampeana | Córdoba, Ciudad de Córdoba |
| 14 | Concordia | Pampeana | |
| 15 | Formosa | NEA | |
| 17 | Neuquén - Plottier | Patagonia | Neuquén, Plottier |
| 18 | Santiago del Estero - La Banda | NOA | Santiago del Estero, La Banda |
| 19 | Jujuy - Palpalá | NOA | Jujuy, San Salvador de Jujuy, Palpalá |
| 20 | Río Gallegos | Patagonia | |
| 22 | Gran Catamarca | NOA | Catamarca, San Fernando del Valle de Catamarca |
| 23 | Gran Salta | NOA | Salta |
| 25 | La Rioja | NOA | |
| 26 | Gran San Luis | Cuyo | San Luis |
| 27 | Gran San Juan | Cuyo | San Juan |
| 29 | Gran Tucumán - Tafí Viejo | NOA | Tucumán, San Miguel de Tucumán, Tafí Viejo |
| 30 | Santa Rosa - Toay | Pampeana | Santa Rosa, Toay |
| 31 | Ushuaia - Río Grande | Patagonia | Ushuaia, Río Grande |
| 32 | Ciudad Autónoma de Buenos Aires | GBA | CABA, Capital Federal, Ciudad de Buenos Aires |
| 33 | Partidos del GBA | GBA | GBA, Gran Buenos Aires, Conurbano, Conurbano bonaerense |
| 34 | Mar del Plata | Pampeana | Mar del Plata - Batán |
| 36 | Río Cuarto | Pampeana | |
| 38 | San Nicolás - Villa Constitución | Pampeana | San Nicolás, Villa Constitución |
| 91 | Rawson - Trelew | Patagonia | Rawson, Trelew |
| 93 | Viedma - Carmen de Patagones | Patagonia | Viedma, Carmen de Patagones |
