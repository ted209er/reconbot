from pathlib import Path

import pytest
from pytest import MonkeyPatch

from reconbot import doctor, main
from reconbot.workspaces import ensure_workspace


def test_check_python_is_healthy_on_supported_runtime() -> None:
    result = doctor.check_python()

    assert result.name == "Python"
    assert result.status == doctor.HealthStatus.HEALTHY
    assert "Python" in result.message


def test_check_config_loads_packaged_default() -> None:
    result = doctor.check_config()

    assert result.status == doctor.HealthStatus.HEALTHY
    assert "Packaged default config" in result.message


def test_check_sqlite_is_healthy() -> None:
    result = doctor.check_sqlite()

    assert result.status == doctor.HealthStatus.HEALTHY
    assert "SQLite" in result.message


def test_check_workspace_warns_when_missing(tmp_path: Path) -> None:
    result = doctor.check_workspace(tmp_path / "missing")

    assert result.status == doctor.HealthStatus.WARNINGS
    assert "does not exist yet" in result.message


def test_check_workspace_errors_when_path_is_file(tmp_path: Path) -> None:
    workspace_file = tmp_path / "workspace"
    workspace_file.write_text("not a directory", encoding="utf-8")

    result = doctor.check_workspace(workspace_file)

    assert result.status == doctor.HealthStatus.ERROR
    assert "not a directory" in result.message


def test_check_workspace_is_healthy_for_standard_layout(tmp_path: Path) -> None:
    paths = ensure_workspace(tmp_path / "workspace")

    result = doctor.check_workspace(paths.root)

    assert result.status == doctor.HealthStatus.HEALTHY
    assert str(paths.root) in result.message


def test_check_tools_warns_for_missing_tools(monkeypatch: MonkeyPatch) -> None:
    def fake_which(tool_name: str) -> str | None:
        return None if tool_name == "gau" else tool_name

    monkeypatch.setattr(doctor, "which", fake_which)

    result = doctor.check_tools(["subfinder", "gau"])

    assert result.status == doctor.HealthStatus.WARNINGS
    assert result.message == "Missing tool(s) on PATH: gau"


def test_check_tools_is_healthy_when_all_tools_are_found(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(doctor, "which", lambda tool_name: f"/usr/bin/{tool_name}")

    result = doctor.check_tools(["subfinder", "gau"])

    assert result.status == doctor.HealthStatus.HEALTHY


def test_format_doctor_output_includes_overall_status() -> None:
    output = doctor.format_doctor_output(
        [
            doctor.CheckResult("Python", doctor.HealthStatus.HEALTHY, "ok"),
            doctor.CheckResult("Tools", doctor.HealthStatus.WARNINGS, "missing"),
        ]
    )

    assert "[HEALTHY] Python: ok" in output
    assert "[WARNINGS] Tools: missing" in output
    assert output.endswith("Result: WARNINGS")


def test_main_doctor_returns_warning_exit_code(
    monkeypatch: MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        main,
        "run_doctor",
        lambda workspace_path=None: [
            doctor.CheckResult("Tools", doctor.HealthStatus.WARNINGS, "missing")
        ],
    )

    exit_code = main.main(["doctor"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Result: WARNINGS" in output


def test_main_doctor_passes_workspace(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    calls: list[Path | None] = []

    def fake_run_doctor(workspace_path: Path | None = None) -> list[doctor.CheckResult]:
        calls.append(workspace_path)
        return [doctor.CheckResult("Python", doctor.HealthStatus.HEALTHY, "ok")]

    monkeypatch.setattr(main, "run_doctor", fake_run_doctor)

    exit_code = main.main(["doctor", "--workspace", str(tmp_path / "workspace")])

    assert exit_code == 0
    assert calls == [tmp_path / "workspace"]
