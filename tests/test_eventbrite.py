import json
from asyncio import iscoroutine
from unittest import mock

import httpx
import pytest

from pybr2022.auth.eventbrite import EventBrite, EventBriteAPIException
from pybr2022.auth.models import Attendee

BASE_DIR = "pybr2022.auth.eventbrite"


def _cancel_coroutines(tasks):
    for task in tasks:
        task.close()


def test_list_attendees_params():
    eventbrite = EventBrite("event-id", "api-token")
    expected_params = {
        "token": "api-token",
        "status": "attending",
    }
    assert eventbrite._list_attendees_params() == expected_params


def test_list_attendees_params_next_page():
    eventbrite = EventBrite("event-id", "api-token")
    expected_params = {
        "token": "api-token",
        "status": "attending",
        "continuation": "eyJwYWdlIjogMn0=",
    }
    assert eventbrite._list_attendees_params(page=2) == expected_params


@mock.patch(f"{BASE_DIR}.EventBrite._get_client", mock.Mock())
def test_prepare_list_attendees_all_pages():
    expected_params_1 = {
        "token": "api-token",
        "status": "attending",
        "continuation": "eyJwYWdlIjogMX0=",
    }
    expected_params_2 = expected_params_1.copy()
    expected_params_2["continuation"] = "eyJwYWdlIjogMn0="
    expected_params_3 = expected_params_1.copy()
    expected_params_3["continuation"] = "eyJwYWdlIjogM30="

    client = mock.Mock()
    eventbrite = EventBrite("event-id", "api-token")
    tasks = eventbrite._prepare_list_attendees_all_pages(client, 1, 3)

    assert len(tasks) == 3
    assert iscoroutine(tasks[0])
    _cancel_coroutines(tasks)


@pytest.mark.asyncio
async def test_list_attendees_exception(httpx_mock):
    httpx_mock.add_exception(
        httpx.TooManyRedirects("Hourly rate limit has been reached for this token")
    )
    eventbrite = EventBrite("event-id", "api-token")
    with pytest.raises(EventBriteAPIException):
        await eventbrite.list_attendees()


@pytest.mark.asyncio
async def test_list_attendees_no_attendees(httpx_mock, shared_datadir):
    data = json.loads((shared_datadir / "event_no_attendees.json").read_text())
    httpx_mock.add_response(json=data)
    eventbrite = EventBrite("event-id", "api-token")
    attendees = await eventbrite.list_attendees()
    assert attendees == []
    assert len(httpx_mock.get_requests()) == 1


@pytest.mark.asyncio
async def test_list_attendees_single_page(httpx_mock, shared_datadir):
    data = json.loads((shared_datadir / "event_attendees_single_page.json").read_text())
    httpx_mock.add_response(json=data)
    eventbrite = EventBrite("event-id", "api-token")
    attendees = await eventbrite.list_attendees()

    assert len(attendees) == 2
    assert len(httpx_mock.get_requests()) == 1
    assert attendees[0] == Attendee(
        "order-id-1", "Attendee", "1", "attendee-1@email.com"
    )
    assert attendees[1] == Attendee(
        "order-id-2", "Attendee", "2", "attendee-2@email.com"
    )


@pytest.mark.asyncio
async def test_list_attendees_multiple_pages(httpx_mock, shared_datadir):
    data = json.loads((shared_datadir / "event_attendees_first_page.json").read_text())
    httpx_mock.add_response(json=data)
    data = json.loads((shared_datadir / "event_attendees_second_page.json").read_text())
    httpx_mock.add_response(json=data)
    eventbrite = EventBrite("event-id", "api-token")
    attendees = await eventbrite.list_attendees()

    assert len(attendees) == 2
    assert len(httpx_mock.get_requests()) == 2
    assert attendees[0] == Attendee(
        "order-id-1", "Attendee", "1", "attendee-1@email.com"
    )
    assert attendees[1] == Attendee(
        "order-id-2", "Attendee", "2", "attendee-2@email.com"
    )