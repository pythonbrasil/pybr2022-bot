import asyncio
import json
from base64 import b64encode
from typing import Optional

from httpx import AsyncClient, HTTPError
from loguru import logger

from .models import Attendee


class EventBriteAPIException(Exception):
    pass


class EventBrite:
    BASE_URL = "https://www.eventbriteapi.com/v3"

    def __init__(self, event_id: str, api_token: str):
        self.event_id = event_id
        self.api_token = api_token

    def _get_client(self):
        return AsyncClient()

    def _build_attendees_endpoint(self) -> str:
        return f"{self.BASE_URL}/events/{self.event_id}/attendees/"

    async def _request(self, client: AsyncClient, url: str, params: dict) -> dict:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
        except HTTPError:
            raise EventBriteAPIException(
                "Error when calling EventBrite API. content={response.text!r}, url={url}, status_code={response.status_code}"
            )

        return response.json()

    async def _list_attendees(
        self, client: AsyncClient, params: Optional[dict] = None
    ) -> dict:
        if not params:
            params = self._list_attendees_params()

        url = self._build_attendees_endpoint()
        response = await self._request(client, url, params)
        logger.info(
            "List attendees request. attendees={attendees}, page_number={page_number}".format(
                attendees=len(response["attendees"]),
                page_number=response["pagination"]["page_number"],
            )
        )
        return response

    def _list_attendees_params(self, page: Optional[int] = None):
        params = {
            "token": self.api_token,
            "status": "attending",
        }
        if page:
            next_page = json.dumps({"page": page})
            next_page = b64encode(next_page.encode("utf-8")).decode("utf-8")
            params["continuation"] = next_page

        return params

    def _prepare_list_attendees_all_pages(
        self, client: AsyncClient, first_page: int, last_page: int
    ):
        tasks = []
        for page_number in range(first_page, last_page + 1):
            params = self._list_attendees_params(page=page_number)
            tasks.append(self._list_attendees(client, params))

        return tasks

    async def _list_all_attendees(
        self, client: AsyncClient, next_page: int, last_page: int
    ) -> list[Attendee]:
        tasks = self._prepare_list_attendees_all_pages(client, next_page, last_page)

        logger.info(
            f"Tasks created for remaining pages of attendees list. tasks={len(tasks)}"
        )
        results = await asyncio.gather(*tasks)
        return [attendees for result in results for attendees in result["attendees"]]

    async def list_attendees(self) -> list[Attendee]:
        # TODO: check updated_at
        # TODO: check cache
        async with self._get_client() as client:
            response = await self._list_attendees(client)
            attendees = response.get("attendees", [])

            if response["pagination"]["has_more_items"]:
                next_page = response["pagination"]["page_number"] + 1
                last_page = response["pagination"]["page_count"]
                attendees.extend(
                    await self._list_all_attendees(client, next_page, last_page)
                )
            # get all attendees
            # filter
            return [Attendee.deserialize(attendee) for attendee in attendees]
