import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from loguru import logger

from .models import Attendee


class AttendeesJSONEncoder(json.JSONEncoder):
    def default(self, obj: Any):
        if isinstance(obj, Attendee):
            return obj.__dict__


class AttendeesIndex:
    def __init__(self, index_path: Path, cache_enabled: bool = False):
        self._index_path = index_path
        self._cache_enabled = cache_enabled
        self._index, self.updated_at = self._load_cache()

    def _load_cache(self):
        if not all(
            [
                self._cache_enabled,
                self._index_path.exists(),
                self._index_path.is_file(),
            ]
        ):
            return {}, None

        with self._index_path.open() as fp:
            cache = json.load(fp)
            updated_at = datetime.fromisoformat(cache["updated_at"])
            index = {
                key: Attendee.from_cache(value) for key, value in cache["index"].items()
            }
            return index, updated_at

    def _store_cache(self):
        if not self._cache_enabled:
            return

        with self._index_path.open(mode="w") as fp:
            cache = {
                "updated_at": self.updated_at.isoformat(),
                "index": self._index,
            }
            json.dump(cache, fp, cls=AttendeesJSONEncoder)

    def add(self, attendee: Attendee) -> None:
        self._index[attendee.order_id.lower()] = attendee
        self._index[attendee.email.lower()] = attendee
        self.updated_at = datetime.utcnow()
        self._store_cache()
        logger.info(
            f"New attendee added to the index. attendee={attendee!r}, updated_at={self.updated_at!r}"
        )

    def search(self, query: str) -> Optional[Attendee]:
        query = query.strip().lower()
        return self._index.get(query)
