import pytest

from reconbot.tools import detection


def test_find_missing_tools_returns_missing_binaries(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_which(tool_name: str) -> str | None:
        return f"/usr/bin/{tool_name}" if tool_name == "present" else None

    monkeypatch.setattr(detection, "which", fake_which)

    assert detection.find_missing_tools(["present", "missing"]) == ["missing"]


def test_validate_required_tools_allows_present_binaries(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_which(tool_name: str) -> str:
        return f"/usr/bin/{tool_name}"

    monkeypatch.setattr(detection, "which", fake_which)

    detection.validate_required_tools(["subfinder", "httpx", "gau"])


def test_validate_required_tools_raises_clear_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_which(tool_name: str) -> str | None:
        return None if tool_name in {"httpx", "gau"} else f"/usr/bin/{tool_name}"

    monkeypatch.setattr(detection, "which", fake_which)

    with pytest.raises(detection.MissingExternalToolsError) as exc_info:
        detection.validate_required_tools(["subfinder", "httpx", "gau"])

    message = str(exc_info.value)
    assert "Missing required external tool(s): gau, httpx" in message
    assert "available on PATH" in message
