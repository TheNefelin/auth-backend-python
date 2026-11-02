---
name: memoria
description: "Auditar la memoria del proyecto (`DEVELOPMENT.md`): presupuesto, poda de historial, decisiones caducadas y rutas muertas. Usar al cerrar una tarea que lo tocó, al iniciar sesión si está sobre el tope, o si lo piden. NO para el catálogo (`catalog-maintenance`) ni para código."
---

# Memoria del proyecto

> Poda `DEVELOPMENT.md` sin perder lo operativo. Esta skill se lee **solo al auditar**; la regla que dispara la auditoría vive en `AGENTS.md` §11 y no se repite aquí.

## Cuándo usar

- Cerrar una tarea que modificó `DEVELOPMENT.md` y el archivo superó el presupuesto blando.
- Iniciar sesión con el archivo ya sobre el tope duro: audita antes de agregar nada.
- El usuario pide "audita la memoria", "esto está muy largo" o "¿qué quedó vigente?".

## Cuándo NO usar

| Situación | Dónde |
|---|---|
| Crear, editar o renombrar una skill del catálogo | `catalog-maintenance` |
| El `DEVELOPMENT.md` del catálogo (inventario y decisiones del propio harness) | `catalog-maintenance` |
| Explicar cómo se usa el proyecto | `README.md` |
| Guardar el avance de una tarea en curso | `.baseline/session.md` (≤40 líneas) |

## Presupuesto

| Nivel | Caracteres | Qué se hace |
|---|---|---|
| Blando | 4.500 | al cerrar, audita antes de reportar |
| Duro | 6.000 | no se agrega nada sin recortar antes |

```powershell
(Get-Content DEVELOPMENT.md -Raw).Length
```

```bash
wc -m < DEVELOPMENT.md
```

Se mide el archivo completo, no solo el historial. Un archivo dentro del blando no se toca aunque tenga fechas viejas: la auditoría no es un ejercicio de estilo.

Aplica a la memoria de un proyecto. El `DEVELOPMENT.md` del catálogo —inventario, decisiones y registro de validación del harness— es otra cosa y no entra en este presupuesto.

## Procedimiento

1. Mide y anota caracteres y líneas: es la columna "antes".
2. Lee `DEVELOPMENT.md` **una vez** y aplica la checklist.
3. Verifica las rutas citadas en lote, sin abrir cada archivo.
4. Escribe el resultado **una vez**.
5. Vuelve a medir: columna "después".

Coste máximo: una lectura y una escritura. Si necesitas releer "para contexto", estás auditando de más.

## Checklist

| # | Criterio | Cómo se comprueba | Acción |
|---|---|---|---|
| 1 | Historial y fechas | entradas fechadas que narran qué pasó | queda la decisión vigente, sin la crónica |
| 2 | Arquitectura narrada | párrafos que repiten el mapa o el README | se reemplazan por una fila del mapa |
| 3 | Decisiones no vigentes | estado `Aceptado` de algo que el código ya no hace | corregir o eliminar |
| 4 | Pendientes resueltos | el código ya lo cumple | eliminar la entrada |
| 5 | Rutas inexistentes | cada ruta en backticks, `Test-Path` en lote | corregir la ruta o quitar la referencia |
| 6 | Contradicción memoria↔código | la memoria afirma X y el código hace Y | gana el código: corrige la memoria y repórtalo |

## Reglas duras

- No inventes contenido para rellenar una sección vacía: déjala vacía o bórrala.
- No borres una decisión vigente por "limpieza": márcala `Pendiente` y pregunta.
- No crees un segundo documento de memoria.
- No muevas contenido a otro archivo salvo que sea de consulta puntual; el patrón es una fila de mapa, no una mudanza.
- El código manda sobre la memoria: una contradicción se corrige en la memoria, nunca en el código, dentro de esta tarea.

## Formato de salida

| Métrica | Antes | Después |
|---|---|---|
| Caracteres | 8.663 | 4.064 |
| Líneas | 97 | 65 |

Después de la tabla: **qué se quitó y por qué** (con la evidencia), **qué se conservó por ser operativo**, y el mensaje de commit propuesto (`docs(memoria): ...`). Los números salen del comando, no de una estimación.
