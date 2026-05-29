from reconbot.utils.normalize import (
    dedupe_sorted,
    hostnames_from_urls,
    http_urls,
    non_empty_strings,
    normalize_domain,
    normalize_url,
    safe_filename,
    strip_value,
)


def test_strip_value_strips_whitespace() -> None:
    assert strip_value("  value\n") == "value"


def test_non_empty_strings_strips_and_filters_empty_values() -> None:
    assert non_empty_strings([" a ", "", "  ", "b"]) == ["a", "b"]


def test_dedupe_sorted_strips_filters_and_sorts() -> None:
    assert dedupe_sorted(["b", " a ", "b", ""]) == ["a", "b"]


def test_normalize_domain_lowercases_and_removes_trailing_dot() -> None:
    assert normalize_domain(" EXAMPLE.COM. ") == "example.com"


def test_normalize_url_lowercases_and_removes_trailing_slash() -> None:
    assert normalize_url(" HTTPS://Example.com/Path/ ") == "https://example.com/path"


def test_http_urls_filters_normalizes_deduplicates_and_sorts() -> None:
    values = ["https://b.example.com/", "ftp://x", "HTTP://A.EXAMPLE.COM", "https://b.example.com"]

    assert http_urls(values) == ["http://a.example.com", "https://b.example.com"]


def test_hostnames_from_urls_extracts_deduplicated_sorted_hosts() -> None:
    urls = ["https://b.example.com/path", "not a url", "http://a.example.com", "https://b.example.com"]

    assert hostnames_from_urls(urls) == ["a.example.com", "b.example.com"]


def test_safe_filename_removes_unsafe_characters() -> None:
    assert safe_filename(" Example Domain.com/../../x ") == "example-domain.com-..-..-x"
    assert safe_filename(" !!! ", default="fallback") == "fallback"
