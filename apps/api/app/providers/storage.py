"""Storage provider interface.

Abstraction over blob storage (recordings, PDFs, case-study uploads, exports).
The local adapter writes under `storage/`; cloud adapters (S3/GCS/Azure) add
presigning, versioning, lifecycle.
"""

from typing import Protocol, runtime_checkable

from .common import Capability, ProviderResult


@runtime_checkable
class StorageProvider(Capability, Protocol):
    def put(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> ProviderResult:
        """Write a blob. Returns ProviderResult (ok + uri)."""
        ...

    def get(self, uri: str) -> bytes:
        """Read a blob. Raises ProviderError on missing."""
        ...

    def delete(self, uri: str) -> ProviderResult:
        """Delete a blob."""
        ...

    def presign(self, uri: str, ttl_seconds: int = 3600) -> str:
        """Return a temporary signed URL for the UI/KB. Local adapter may return a file URL."""
        ...
