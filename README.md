# RRG — REAPER Region Generator

Herramienta en Python para generar archivos de regiones compatibles con [REAPER](https://www.reaper.fm/).

## Características

- Exporta regiones en **tres formatos**:
  - **CSV** — importable desde el Region/Marker Manager de REAPER.
  - **Lua ReaScript** — script ejecutable desde el menú Actions de REAPER.
  - **RPP markers** — fragmento para incluir en un archivo `.rpp`.
- Carga regiones desde un **archivo CSV** o usa **plantillas integradas** (`song`, `podcast`).
- Soporta **colores personalizados** por región (RGB).

## Requisitos

- Python 3.8 o superior.

## Instalación

```bash
pip install -e .
```

## Uso

### Desde la línea de comandos

```bash
# Generar CSV con la plantilla de canción
rrg --template song --format csv -o regiones.csv

# Generar Lua ReaScript con la plantilla de podcast
rrg --template podcast --format lua -o regiones.lua

# Generar marcadores RPP desde un archivo CSV personalizado
rrg --csv mi_estructura.csv --format rpp -o marcadores.txt
```

### Formato del CSV de entrada

```
name,start,end,r,g,b
Intro,0,15,100,150,255
Verse 1,15,45,100,200,100
```

Columnas: `name`, `start` (segundos), `end` (segundos), y opcionalmente `r`, `g`, `b` (color RGB 0-255).

### Como librería Python

```python
from rrg.generator import RegionGenerator

gen = RegionGenerator()
gen.add_region("Intro", 0, 15, color=(100, 150, 255))
gen.add_region("Verse", 15, 45, color=(100, 200, 100))

gen.to_csv("regiones.csv")   # Para importar en REAPER
gen.to_lua("regiones.lua")   # ReaScript para REAPER
```

## Plantillas integradas

| Plantilla  | Regiones | Descripción                      |
|------------|----------|----------------------------------|
| `song`     | 8        | Estructura pop/rock estándar     |
| `podcast`  | 5        | Estructura de episodio de podcast|

## Tests

```bash
pip install pytest
python -m pytest tests/ -v
```

## Ejemplos

Archivos de ejemplo en la carpeta [`examples/`](examples/):

- `song_structure.csv` — estructura de canción
- `podcast_structure.csv` — estructura de podcast
