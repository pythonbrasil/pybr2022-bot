from datetime import datetime
from unittest.mock import patch

from pybr2022.auth.index import AttendeesIndex
from pybr2022.auth.models import Attendee


@patch("pybr2022.auth.index.datetime")
def test_index(mock_datetime):
    email = "attendee@email.com"
    order_id = "order_id"
    attendee = Attendee(order_id, "first-name", "last-name", email)

    now = datetime.utcnow()
    mock_datetime.utcnow.return_value = now

    index = AttendeesIndex()
    index.add(attendee)

    assert len(index._index) == 2
    assert index.search(order_id) == attendee
    assert index.search(email) == attendee
    assert index.updated_at == now
