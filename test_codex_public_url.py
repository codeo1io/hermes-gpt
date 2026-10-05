"""Focused tests for the Codex web-extraction network gate and fetch seam.

Pins rm-150: ``validate_public_url`` check-time resolution semantics (the
FULL DNS answer must be global — a mixed public+private answer, the classic
rebinding shape, is rejected as a whole; resolution is fresh on every call)
and the out-of-tree fetch seam contract pinned by
``codex_core.WEB_EXTRACT_SEAM_CONTRACT`` and docs/codex.md: the fetcher
receives exactly the validated URL and MUST refuse (or re-validate) every
redirect hop.
"""

from __future__ import annotations

import ipaddress
import typing
from pathlib import Path
from typing import Any

import pytest

import codex_core as core_module


PUBLIC = "93.184.216.34"  # example.com — global unicast
PRIVATE = "10.1.2.3"
META = "169.254.169.254"


def fake_resolver(answers: list[list[str]]):
    """Build a getaddrinfo stub whose successive calls return ``answers``.

    Each call resolves to one A record per address string in that answer —
    this is the rebinding mock: consecutive resolutions for the same name
    can return different address sets.
    """
    calls: list[tuple[str, int]] = []

    def getaddrinfo(host, port, *args, **kwargs):  # noqa: ANN002, ANN003
        calls.append((host, port))
        answer = answers[min(len(calls) - 1, len(answers) - 1)]
        return [
            (2, 1, 6, "", (address, port))
            for address in answer
        ]

    getaddrinfo.calls = calls  # type: ignore[attr-defined]
    return getaddrinfo


def make_core(web_extract=None) -> core_module.CodexToolCore:
    if web_extract is None:
        def web_extract(urls, limit):  # noqa: ANN001
            return {"url": urls[0], "chars": limit}

    return core_module.CodexToolCore(
        version="0.13.0",
        imports_ready=lambda: True,
        gateway_snapshot=lambda: {"gateway": {"running": True, "pid": 42}},
        gateway_diagnostics_callback=lambda: {"success": True, "warnings": []},
        vision_analyze=lambda path, prompt: {"path": path, "prompt": prompt},
        web_search=lambda query, limit: {"title": "Result", "url": "https://example.com"},
        web_extract=web_extract,
        cron_create_callback=lambda schedule, prompt, dry_run: {"ok": True},
        skill_create_callback=lambda name, content, dry_run: {"ok": True},
    )


# ---------------------------------------------------------------------------
# validate_public_url — literal and name-based rejection (no network)


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/",
        "http://10.0.0.8/",
        "http://192.168.1.4/",
        "http://172.16.9.9/",
        "http://100.64.0.1/",  # CGNAT shared range
        "http://169.254.169.254/latest/meta-data/",
        "http://[::1]/",
        "http://[fe80::1]/",
    ],
)
def test_nonpublic_literal_ips_are_blocked(url):
    with pytest.raises(PermissionError):
        core_module.validate_public_url(url)


def test_global_literal_ip_passes_without_dns():
    assert core_module.validate_public_url(f"https://{PUBLIC}/docs") == f"https://{PUBLIC}/docs"


@pytest.mark.parametrize(
    "url",
    ["http://localhost:8080/", "http://api.localhost/", "http://printer.local/"],
)
def test_local_names_are_blocked_without_resolution(url, monkeypatch):
    # These must be rejected by name, never by DNS answer: prove no resolver
    # is consulted at all.
    def explode(*args, **kwargs):
        raise AssertionError("resolver must not be consulted for local names")

    monkeypatch.setattr(core_module.socket, "getaddrinfo", explode)
    with pytest.raises(PermissionError):
        core_module.validate_public_url(url)


@pytest.mark.parametrize(
    "url",
    [
        "ftp://example.com/file",
        "file:///etc/passwd",
        "https://user:secretpw@example.com/",
        "https:///path",
        "not a url",
    ],
)
def test_non_http_credentialed_and_hostless_urls_are_rejected(url):
    with pytest.raises((ValueError, PermissionError)):
        core_module.validate_public_url(url)


def test_private_network_env_override_is_the_only_escape_hatch(monkeypatch):
    with pytest.raises(PermissionError):
        core_module.validate_public_url(f"http://{PRIVATE}/")
    monkeypatch.setenv(core_module.ALLOW_PRIVATE_NETWORK_ENV, "1")
    assert core_module.validate_public_url(f"http://{PRIVATE}/") == f"http://{PRIVATE}/"


# ---------------------------------------------------------------------------
# check-time resolution semantics (rebinding mock resolver)


def test_resolution_is_fresh_on_every_call_no_cross_call_caching(monkeypatch):
    resolver = fake_resolver([[PUBLIC], [PRIVATE]])
    monkeypatch.setattr(core_module.socket, "getaddrinfo", resolver)

    assert core_module.validate_public_url("https://rebind.example/") == "https://rebind.example/"
    # The DNS answer flipped (rebinding between validation and a later fetch):
    # a later validation resolves FRESH and must see the new answer.
    with pytest.raises(PermissionError):
        core_module.validate_public_url("https://rebind.example/")
    assert resolver.calls == [("rebind.example", 443), ("rebind.example", 443)]


def test_mixed_public_private_answer_is_rejected_as_a_whole(monkeypatch):
    # The classic rebinding shape at check time: one public + one private A
    # record. The gate checks EVERY address; it must not sample.
    monkeypatch.setattr(core_module.socket, "getaddrinfo", fake_resolver([[PUBLIC, PRIVATE]]))
    with pytest.raises(PermissionError):
        core_module.validate_public_url("https://mixed.example/")


def test_multi_public_answer_passes(monkeypatch):
    monkeypatch.setattr(
        core_module.socket, "getaddrinfo", fake_resolver([[PUBLIC, "2606:2800:220:1::1"]])
    )
    assert core_module.validate_public_url("https://multi.example/x") == "https://multi.example/x"


def test_unresolvable_host_raises_a_clean_value_error(monkeypatch):
    def gaierror(*args, **kwargs):
        raise core_module.socket.gaierror("name or service not known")

    monkeypatch.setattr(core_module.socket, "getaddrinfo", gaierror)
    with pytest.raises(ValueError, match="could not be resolved safely"):
        core_module.validate_public_url("https://nonexistent.invalid/")


def test_resolver_uses_the_url_port_https_default(monkeypatch):
    resolver = fake_resolver([[PUBLIC]])
    monkeypatch.setattr(core_module.socket, "getaddrinfo", resolver)
    core_module.validate_public_url("https://example.com:8443/x")
    core_module.validate_public_url("https://example.com/x")
    assert [port for _, port in resolver.calls] == [8443, 443]


def test_all_addresses_are_checked_as_ip_objects(monkeypatch):
    seen: list[str] = []

    original = ipaddress.ip_address

    def spy(value):
        seen.append(str(value))
        return original(value)

    monkeypatch.setattr(core_module.ipaddress, "ip_address", spy)
    monkeypatch.setattr(core_module.socket, "getaddrinfo", fake_resolver([[PUBLIC, PRIVATE]]))
    with pytest.raises(PermissionError):
        core_module.validate_public_url("https://both.example/")
    assert set(seen) >= {PUBLIC, PRIVATE}


# ---------------------------------------------------------------------------
# the fetch seam: exact call shape, gate ordering, limit clamping


def test_extract_page_hands_the_seam_exactly_the_validated_url(monkeypatch):
    calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []

    def spy_web_extract(*args, **kwargs):
        calls.append((args, kwargs))
        return {"content": "ok"}

    monkeypatch.setattr(
        core_module.socket, "getaddrinfo", fake_resolver([[PUBLIC]])
    )
    tool = make_core(spy_web_extract)
    monkeypatch.setenv(core_module.ENABLE_CODEX_ENV, "1")
    monkeypatch.setenv(core_module.ENABLE_MCP_ENV, "1")
    monkeypatch.setenv(core_module.ENABLE_WEB_ENV, "1")

    result = tool.extract_page("https://seam.example/page", 2000)

    assert result["ok"] is True
    assert result["url"] == "https://seam.example/page"
    # The seam receives exactly one positional call: (list-of-validated-url,
    # clamped-limit). No extra URLs, no kwargs, exactly once.
    assert len(calls) == 1
    assert calls[0] == ((["https://seam.example/page"], 2000), {})


def test_seam_is_never_called_when_the_gate_blocks(monkeypatch):
    called = False

    def spy_web_extract(*args, **kwargs):
        nonlocal called
        called = True
        return {}

    tool = make_core(spy_web_extract)
    monkeypatch.setenv(core_module.ENABLE_CODEX_ENV, "1")
    monkeypatch.setenv(core_module.ENABLE_MCP_ENV, "1")
    monkeypatch.setenv(core_module.ENABLE_WEB_ENV, "1")

    result = tool.extract_page(f"http://{META}/latest/meta-data/")

    assert result["ok"] is False
    assert result["error"]["code"] == "URL_BLOCKED"
    assert called is False


@pytest.mark.parametrize(
    "requested,expected",
    [(1, 500), (2000, 2000), (10_000_000, core_module.MAX_EXTRACT_CHARS)],
)
def test_seam_limit_is_clamped_to_the_contract_range(requested, expected, monkeypatch):
    limits: list[int] = []

    def spy_web_extract(urls, limit):
        limits.append(limit)
        return {}

    monkeypatch.setattr(core_module.socket, "getaddrinfo", fake_resolver([[PUBLIC]]))
    tool = make_core(spy_web_extract)
    monkeypatch.setenv(core_module.ENABLE_CODEX_ENV, "1")
    monkeypatch.setenv(core_module.ENABLE_MCP_ENV, "1")
    monkeypatch.setenv(core_module.ENABLE_WEB_ENV, "1")

    assert tool.extract_page("https://clamp.example/x", requested)["ok"] is True
    assert limits == [expected]


# ---------------------------------------------------------------------------
# the seam contract itself (fails if the seam silently changes)


def test_web_extract_seam_contract_constant_pins_the_fetcher_duties():
    contract = core_module.WEB_EXTRACT_SEAM_CONTRACT
    # The contract must keep stating, in MUST language, that the fetcher
    # fetches only the validated URL and refuses/re-validates redirect hops
    # (the rebinding/redirect escape from the in-tree gate).
    assert "MUST" in contract
    assert "exactly the validated URL" in contract
    assert "redirect" in contract
    assert "re-validat" in contract
    assert "rebinding" in contract
    # And that changing it is a documented, test-visible event.
    assert "test_codex_public_url.py" in contract


def test_seam_field_signature_is_pinned():
    hints = typing.get_type_hints(core_module.CodexToolCore)
    assert hints["web_extract"] == typing.Callable[[list[str], int], Any]


def test_docs_state_the_seam_contract():
    text = Path("docs/codex.md").read_text(encoding="utf-8")
    assert "Fetch seam contract" in text
    assert "WEB_EXTRACT_SEAM_CONTRACT" in text
    assert "redirect hop" in text
    assert "DNS rebinding" in text


def test_extract_page_documents_the_seam_in_source():
    source = Path(core_module.__file__).read_text(encoding="utf-8")
    assert "WEB_EXTRACT_SEAM_CONTRACT" in source


def test_redaction_still_applies_to_seam_output(monkeypatch):
    monkeypatch.setattr(core_module.socket, "getaddrinfo", fake_resolver([[PUBLIC]]))

    def leaky_web_extract(urls, limit):
        return {"content": "Authorization: Bearer abcdefghijkl.mnopqrstuv.wxzy"}

    tool = make_core(leaky_web_extract)
    monkeypatch.setenv(core_module.ENABLE_CODEX_ENV, "1")
    monkeypatch.setenv(core_module.ENABLE_MCP_ENV, "1")
    monkeypatch.setenv(core_module.ENABLE_WEB_ENV, "1")

    result = tool.extract_page("https://leaky.example/x")
    assert result["ok"] is True
    assert "[REDACTED]" in str(result)
    assert "abcdefghijkl.mnopqrstuv.wxzy" not in str(result)
