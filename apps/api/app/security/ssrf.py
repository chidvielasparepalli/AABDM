"""SSRF-safe URL validation.

Rejects URLs that would make the server fetch internal resources: schemes
other than http/https, and any hostname (or DNS result) resolving to a
private, link-local, loopback, or cloud-metadata address.

Enforced before any outbound fetch in the research engine — `fetch_site`
and `page_speed` both call `validate_url`.

DNS rebinding note: `socket.getaddrinfo` resolves at validation time; a
host whose address changes between validation and connection is a residual
risk. The redirect cap in `fetch_site` bounds the blast radius further.
"""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

from . import errors

# Blocks of metadata endpoints and internal services.
_PRIVATE_NETS = (
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),  # link-local, cloud metadata
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("fd00::/8"),
    ipaddress.ip_network("fe80::/10"),
)

_MAX_REDIRECTS = 3


def validate_url(url: str) -> str:
    """Return a normalized http(s) URL, or raise SSRFBlocked.

    Accepts bare hostnames (e.g. "acme.com"); normalizes to https.
    """
    candidate = url if "://" in url else f"https://{url}"
    parsed = urlparse(candidate)

    if parsed.scheme not in ("http", "https"):
        raise errors.SSrfBlocked(f"scheme '{parsed.scheme}' not allowed")

    host = parsed.hostname
    if not host:
        raise errors.SSrfBlocked("URL has no host")

    # Localhost by name — beats DNS resolution by covering
    # "localhost", "localhost.localdomain", and bare IP literals.
    if _is_ip_address(host):
        _assert_public_ip(host)
    else:
        _assert_public_name(host)

    return candidate


def _is_ip_address(host: str) -> bool:
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        return False


def _assert_public_ip(host: str) -> None:
    addr = ipaddress.ip_address(host)
    if addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved or addr.is_multicast:
        raise errors.SSrfBlocked(f"host {host} resolves to a non-public address")


def _assert_public_name(host: str) -> None:
    lowered = host.lower()
    if lowered in ("localhost", "localhost.localdomain"):
        raise errors.SSrfBlocked("localhost is not allowed")

    try:
        infos = socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise errors.SSrfBlocked(f"host {host} does not resolve") from exc

    for info in infos:
        addr = ipaddress.ip_address(info[4][0])
        if _is_private(addr):
            raise errors.SSrfBlocked(f"host {host} resolves to a non-public address")


def _is_private(addr: ipaddress._BaseAddress) -> bool:
    return any(addr in net for net in _PRIVATE_NETS) or addr.is_loopback or addr.is_link_local


def max_redirects() -> int:
    """Redirect cap applied by callers (also lives in module scope)."""
    return _MAX_REDIRECTS
