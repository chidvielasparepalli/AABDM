"""Meeting repo."""

from datetime import datetime, timezone

from ..models import Meeting
from .base import ModelRepository


class MeetingRepository(ModelRepository[Meeting]):
    model = Meeting

    def create(self, client_id: int, title: str, scheduled_at: datetime) -> Meeting:
        return self.add(client_id=client_id, title=title, scheduled_at=scheduled_at)

    def list(self, upcoming_only: bool, limit: int, offset: int) -> list[Meeting]:
        from ..domain.enums import MeetingStatus

        query = self._base()
        if upcoming_only:
            now = datetime.now(timezone.utc)
            query = query.filter(
                Meeting.scheduled_at >= now,
                Meeting.status != MeetingStatus.CANCELLED,
            )
        return query.order_by(Meeting.scheduled_at.asc()).offset(offset).limit(limit).all()
