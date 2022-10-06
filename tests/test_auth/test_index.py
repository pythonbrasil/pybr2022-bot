import json
from datetime import datetime
from unittest.mock import patch

from pybr2022.auth.index import AttendeesIndex, AttendeesJSONEncoder


@patch("pybr2022.auth.index.datetime")
def test_index(mock_datetime, attendees_index, attendee):
    now = datetime.utcnow()
    mock_datetime.utcnow.return_value = now

    attendees_index.add(attendee)

    assert len(attendees_index._index) == 2
    assert attendees_index.search(attendee.order_id) == attendee
    assert attendees_index.search(attendee.email) == attendee
    assert attendees_index.updated_at == now


def test_load_cache(tmp_path, attendee):
    now = datetime.utcnow()

    cache = {
        "updated_at": now.isoformat(),
        "index": {
            attendee.order_id: attendee.__dict__,
            attendee.email: attendee.__dict__,
        },
    }

    cache_file = tmp_path / "cache.json"
    with cache_file.open("w") as fp:
        json.dump(cache, fp)

    index = AttendeesIndex(cache_file, True)
    assert index.updated_at == now
    assert index.search(attendee.order_id).__dict__ == attendee.__dict__
    assert index.search(attendee.email).__dict__ == attendee.__dict__


@patch("pybr2022.auth.index.datetime")
def test_store_cache(mock_datetime, attendees_index, attendee):
    now = datetime.utcnow()
    mock_datetime.utcnow.return_value = now

    attendees_index.add(attendee)
    with attendees_index._index_path.open(mode="r") as fp:
        data = json.load(fp)
        assert data["updated_at"] == now.isoformat()
        assert data["index"][attendee.order_id] == attendee.__dict__
        assert data["index"][attendee.email] == attendee.__dict__


def test_attendees_json_encoder(attendee):
    assert AttendeesJSONEncoder().default(attendee) == attendee.__dict__
    assert AttendeesJSONEncoder().default("other-type") == None
