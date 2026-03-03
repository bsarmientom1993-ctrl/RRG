"""Interfaz de línea de comandos para RRG - Generador de Regiones para REAPER."""

import argparse
import sys

from rrg.generator import RegionGenerator


def main(argv=None):
    """Punto de entrada para el comando ``rrg``."""
    parser = argparse.ArgumentParser(
        prog="rrg",
        description="RRG - Generador de Regiones para REAPER: crea archivos de regiones para REAPER.",
    )

    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--csv",
        metavar="ARCHIVO",
        help="Archivo CSV de entrada con columnas: name, start, end[, r, g, b]",
    )
    input_group.add_argument(
        "--template",
        choices=["song", "podcast"],
        help="Usar una plantilla integrada (song, podcast)",
    )

    parser.add_argument(
        "--format",
        choices=["csv", "lua", "rpp"],
        default="lua",
        help="Formato de salida: csv (importar en REAPER), lua (ReaScript), rpp (marcadores RPP). Por defecto: lua",
    )
    parser.add_argument(
        "-o",
        "--output",
        metavar="ARCHIVO",
        required=True,
        help="Ruta del archivo de salida",
    )

    args = parser.parse_args(argv)

    gen = RegionGenerator()

    if args.csv:
        try:
            gen.load_csv(args.csv)
        except FileNotFoundError:
            print(f"Error: archivo de entrada no encontrado: {args.csv}", file=sys.stderr)
            return 1
        except Exception as exc:
            print(f"Error al leer CSV: {exc}", file=sys.stderr)
            return 1
    else:
        gen.load_template(args.template)

    if not gen.regions:
        print("Advertencia: no hay regiones para exportar.", file=sys.stderr)
        return 1

    if args.format == "csv":
        gen.to_csv(args.output)
    elif args.format == "lua":
        gen.to_lua(args.output)
    elif args.format == "rpp":
        gen.to_rpp_markers(args.output)

    print(
        f"Exportadas {len(gen.regions)} región(es) a {args.output} "
        f"(formato: {args.format})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
