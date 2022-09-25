from unittest import mock

import pytest

from pybr2022.auth.cog import AuthenticationCog


@pytest.mark.asyncio
@mock.patch("pybr2022.auth.cog.EventBrite.list_attendees")
async def test_load_attendees(mock_list_attendees):
    cog = AuthenticationCog("bot", "event-id", "eventbrite-api-token")
    assert not cog.attendees_index._index
    assert not cog.attendees_index.updated_at

    fake_attendee = mock.Mock(email="email", order_id="order-id")
    mock_list_attendees.return_value = [fake_attendee]

    await cog._load_attendees()

    assert len(cog.attendees_index._index) == 2
    assert cog.attendees_index.search(fake_attendee.email) == fake_attendee
    assert cog.attendees_index.search(fake_attendee.order_id) == fake_attendee
