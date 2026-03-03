"""Tests for rrg.cli — command-line interface."""

import os
import tempfile

from rrg.cli import main


class TestCLI:
    def test_template_csv_output(self):
        with tempfile.NamedTemporaryFile(
            suffix=".csv", delete=False
        ) as tmp:
            path = tmp.name

        try:
            rc = main(["--template", "song", "--format", "csv", "-o", path])
            assert rc == 0
            with open(path, encoding="utf-8") as fh:
                content = fh.read()
            assert "Intro" in content
        finally:
            os.unlink(path)

    def test_template_lua_output(self):
        with tempfile.NamedTemporaryFile(
            suffix=".lua", delete=False
        ) as tmp:
            path = tmp.name

        try:
            rc = main(["--template", "song", "--format", "lua", "-o", path])
            assert rc == 0
            with open(path, encoding="utf-8") as fh:
                content = fh.read()
            assert "reaper.AddProjectMarker2" in content
        finally:
            os.unlink(path)

    def test_csv_input(self):
        csv_path = os.path.join(
            os.path.dirname(__file__), "..", "examples", "song_structure.csv"
        )
        with tempfile.NamedTemporaryFile(
            suffix=".csv", delete=False
        ) as tmp:
            out_path = tmp.name

        try:
            rc = main(["--csv", csv_path, "--format", "csv", "-o", out_path])
            assert rc == 0
        finally:
            os.unlink(out_path)

    def test_missing_csv_file(self):
        rc = main(["--csv", "/nonexistent.csv", "-o", "/tmp/out.csv"])
        assert rc == 1

    def test_rpp_format(self):
        with tempfile.NamedTemporaryFile(
            suffix=".txt", delete=False
        ) as tmp:
            path = tmp.name

        try:
            rc = main(["--template", "podcast", "--format", "rpp", "-o", path])
            assert rc == 0
            with open(path, encoding="utf-8") as fh:
                content = fh.read()
            assert "MARKER" in content
        finally:
            os.unlink(path)
