from datetime import datetime
from typing import Optional

from loguru import logger

from .models import Attendee


class AttendeesIndex:
    def __init__(self):
        self._index = {}
        self.updated_at = None

    def add(self, attendee: Attendee) -> None:
        self._index[attendee.order_id.lower()] = attendee
        self._index[attendee.email.lower()] = attendee
        self.updated_at = datetime.utcnow()
        logger.info(
            f"New attendee added to the index. attendee={attendee!r}, updated_at={self.updated_at!r}"
        )

    def search(self, query: str) -> Optional[Attendee]:
        query = query.strip().lower()
        return self._index.get(query)
