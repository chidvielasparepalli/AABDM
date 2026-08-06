"""Calendar provider interface.

Abstraction over real calendar sync (Google/Outlook). The internal adapter
uses the meetings table alone (today's behavior); external adapters add
availability + invite delivery.

Timezone contract: all slots are timezone-aware datetimes (UTC or explicit
offset). Conflicts are the adapter's job — a slot must never double-book.
"""

from datetime import datetime
from typing import Protocol, runtime_checkable

from .common import Capability, ProviderResult


@runtime_checkable
class CalendarProvider(Capability, Protocol):
    def list_slots(self, window_start: datetime, window_end: datetime) -> list[dict]:
        """Return available slots [{start, end, tz}]. Timezone-aware."""
        ...

    def book(self, slot_start: datetime, title: str, attendee_email: str) -> ProviderResult:
        """Book a slot; deliver invite. Returns ProviderResult (ok + booking id)."""
        ...

    def cancel(self, booking_id: str) -> ProviderResult:
        """Cancel a booking."""
        ...

    def reschedule(self, booking_id: str, new_start: datetime) -> ProviderResult:
        """Move a booking to a new slot."""
        ...
