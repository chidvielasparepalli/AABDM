"""Unit tests for SSRF-safe URL validation.

Validates the allowlist/denylist: public http(s) passes, private/link-local/
metadata addresses and non-http schemes are blocked, and DNS-resolved
internal hosts are caught after resolution.
"""

import pytest

from app.security.errors import SSrfBlocked
from app.security.ssrf import validate_url


def test_public_url_passes():
    assert validate_url("https://example.com") == "https://example.com"
    assert validate_url("http://example.com/path?q=1") == "http://example.com/path?q=1"


def test_bare_hostname_normalized_to_https():
    assert validate_url("example.com") == "https://example.com"


def test_metadata_ipv4_blocked():
    with pytest.raises(SSrfBlocked):
        validate_url("http://169.254.169.254/latest/meta-data/")


def test_private_ipv4_blocked():
    for host in ("10.0.0.1", "172.16.0.5", "192.168.1.1", "127.0.0.1"):
        with pytest.raises(SSrfBlocked):
            validate_url(f"http://{host}/")


def test_ipv6_private_blocked():
    with pytest.raises(SSrfBlocked):
        validate_url("http://[fd00::1]/")


def test_non_http_scheme_blocked():
    for scheme in ("file", "ftp", "gopher", "redis", "smb"):
        with pytest.raises(SSrfBlocked):
            validate_url(f"{scheme}://example.com/x")


def test_localhost_name_blocked():
    with pytest.raises(SSrfBlocked):
        validate_url("http://localhost/admin")


def test_dns_resolves_to_private_host_blocked(monkeypatch):
    """A public-looking hostname whose DNS maps to a private IP is caught."""

    class FakeAddrInfo(tuple):
        # getaddrinfo entry: (family, type, proto, canonname, sockaddr)
        def __new__(cls, ip):
            return super().__new__(cls, (None, None, None, None, (ip, 0)))

    monkeypatch.setattr(
        "app.security.ssrf.socket.getaddrinfo",
        lambda host, port, proto=None: [FakeAddrInfo("10.0.0.42")],
    )
    with pytest.raises(SSrfBlocked):
        validate_url("http://internal.example.com/")


def test_dns_resolution_failure_blocked(monkeypatch):
    monkeypatch.setattr(
        "app.security.ssrf.socket.getaddrinfo",
        lambda host, port, proto=None: (_ for _ in ()).throw(__import__("socket").gaierror()),
    )
    with pytest.raises(SSrfBlocked):
        validate_url("http://nonexistent.invalid/")


def test_public_ip_parsed_as_literal():
    # 8.8.8.8 is a valid public IP literal — should pass validation
    assert validate_url("http://8.8.8.8/") == "http://8.8.8.8/"
