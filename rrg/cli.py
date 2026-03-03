"""Command-line interface for RRG - REAPER Region Generator."""

import argparse
import sys

from rrg.generator import RegionGenerator


def main(argv=None):
    """Entry point for the ``rrg`` command."""
    parser = argparse.ArgumentParser(
        prog="rrg",
        description="RRG - REAPER Region Generator: create region files for REAPER.",
    )

    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--csv",
        metavar="FILE",
        help="Input CSV file with columns: name, start, end[, r, g, b]",
    )
    input_group.add_argument(
        "--template",
        choices=["song", "podcast"],
        help="Use a built-in template (song, podcast)",
    )

    parser.add_argument(
        "--format",
        choices=["csv", "lua", "rpp"],
        default="csv",
        help="Output format: csv (REAPER import), lua (ReaScript), rpp (RPP markers). Default: csv",
    )
    parser.add_argument(
        "-o",
        "--output",
        metavar="FILE",
        required=True,
        help="Output file path",
    )

    args = parser.parse_args(argv)

    gen = RegionGenerator()

    if args.csv:
        try:
            gen.load_csv(args.csv)
        except FileNotFoundError:
            print(f"Error: input file not found: {args.csv}", file=sys.stderr)
            return 1
        except Exception as exc:
            print(f"Error reading CSV: {exc}", file=sys.stderr)
            return 1
    else:
        gen.load_template(args.template)

    if not gen.regions:
        print("Warning: no regions to export.", file=sys.stderr)
        return 1

    if args.format == "csv":
        gen.to_csv(args.output)
    elif args.format == "lua":
        gen.to_lua(args.output)
    elif args.format == "rpp":
        gen.to_rpp_markers(args.output)

    print(
        f"Exported {len(gen.regions)} region(s) to {args.output} "
        f"(format: {args.format})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
