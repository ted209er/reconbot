from pathlib import Path

from reconbot.models import ReconReport, ReconTarget, ToolResult


def test_recon_report_tracks_results_and_completion() -> None:
    target = ReconTarget(domain="example.com", config_path=Path("config.yaml"))
    report = ReconReport(target=target)

    report.add_result(ToolResult(name="placeholder", success=True))
    report.complete()

    assert report.target.domain == "example.com"
    assert report.results[0].name == "placeholder"
    assert report.successful is True
    assert report.finished_at is not None


def test_recon_report_successful_reflects_failed_result() -> None:
    target = ReconTarget(domain="example.com", config_path=Path("config.yaml"))
    report = ReconReport(target=target)

    report.add_result(ToolResult(name="placeholder", success=False, return_code=1))

    assert report.successful is False
