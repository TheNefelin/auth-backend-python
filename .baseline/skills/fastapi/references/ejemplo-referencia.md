# Ejemplo de referencia (no normativo) — fastapi

> Casos concretos del proyecto que originó esta skill. **No son reglas**: si el proyecto cambia, se actualiza este archivo y `SKILL.md` sigue vigente.

## Borrado explícito (sin cascadas)

Tablas del proyecto: `wm_edition`, `wm_format`, `wm_edition_format` (puente) y `wm_copy`. Prefijo `wm_`.

- **Borrar `Edition`**: `editions/repository.delete_formats_by_edition` hace `SELECT` de las filas puente, `db.delete` de cada una y `flush`; después `db.delete(edition)`. `Format` queda intacto.
- **Borrar `Edition` con `Copy` asociadas**: se bloquea con `BadRequestProblem` (patrón `has_copies`), no se arrastra nada.
- **Borrar `Format`**: prohibido mientras tenga puentes; se valida primero y se bloquea.

Incorrecto: `relationship(cascade="all, delete-orphan")` en `Format` → arrastra `EditionFormat` y deja huérfanas las ediciones.

## Equivalencias con los nombres genéricos

| Genérico en `SKILL.md` | Nombre en el proyecto |
|---|---|
| `exists_by_*` | `edition_exists`, `copy_status_exists` |
| tabla puente | `wm_edition_format` |
| prefijo de tablas | `wm_` |
| feature de ejemplo | `products` / `categories` |

## Nota

Los nombres concretos existen para que el agente reconozca el caso cuando trabaje en este proyecto. En un proyecto nuevo, se usan los genéricos de `SKILL.md` y este archivo no aplica.
