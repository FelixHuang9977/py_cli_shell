#!/usr/bin/env python3
import os
import click
import pytest
import json
from datetime import datetime


class Context:
    def __init__(self):
        self.verbose = False
        self.test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "testcase")
        # 添加 logs 目錄路徑
        self.logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")


class TestResultCollector:
    def __init__(self):
        self.passed = []
        self.failed = []
        self.errors = []
        self.skipped = []
        self.start_time = None
        self.end_time = None

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(self, item, call):
        outcome = yield
        report = outcome.get_result()
        
        if report.when == "call":
            test_name = item.nodeid
            if report.passed:
                self.passed.append(test_name)
            elif report.failed:
                if report.outcome == "failed":
                    self.failed.append((test_name, str(report.longrepr)))
                else:
                    self.errors.append((test_name, str(report.longrepr)))
            elif report.skipped:
                self.skipped.append((test_name, str(report.longrepr)))

    def pytest_sessionstart(self):
        self.start_time = datetime.now()

    def pytest_sessionfinish(self):
        self.end_time = datetime.now()

    def generate_summary(self):
        duration = self.end_time - self.start_time if self.start_time and self.end_time else None
        
        summary = []
        summary.append("Test Execution Summary")
        summary.append("=" * 80)
        summary.append(f"Execution Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        if duration:
            summary.append(f"Duration: {duration}")
        summary.append("-" * 80)
        
        # 統計資訊
        summary.append("\nTest Statistics:")
        summary.append(f"Total Tests: {len(self.passed) + len(self.failed) + len(self.errors) + len(self.skipped)}")
        summary.append(f"Passed: {len(self.passed)}")
        summary.append(f"Failed: {len(self.failed)}")
        summary.append(f"Errors: {len(self.errors)}")
        summary.append(f"Skipped: {len(self.skipped)}")
        
        # 詳細結果
        if self.passed:
            summary.append("\nPassed Tests:")
            summary.append("-" * 40)
            for test in self.passed:
                summary.append(f"✓ {test}")
        
        if self.failed:
            summary.append("\nFailed Tests:")
            summary.append("-" * 40)
            for test, error in self.failed:
                summary.append(f"✗ {test}")
                summary.append("Error Details:")
                summary.append(error)
                summary.append("-" * 40)
        
        if self.errors:
            summary.append("\nErrors:")
            summary.append("-" * 40)
            for test, error in self.errors:
                summary.append(f"! {test}")
                summary.append("Error Details:")
                summary.append(error)
                summary.append("-" * 40)
        
        if self.skipped:
            summary.append("\nSkipped Tests:")
            summary.append("-" * 40)
            for test, reason in self.skipped:
                summary.append(f"- {test}")
                summary.append(f"Reason: {reason}")
        
        return "\n".join(summary)


pass_context = click.make_pass_decorator(Context, ensure=True)


@click.group()
@click.option("--verbose", is_flag=True, help="Enable verbose mode.")
@click.option(
    "--test-dir",
    type=click.Path(exists=True),
    help="Directory containing test cases.",
)
@pass_context
def cli(ctx, verbose, test_dir):
    ctx.verbose = verbose
    if test_dir is not None:
        ctx.test_dir = test_dir
    # 確保 logs 目錄存在
    os.makedirs(ctx.logs_dir, exist_ok=True)
@cli.command()
@pass_context
def categories(ctx):
    """List all available test categories."""
    categories = []
    test_dir = ctx.test_dir
    
    for item in os.listdir(test_dir):
        item_path = os.path.join(test_dir, item)
        if os.path.isdir(item_path) and not item.startswith((".", "__", "logs", "config","docs")):
            categories.append(item)

    if not categories:
        click.echo("No test categories found.")
    else:
        click.echo("Available test categories:")
        for category in sorted(categories):
            click.echo(f"  - {category}")
@cli.command()
@pass_context
def config(ctx):
    """Show current configuration."""
    click.echo(f"Test directory: {ctx.test_dir}")
    click.echo(f"Verbose mode: {ctx.verbose}")
@cli.command()
@click.argument("category", required=False)
@pass_context
def list(ctx, category):
    """List available tests."""
    test_dir = ctx.test_dir
    if category:
        test_dir = os.path.join(test_dir, category)

    if not os.path.exists(test_dir):
        click.echo(f"Category '{category}' not found.")
        return

    for root, _, files in os.walk(test_dir):
        for file in files:
            if file.startswith("test_") and file.endswith(".py"):
                rel_path = os.path.relpath(os.path.join(root, file), ctx.test_dir)
                click.echo(f"{rel_path}")


@cli.command()
@click.argument("test_path")
@click.option("--stress", is_flag=True, help="Enable stress test mode")
@click.option("--junit-xml", type=str, help="Generate junit-xml format report")
@pass_context
def run(ctx, test_path, stress, junit_xml):
    """Run specified test."""
    test_path = os.path.join(ctx.test_dir, test_path)
    if not os.path.exists(test_path):
        click.echo(f"Test '{test_path}' not found.")
        return

    # 準備 pytest 參數
    args = [test_path]
    if ctx.verbose:
        args.append("-v")
    if stress:
        os.environ["STRESS_TEST"] = "1"
    if junit_xml:
        args.extend(["--junitxml", junit_xml])

    # 創建結果收集器
    collector = TestResultCollector()
    
    # 註冊 pytest 插件
    plugins = [collector]
    
    # 執行測試
    pytest.main(args, plugins=plugins)
    
    # 生成摘要報告
    summary = collector.generate_summary()
    
    # 創建摘要文件名稱
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    summary_file = os.path.join(ctx.logs_dir, f"test_summary_{timestamp}.txt")
    
    # 保存摘要
    with open(summary_file, 'w') as f:
        f.write(summary)
    
    click.echo(f"\nTest summary has been saved to: {summary_file}")


@cli.command()
@click.argument("output", type=click.Choice(["text", "json"]), default="text")
@pass_context
def show(ctx, output):
    """Show test results."""
    # TODO: Implement show command
    click.echo("Show command not implemented yet.")


if __name__ == "__main__":
    cli()
