"""
Command-line interface for alpha-attribution-clinic.
alpha-attribution-clinic 命令行接口。

Usage:
    clinic inject --type lookahead --output dirty_data.csv
    clinic detect --input dirty_data.csv --output report.json
    clinic report --input report.json --format markdown
    clinic demo  # Run full inject -> detect -> report pipeline
"""

import json
import sys
from pathlib import Path

import click
import pandas as pd

from . import fixtures
from . import injectors
from . import detectors


@click.group()
@click.version_option()
def main():
    """
    Alpha Attribution Clinic - Bad Experiment Diagnosis Toolkit.

    ⚠️ TEACHING/DIAGNOSIS ONLY - No investment advice.
    仅用于教学/诊断 - 无投资建议。
    """
    pass


@main.command()
@click.option(
    "--type", "-t",
    type=click.Choice(["lookahead", "leakage", "survivorship", "cost_blind", "all"]),
    default="all",
    help="Type of anti-pattern to inject",
)
@click.option(
    "--output", "-o",
    type=click.Path(),
    default=None,
    help="Output CSV file path",
)
@click.option(
    "--seed", "-s",
    type=int,
    default=42,
    help="Random seed for reproducibility",
)
def inject(type: str, output: str | None, seed: int):
    """
    Inject anti-patterns into synthetic data.
    向合成数据注入反模式。
    """
    click.echo(f"Generating synthetic data with seed={seed}...")

    if type == "survivorship":
        data, delist_info = fixtures.generate_universe_with_delistings(
            n_assets=10, n_days=100, seed=seed
        )
    else:
        data = fixtures.generate_aligned_bars(n_assets=5, n_days=100, seed=seed)
        delist_info = None

    injectors_to_run = []
    if type == "all":
        injectors_to_run = ["lookahead", "leakage", "cost_blind"]
    elif type != "survivorship":
        injectors_to_run = [type]

    for inj_type in injectors_to_run:
        click.echo(f"Injecting {inj_type} bias...")
        if inj_type == "lookahead":
            injector = injectors.LookaheadInjector(lookahead_days=1)
            data = injector.inject(data)
        elif inj_type == "leakage":
            injector = injectors.LeakageInjector(leakage_type="close_for_open")
            data = injector.inject(data)
        elif inj_type == "cost_blind":
            injector = injectors.CostBlindInjector()
            data = injector.inject(data)

    if type == "survivorship":
        click.echo("Injecting survivorship bias...")
        injector = injectors.SurvivorshipInjector()
        data = injector.inject(data, delist_info=delist_info)
        click.echo(f"  Removed {len(injector._removed_assets)} delisted assets")

    if output:
        data.to_csv(output)
        click.echo(f"Saved to {output}")
    else:
        click.echo("\nInjected data preview:")
        click.echo(data.head(10).to_string())

    click.echo("\n✅ Injection complete")


@main.command()
@click.option(
    "--input", "-i",
    type=click.Path(exists=True),
    default=None,
    help="Input CSV file with potentially biased data",
)
@click.option(
    "--output", "-o",
    type=click.Path(),
    default=None,
    help="Output JSON report path",
)
@click.option(
    "--format", "-f",
    type=click.Choice(["json", "markdown", "summary"]),
    default="summary",
    help="Output format",
)
def detect(input: str | None, output: str | None, format: str):
    """
    Detect anti-patterns in data.
    检测数据中的反模式。
    """
    if input:
        click.echo(f"Loading data from {input}...")
        data = pd.read_csv(input, parse_dates=["date"])
        data = data.set_index(["date", "asset_id"])
    else:
        click.echo("No input provided, generating demo data with injections...")
        data = fixtures.generate_aligned_bars(n_assets=5, n_days=100, seed=42)
        injector = injectors.LookaheadInjector(lookahead_days=1)
        data = injector.inject(data)
        injector = injectors.LeakageInjector(leakage_type="close_for_open")
        data = injector.inject(data)
        injector = injectors.CostBlindInjector()
        data = injector.inject(data)

    click.echo("Running detectors...")
    report = detectors.generate_report(data)

    if format == "json":
        result = report.to_json()
    elif format == "markdown":
        result = report.to_markdown()
    else:
        n_issues = report.summary.get("issues_detected", 0)
        triggered = report.summary.get("detectors_triggered", [])
        result = f"""
Detection Summary / 检测摘要
============================
Total checks: {report.summary.get('total_checks', 0)}
Issues detected: {n_issues}
Clean: {report.summary.get('issues_clean', 0)}

{"⚠️ Issues found: " + ", ".join(triggered) if triggered else "✅ No issues detected"}
"""

    if output:
        Path(output).write_text(result)
        click.echo(f"Report saved to {output}")
    else:
        click.echo(result)


@main.command()
@click.option(
    "--input", "-i",
    type=click.Path(exists=True),
    required=True,
    help="Input JSON report path",
)
@click.option(
    "--format", "-f",
    type=click.Choice(["markdown", "json", "html"]),
    default="markdown",
    help="Output format",
)
def report(input: str, format: str):
    """
    Convert detection report to different formats.
    将检测报告转换为不同格式。
    """
    with open(input) as f:
        data = json.load(f)

    click.echo(f"Loaded report from {input}")

    if format == "json":
        click.echo(json.dumps(data, indent=2))
    elif format == "markdown":
        report_obj = detectors.DetectionReport(
            timestamp=data.get("timestamp", ""),
            summary=data.get("summary", {}),
        )
        for name, result_data in data.get("results", {}).items():
            result = detectors.base.DetectionResult(**result_data)
            report_obj.results[name] = result
        click.echo(report_obj.to_markdown())
    else:
        click.echo("HTML format not yet implemented")


@main.command()
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Show detailed output",
)
def demo(verbose: bool):
    """
    Run full demo: inject -> detect -> report.
    运行完整演示：注入 -> 检测 -> 报告。
    """
    click.echo("=" * 60)
    click.echo("Alpha Attribution Clinic - Demo / 演示")
    click.echo("=" * 60)
    click.echo()
    click.echo("⚠️ TEACHING/DIAGNOSIS ONLY - No investment advice")
    click.echo("   仅用于教学/诊断 - 无投资建议")
    click.echo()

    click.echo("Step 1: Generate clean synthetic data...")
    clean_data = fixtures.generate_aligned_bars(n_assets=5, n_days=100, seed=42)
    click.echo(f"  Generated {len(clean_data)} rows for 5 assets over 100 days")

    click.echo("\nStep 2: Inject anti-patterns...")

    dirty_data = clean_data.copy()
    la_injector = injectors.LookaheadInjector(lookahead_days=1)
    dirty_data = la_injector.inject(dirty_data)
    click.echo("  ✓ Lookahead bias injected")

    le_injector = injectors.LeakageInjector(leakage_type="close_for_open")
    dirty_data = le_injector.inject(dirty_data)
    click.echo("  ✓ Data leakage injected")

    cb_injector = injectors.CostBlindInjector()
    dirty_data = cb_injector.inject(dirty_data)
    click.echo("  ✓ Cost-blind bias injected")

    click.echo("\nStep 3: Run detectors...")
    report_obj = detectors.generate_report(dirty_data)

    click.echo("\nStep 4: Generate report...")
    click.echo()
    click.echo(report_obj.to_markdown())

    click.echo("\n" + "=" * 60)
    click.echo("Demo complete! / 演示完成！")
    click.echo("=" * 60)


if __name__ == "__main__":
    main()
