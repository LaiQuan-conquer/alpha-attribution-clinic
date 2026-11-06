"""
Tests for CLI functionality.
CLI功能测试。
"""

import pytest
from click.testing import CliRunner

from alpha_attribution_clinic.cli import main


class TestCLI:
    """Tests for CLI commands."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_main_help(self, runner):
        """Test main help displays."""
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Alpha Attribution Clinic" in result.output

    def test_inject_command(self, runner):
        """Test inject command runs."""
        result = runner.invoke(main, ["inject", "--type", "lookahead"])
        assert result.exit_code == 0
        assert "Injection complete" in result.output

    def test_inject_all_types(self, runner):
        """Test injecting all anti-patterns."""
        result = runner.invoke(main, ["inject", "--type", "all"])
        assert result.exit_code == 0

    def test_detect_command(self, runner):
        """Test detect command runs."""
        result = runner.invoke(main, ["detect"])
        assert result.exit_code == 0
        assert "Detection Summary" in result.output or "summary" in result.output.lower()

    def test_detect_markdown_format(self, runner):
        """Test detect with markdown output."""
        result = runner.invoke(main, ["detect", "--format", "markdown"])
        assert result.exit_code == 0
        assert "Detection Report" in result.output

    def test_demo_command(self, runner):
        """Test demo command runs full pipeline."""
        result = runner.invoke(main, ["demo"])
        assert result.exit_code == 0
        assert "Demo complete" in result.output
        assert "Lookahead bias injected" in result.output

    def test_demo_verbose(self, runner):
        """Test demo with verbose flag."""
        result = runner.invoke(main, ["demo", "--verbose"])
        assert result.exit_code == 0

    def test_version(self, runner):
        """Test version flag."""
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output
