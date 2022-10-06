from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from pybr2022.auth.index import AttendeesIndex
from tests.test_auth.factories import AttendeeFactory


@pytest.fixture
def attendee():
    return AttendeeFactory.build()


@pytest.fixture
def attendees_index():
    with TemporaryDirectory() as dir:
        cache_file = Path(dir) / "cache.json"
        yield AttendeesIndex(cache_file, True)
