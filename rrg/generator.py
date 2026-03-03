"""Modelo de región y lógica del generador para regiones de REAPER."""

import csv
import uuid


class Region:
    """Representa una región de REAPER con nombre, rango de tiempo y color."""

    def __init__(self, name, start, end, color=None):
        """Crea una Región.

        Args:
            name: Nombre visible de la región.
            start: Tiempo de inicio en segundos.
            end: Tiempo de fin en segundos.
            color: Tupla opcional de (r, g, b) enteros 0-255.

        Raises:
            ValueError: Si start >= end o los tiempos son negativos.
        """
        if start < 0 or end < 0:
            raise ValueError("Los tiempos de la región deben ser no negativos")
        if start >= end:
            raise ValueError(
                f"El inicio de la región ({start}) debe ser anterior al fin ({end})"
            )
        self.name = name
        self.start = float(start)
        self.end = float(end)
        self.color = color

    @property
    def length(self):
        """Duración de la región en segundos."""
        return self.end - self.start

    def reaper_color(self):
        """Devuelve el entero de color nativo de REAPER para esta región.

        REAPER almacena colores como ``(r | (g << 8) | (b << 16)) | 0x1000000``.
        Devuelve 0 (color por defecto) cuando no se asigna color.
        """
        if self.color is None:
            return 0
        r, g, b = self.color
        return (r | (g << 8) | (b << 16)) | 0x1000000

    def __repr__(self):
        return (
            f"Region(name={self.name!r}, start={self.start}, "
            f"end={self.end}, color={self.color})"
        )

    def __eq__(self, other):
        if not isinstance(other, Region):
            return NotImplemented
        return (
            self.name == other.name
            and self.start == other.start
            and self.end == other.end
            and self.color == other.color
        )


class RegionGenerator:
    """Construye una lista de regiones de REAPER y las exporta en varios formatos."""

    def __init__(self):
        self.regions = []

    def add_region(self, name, start, end, color=None):
        """Agrega una región al generador.

        Args:
            name: Nombre de la región.
            start: Tiempo de inicio en segundos.
            end: Tiempo de fin en segundos.
            color: Tupla opcional (r, g, b).

        Returns:
            La instancia de Region creada.
        """
        region = Region(name, start, end, color)
        self.regions.append(region)
        return region

    def clear(self):
        """Elimina todas las regiones."""
        self.regions.clear()

    # ---- Ayudantes de entrada ------------------------------------------- #

    def load_csv(self, filepath):
        """Carga regiones desde un archivo CSV.

        Columnas esperadas: ``name, start, end[, r, g, b]``

        Args:
            filepath: Ruta al archivo CSV.
        """
        with open(filepath, newline="", encoding="utf-8") as fh:
            reader = csv.reader(fh)
            header = next(reader, None)
            if header is None:
                return
            for row in reader:
                if not row or not row[0].strip():
                    continue
                name = row[0].strip()
                start = float(row[1])
                end = float(row[2])
                color = None
                if len(row) >= 6 and row[3].strip():
                    color = (int(row[3]), int(row[4]), int(row[5]))
                self.add_region(name, start, end, color)

    def load_template(self, template_name):
        """Carga una plantilla de regiones integrada.

        Plantillas disponibles:
            - ``song``: Estructura estándar de canción pop/rock.
            - ``podcast``: Estructura simple de episodio de podcast.

        Args:
            template_name: Nombre de la plantilla.

        Raises:
            ValueError: Si el nombre de la plantilla es desconocido.
        """
        templates = {
            "song": [
                ("Intro", 0, 15, (100, 150, 255)),
                ("Verse 1", 15, 45, (100, 200, 100)),
                ("Chorus 1", 45, 75, (255, 200, 50)),
                ("Verse 2", 75, 105, (100, 200, 100)),
                ("Chorus 2", 105, 135, (255, 200, 50)),
                ("Bridge", 135, 160, (200, 100, 200)),
                ("Chorus 3", 160, 190, (255, 200, 50)),
                ("Outro", 190, 210, (100, 150, 255)),
            ],
            "podcast": [
                ("Intro", 0, 30, (100, 150, 255)),
                ("Topic 1", 30, 300, (100, 200, 100)),
                ("Topic 2", 300, 600, (200, 200, 100)),
                ("Topic 3", 600, 900, (200, 100, 100)),
                ("Outro", 900, 960, (100, 150, 255)),
            ],
        }

        if template_name not in templates:
            raise ValueError(
                f"Plantilla desconocida '{template_name}'. "
                f"Disponibles: {', '.join(sorted(templates))}"
            )

        for name, start, end, color in templates[template_name]:
            self.add_region(name, start, end, color)

    # ---- Ayudantes de salida -------------------------------------------- #

    def to_csv(self, filepath):
        """Exporta regiones como archivo CSV separado por tabulaciones compatible con REAPER.

        El archivo se puede importar desde el Region/Marker Manager de REAPER.

        Args:
            filepath: Ruta del archivo de destino.
        """
        with open(filepath, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh, delimiter="\t")
            writer.writerow(["#", "Name", "Start", "End", "Length", "Color"])
            for idx, region in enumerate(self.regions, start=1):
                writer.writerow([
                    f"R{idx}",
                    region.name,
                    _format_time(region.start),
                    _format_time(region.end),
                    _format_time(region.length),
                    region.reaper_color(),
                ])

    def to_lua(self, filepath):
        """Exporta regiones como un script Lua ReaScript para ejecutar en REAPER.

        Los usuarios pueden ejecutar el archivo ``.lua`` generado desde el menú
        Actions de REAPER.

        Args:
            filepath: Ruta del archivo de destino.
        """
        lines = [
            "-- RRG: Generador de Regiones para REAPER",
            "-- Ejecuta este script dentro de REAPER para crear las regiones.",
            "",
            "reaper.Undo_BeginBlock()",
            'reaper.PreventUIRefresh(1)',
            "",
        ]
        for region in self.regions:
            color = region.reaper_color()
            is_rgn = "true"
            lines.append(
                f'reaper.AddProjectMarker2(0, {is_rgn}, {region.start}, '
                f'{region.end}, "{region.name}", -1, {color})'
            )
        lines += [
            "",
            'reaper.PreventUIRefresh(-1)',
            "reaper.UpdateArrange()",
            'reaper.Undo_EndBlock("RRG: Crear regiones", -1)',
            "",
        ]
        with open(filepath, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines))

    def to_rpp_markers(self, filepath):
        """Exporta regiones como líneas MARKER de RPP para incluir en un archivo .rpp.

        Cada región se representa como un par de entradas MARKER (inicio/fin).

        Args:
            filepath: Ruta del archivo de destino.
        """
        lines = []
        marker_id = 1
        for region in self.regions:
            guid = "{" + str(uuid.uuid4()).upper() + "}"
            color = region.reaper_color()
            lines.append(
                f'  MARKER {marker_id} {region.start} "{region.name}" '
                f"{color} 0 1 B {guid}"
            )
            lines.append(
                f'  MARKER {marker_id} {region.end} "" '
                f"{color} 0 1 B {guid}"
            )
            marker_id += 1
        with open(filepath, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")


# ---- Ayudantes --------------------------------------------------------- #


def _format_time(seconds):
    """Formatea segundos como ``M:SS.mmm`` para importación CSV de REAPER."""
    minutes = int(seconds) // 60
    secs = seconds - minutes * 60
    return f"{minutes}:{secs:06.3f}"
