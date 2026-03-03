"""Core region model and generator logic for REAPER regions."""

import csv
import uuid


class Region:
    """Represents a single REAPER region with a name, time range, and color."""

    def __init__(self, name, start, end, color=None):
        """Create a Region.

        Args:
            name: Display name of the region.
            start: Start time in seconds.
            end: End time in seconds.
            color: Optional tuple of (r, g, b) integers 0-255.

        Raises:
            ValueError: If start >= end or times are negative.
        """
        if start < 0 or end < 0:
            raise ValueError("Region times must be non-negative")
        if start >= end:
            raise ValueError(
                f"Region start ({start}) must be before end ({end})"
            )
        self.name = name
        self.start = float(start)
        self.end = float(end)
        self.color = color

    @property
    def length(self):
        """Duration of the region in seconds."""
        return self.end - self.start

    def reaper_color(self):
        """Return the REAPER native color integer for this region.

        REAPER stores colors as ``(r | (g << 8) | (b << 16)) | 0x1000000``.
        Returns 0 (default color) when no color is set.
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
    """Builds a list of REAPER regions and exports them in various formats."""

    def __init__(self):
        self.regions = []

    def add_region(self, name, start, end, color=None):
        """Add a region to the generator.

        Args:
            name: Region name.
            start: Start time in seconds.
            end: End time in seconds.
            color: Optional (r, g, b) tuple.

        Returns:
            The created Region instance.
        """
        region = Region(name, start, end, color)
        self.regions.append(region)
        return region

    def clear(self):
        """Remove all regions."""
        self.regions.clear()

    # ---- Input helpers -------------------------------------------------- #

    def load_csv(self, filepath):
        """Load regions from a CSV file.

        Expected columns: ``name, start, end[, r, g, b]``

        Args:
            filepath: Path to the CSV file.
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
        """Load a built-in region template.

        Available templates:
            - ``song``: Standard pop/rock song structure.
            - ``podcast``: Simple podcast episode structure.

        Args:
            template_name: Name of the template.

        Raises:
            ValueError: If the template name is unknown.
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
                f"Unknown template '{template_name}'. "
                f"Available: {', '.join(sorted(templates))}"
            )

        for name, start, end, color in templates[template_name]:
            self.add_region(name, start, end, color)

    # ---- Output helpers ------------------------------------------------- #

    def to_csv(self, filepath):
        """Export regions as a tab-separated CSV file compatible with REAPER.

        The file can be imported via REAPER's Region/Marker Manager.

        Args:
            filepath: Destination file path.
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
        """Export regions as a Lua ReaScript that creates them inside REAPER.

        Users can run the generated ``.lua`` file from REAPER's Actions menu.

        Args:
            filepath: Destination file path.
        """
        lines = [
            "-- RRG: REAPER Region Generator",
            "-- Run this script inside REAPER to create regions.",
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
            'reaper.Undo_EndBlock("RRG: Create regions", -1)',
            "",
        ]
        with open(filepath, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines))

    def to_rpp_markers(self, filepath):
        """Export regions as RPP MARKER lines for inclusion in a .rpp file.

        Each region is represented as a pair of MARKER entries (start/end).

        Args:
            filepath: Destination file path.
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


# ---- Helpers ------------------------------------------------------------ #


def _format_time(seconds):
    """Format seconds as ``M:SS.mmm`` for REAPER CSV import."""
    minutes = int(seconds) // 60
    secs = seconds - minutes * 60
    return f"{minutes}:{secs:06.3f}"
