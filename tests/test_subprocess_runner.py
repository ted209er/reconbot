import sys
from pathlib import Path

from reconbot.utils.subprocess_runner import (
    MISSING_EXECUTABLE_RETURN_CODE,
    TIMEOUT_RETURN_CODE,
    run_command,
)


def test_run_command_success() -> None:
    result = run_command(
        "python-print",
        [sys.executable, "-c", "print('ok')"],
        timeout=5,
    )

    assert result.success is True
    assert result.return_code == 0
    assert result.output.strip() == "ok"
    assert result.error == ""


def test_run_command_timeout() -> None:
    result = run_command(
        "python-sleep",
        [sys.executable, "-c", "import time; time.sleep(2)"],
        timeout=0.1,
    )

    assert result.success is False
    assert result.return_code == TIMEOUT_RETURN_CODE
    assert "timed out" in result.error


def test_run_command_nonzero_exit_code() -> None:
    result = run_command(
        "python-fail",
        [sys.executable, "-c", "import sys; print('bad', file=sys.stderr); sys.exit(3)"],
        timeout=5,
    )

    assert result.success is False
    assert result.return_code == 3
    assert result.error.strip() == "bad"


def test_run_command_missing_executable() -> None:
    result = run_command(
        "missing",
        ["definitely-not-a-real-reconbot-command"],
        timeout=5,
    )

    assert result.success is False
    assert result.return_code == MISSING_EXECUTABLE_RETURN_CODE
    assert result.error


def test_run_command_supports_environment_and_cwd(tmp_path: Path) -> None:
    result = run_command(
        "python-env-cwd",
        [
            sys.executable,
            "-c",
            "import os, pathlib; print(os.environ['RECONBOT_TEST']); print(pathlib.Path.cwd())",
        ],
        cwd=tmp_path,
        env={"RECONBOT_TEST": "enabled"},
        timeout=5,
    )

    assert result.success is True
    assert result.output.splitlines() == ["enabled", str(tmp_path)]
