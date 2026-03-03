"""Pruebas para rrg.generator — Modelo de región y RegionGenerator."""

import csv
import os
import tempfile

import pytest

from rrg.generator import Region, RegionGenerator, _format_time


# ── Modelo de región ────────────────────────────────────────────────────── #


class TestRegion:
    def test_basic_creation(self):
        r = Region("Verse", 10, 30)
        assert r.name == "Verse"
        assert r.start == 10.0
        assert r.end == 30.0
        assert r.color is None

    def test_length(self):
        r = Region("Chorus", 30, 75.5)
        assert r.length == pytest.approx(45.5)

    def test_negative_start_raises(self):
        with pytest.raises(ValueError, match="no negativos"):
            Region("Bad", -1, 5)

    def test_start_equals_end_raises(self):
        with pytest.raises(ValueError, match="debe ser anterior al fin"):
            Region("Bad", 10, 10)

    def test_start_after_end_raises(self):
        with pytest.raises(ValueError, match="debe ser anterior al fin"):
            Region("Bad", 20, 10)

    def test_reaper_color_default(self):
        r = Region("X", 0, 1)
        assert r.reaper_color() == 0

    def test_reaper_color_custom(self):
        r = Region("X", 0, 1, color=(255, 0, 0))
        # 255 | (0 << 8) | (0 << 16) | 0x1000000
        assert r.reaper_color() == 0x10000FF

    def test_equality(self):
        a = Region("A", 0, 10, (1, 2, 3))
        b = Region("A", 0, 10, (1, 2, 3))
        assert a == b

    def test_inequality(self):
        a = Region("A", 0, 10)
        b = Region("B", 0, 10)
        assert a != b


# ── RegionGenerator ─────────────────────────────────────────────────────── #


class TestRegionGenerator:
    def test_add_region(self):
        gen = RegionGenerator()
        r = gen.add_region("Intro", 0, 15)
        assert len(gen.regions) == 1
        assert r.name == "Intro"

    def test_clear(self):
        gen = RegionGenerator()
        gen.add_region("A", 0, 5)
        gen.clear()
        assert len(gen.regions) == 0

    def test_load_template_song(self):
        gen = RegionGenerator()
        gen.load_template("song")
        assert len(gen.regions) == 8
        assert gen.regions[0].name == "Intro"

    def test_load_template_podcast(self):
        gen = RegionGenerator()
        gen.load_template("podcast")
        assert len(gen.regions) == 5

    def test_load_template_unknown_raises(self):
        gen = RegionGenerator()
        with pytest.raises(ValueError, match="Plantilla desconocida"):
            gen.load_template("unknown")

    def test_load_csv(self):
        gen = RegionGenerator()
        csv_path = os.path.join(
            os.path.dirname(__file__), "..", "examples", "song_structure.csv"
        )
        gen.load_csv(csv_path)
        assert len(gen.regions) == 8
        assert gen.regions[0].name == "Intro"
        assert gen.regions[0].color == (100, 150, 255)

    def test_load_csv_without_color(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, newline=""
        ) as f:
            writer = csv.writer(f)
            writer.writerow(["name", "start", "end"])
            writer.writerow(["Part A", "0", "30"])
            writer.writerow(["Part B", "30", "60"])
            f.flush()
            path = f.name

        try:
            gen = RegionGenerator()
            gen.load_csv(path)
            assert len(gen.regions) == 2
            assert gen.regions[0].color is None
        finally:
            os.unlink(path)

    # ── Exportar: CSV ──────────────────────────────────────────────────── #

    def test_to_csv_creates_file(self):
        gen = RegionGenerator()
        gen.add_region("Intro", 0, 15)
        gen.add_region("Verse", 15, 45)

        with tempfile.NamedTemporaryFile(
            suffix=".csv", delete=False
        ) as tmp:
            path = tmp.name

        try:
            gen.to_csv(path)
            with open(path, encoding="utf-8") as fh:
                content = fh.read()
            assert "Intro" in content
            assert "Verse" in content
            assert "R1" in content
            assert "R2" in content
        finally:
            os.unlink(path)

    # ── Exportar: Lua ──────────────────────────────────────────────────── #

    def test_to_lua_creates_valid_script(self):
        gen = RegionGenerator()
        gen.add_region("Test", 0, 10, (255, 0, 0))

        with tempfile.NamedTemporaryFile(
            suffix=".lua", delete=False
        ) as tmp:
            path = tmp.name

        try:
            gen.to_lua(path)
            with open(path, encoding="utf-8") as fh:
                content = fh.read()
            assert "reaper.AddProjectMarker2" in content
            assert '"Test"' in content
            assert "Undo_BeginBlock" in content
            assert "Undo_EndBlock" in content
        finally:
            os.unlink(path)

    # ── Exportar: RPP ──────────────────────────────────────────────────── #

    def test_to_rpp_markers_creates_file(self):
        gen = RegionGenerator()
        gen.add_region("Intro", 0, 15)

        with tempfile.NamedTemporaryFile(
            suffix=".txt", delete=False
        ) as tmp:
            path = tmp.name

        try:
            gen.to_rpp_markers(path)
            with open(path, encoding="utf-8") as fh:
                content = fh.read()
            assert "MARKER" in content
            assert '"Intro"' in content
            # Una región genera un marcador de inicio y uno de fin
            assert content.count("MARKER") == 2
        finally:
            os.unlink(path)


# ── Ayudantes ───────────────────────────────────────────────────────────── #


class TestFormatTime:
    def test_zero(self):
        assert _format_time(0) == "0:00.000"

    def test_seconds_only(self):
        assert _format_time(30) == "0:30.000"

    def test_minutes_and_seconds(self):
        assert _format_time(90) == "1:30.000"

    def test_fractional_seconds(self):
        assert _format_time(61.5) == "1:01.500"
