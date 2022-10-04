from unittest.mock import AsyncMock, Mock, patch

import pytest
from discord import ChannelType

from pybr2022.auth.cog import AuthenticationCog
from pybr2022.auth.eventbrite import EventBrite
from pybr2022.auth.index import AttendeesIndex


@pytest.fixture
@patch("pybr2022.auth.cog.AuthenticationCog._start_tasks", Mock())
def auth_cog(attendees_index: AttendeesIndex):
    mock_bot = AsyncMock()
    mock_guild = AsyncMock()
    eventbrite = EventBrite("event-id", "eventbrite-api-token")

    return AuthenticationCog(
        mock_bot,
        mock_guild,
        eventbrite,
        attendees_index,
        "attendee-role-name",
    )


@pytest.mark.asyncio
@patch("pybr2022.auth.cog.EventBrite.list_attendees")
async def test_load_attendees(mock_list_attendees, auth_cog, attendee):
    assert not auth_cog.attendees_index._index
    assert not auth_cog.attendees_index.updated_at

    mock_list_attendees.return_value = [attendee]

    await auth_cog._load_attendees()

    assert len(auth_cog.attendees_index._index) == 2
    assert auth_cog.attendees_index.search(attendee.email) == attendee
    assert auth_cog.attendees_index.search(attendee.order_id) == attendee


def test_message_from_bot(auth_cog):
    message = Mock()
    message.author.bot = True
    assert not auth_cog._is_private_message(message)


@pytest.mark.parametrize(
    "type, expected",
    (
        (ChannelType.forum, False),
        (ChannelType.news, False),
        (ChannelType.private_thread, False),
        (ChannelType.public_thread, False),
        (ChannelType.text, False),
        (ChannelType.private, True),
    ),
)
def test_message_types(type, expected, auth_cog):
    message = Mock()
    message.author.bot = False
    message.channel.type = type
    assert auth_cog._is_private_message(message) == expected


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "member,expect",
    (
        (Mock(roles=["role-1"]), True),
        (Mock(roles=["role-1", "role-2"]), False),
    ),
)
async def test_is_auth_needed(member, expect, auth_cog):
    should_check = await auth_cog._is_auth_needed(member)
    assert should_check == expect


@pytest.mark.asyncio
async def test_get_attendee_role(auth_cog):
    auth_cog._guild.fetch_roles.return_value = [Mock(name="")]
    await auth_cog._get_attendee_role()


@pytest.mark.asyncio
async def test_set_attendee_role(auth_cog):
    member = AsyncMock()
    role = Mock()
    auth_cog._attendee_role = role
    await auth_cog._set_attendee_role(member)
    member.add_roles.assert_called_once_with(role)


@pytest.mark.asyncio
@patch("pybr2022.auth.cog.AuthenticationCog._is_private_message")
@patch("pybr2022.auth.cog.AuthenticationCog._is_auth_needed")
async def test_authenticate_not_private_message(
    mock_is_auth_needed, mock_is_private_message, auth_cog
):
    mock_is_private_message.return_value = False
    await auth_cog.authenticate("message")
    mock_is_auth_needed.assert_not_called()


@pytest.mark.asyncio
@patch(
    "pybr2022.auth.cog.AuthenticationCog._is_private_message", Mock(return_value=True)
)
@patch(
    "pybr2022.auth.cog.AuthenticationCog._get_user_from_server",
    AsyncMock(return_value=False),
)
async def test_authenticate_member_not_in_server(auth_cog):
    mock_index = Mock()
    auth_cog.attendees_index = mock_index

    message = AsyncMock()
    await auth_cog.authenticate(message)
    message.author.send.assert_called()
    mock_index.search.assert_not_called()


@pytest.mark.asyncio
@patch(
    "pybr2022.auth.cog.AuthenticationCog._is_private_message", Mock(return_value=True)
)
@patch(
    "pybr2022.auth.cog.AuthenticationCog._get_user_from_server",
    AsyncMock(return_value=True),
)
@patch(
    "pybr2022.auth.cog.AuthenticationCog._is_auth_needed", AsyncMock(return_value=False)
)
async def test_authenticate_user_already_authenticated(auth_cog):
    mock_index = Mock()
    auth_cog.attendees_index = mock_index

    message = AsyncMock()
    await auth_cog.authenticate(message)
    message.author.send.assert_called()
    mock_index.search.assert_not_called()


@pytest.mark.asyncio
@patch(
    "pybr2022.auth.cog.AuthenticationCog._is_private_message", Mock(return_value=True)
)
@patch(
    "pybr2022.auth.cog.AuthenticationCog._is_auth_needed",
    AsyncMock(return_value=True),
)
@patch("pybr2022.auth.cog.AuthenticationCog._get_user_from_server")
@patch("pybr2022.auth.cog.AuthenticationCog._set_attendee_role")
async def test_authenticate_attendee(
    mock_set_attendee_role, mock_get_user_from_server, auth_cog, attendee
):
    auth_cog.attendees_index.add(attendee)

    message = AsyncMock(content=attendee.email)
    await auth_cog.authenticate(message)
    mock_set_attendee_role.assert_called_with(mock_get_user_from_server.return_value)


@pytest.mark.asyncio
@patch(
    "pybr2022.auth.cog.AuthenticationCog._is_private_message", Mock(return_value=True)
)
@patch(
    "pybr2022.auth.cog.AuthenticationCog._is_auth_needed",
    AsyncMock(return_value=True),
)
@patch("pybr2022.auth.cog.AuthenticationCog._set_attendee_role")
@patch("pybr2022.auth.cog.AuthenticationCog._log_channel")
async def test_authenticate_not_attendee(
    mock_log_channel, mock_set_attendee_role, auth_cog
):
    message = AsyncMock(content="email")

    await auth_cog.authenticate(message)
    mock_set_attendee_role.assert_not_called()
    mock_log_channel.assert_called_once()


@pytest.mark.asyncio
@patch("pybr2022.auth.cog.AuthenticationCog.authenticate")
async def test_on_message(mock_athenticate, auth_cog):
    message = "message"
    await auth_cog.on_message(message)
    mock_athenticate.assert_called_with(message)


@patch("pybr2022.auth.cog.AuthenticationCog._load_attendees")
def test_start_tasks(mock_load_attendees):
    AuthenticationCog("bot", "guild", "eventbrite", "index", "attendee-role-name")
    mock_load_attendees.start.assert_called_once()


@pytest.mark.asyncio
async def test_log_channel(auth_cog):
    channel = AsyncMock()
    channel.name = "logs"
    auth_cog._guild.fetch_channels.return_value = [channel]

    message = "log"
    await auth_cog._log_channel(message)

    auth_cog._guild.fetch_channels.assert_called_once()
    channel.send.assert_called_once_with(message)


@pytest.mark.asyncio
async def test_log_channel_cache(auth_cog):
    channel = AsyncMock()
    channel.name = "logs"
    message = "log"

    auth_cog._channels = [channel]
    await auth_cog._log_channel(message)

    auth_cog._guild.fetch_channels.assert_not_called()
    channel.send.assert_called_once_with(message)
