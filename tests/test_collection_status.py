from reconbot.collection_status import (
    CollectionState,
    CollectionStatus,
    RunCompleteness,
    determine_run_completeness,
    disabled_status,
    status_from_result,
)
from reconbot.models import ToolResult
from reconbot.utils.subprocess_runner import TIMEOUT_RETURN_CODE


def test_status_from_result_maps_success_and_zero_results() -> None:
    success = ToolResult(name="subfinder", success=True)

    assert status_from_result(
        source="subfinder",
        target="example.com",
        result=success,
        result_count=2,
    ).status == CollectionState.SUCCESS
    assert status_from_result(
        source="subfinder",
        target="example.com",
        result=success,
        result_count=0,
    ).status == CollectionState.ZERO_RESULTS


def test_status_from_result_maps_failure_timeout_and_concise_error() -> None:
    failure = ToolResult(
        name="gau",
        success=False,
        return_code=2,
        error="first line\nsecond line",
    )
    timeout = ToolResult(name="gau", success=False, return_code=TIMEOUT_RETURN_CODE)

    failed_status = status_from_result(
        source="gau",
        target="example.com",
        result=failure,
        result_count=0,
    )

    assert failed_status.status == CollectionState.FAILED
    assert failed_status.error_summary == "first line second line"
    assert status_from_result(
        source="gau",
        target="example.com",
        result=timeout,
        result_count=0,
    ).status == CollectionState.TIMED_OUT


def test_disabled_status_is_explicit() -> None:
    assert disabled_status(source="gowitness", target="example.com") == CollectionStatus(
        source="gowitness",
        target="example.com",
        status=CollectionState.DISABLED,
        result_count=0,
    )


def test_determine_run_completeness_ignores_disabled_sources() -> None:
    disabled = disabled_status(source="gowitness", target="example.com")
    success = CollectionStatus("subfinder", "example.com", CollectionState.SUCCESS, 2)
    failure = CollectionStatus("gau", "example.com", CollectionState.FAILED, 0)

    assert determine_run_completeness([disabled]) == RunCompleteness.COMPLETE
    assert determine_run_completeness([success, disabled]) == RunCompleteness.COMPLETE
    assert determine_run_completeness([success, failure]) == RunCompleteness.PARTIAL
    assert determine_run_completeness([failure]) == RunCompleteness.FAILED
