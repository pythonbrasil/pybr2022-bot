import asyncio
from typing import Optional

from loguru import logger
from httpx import AsyncClient, HTTPError, ReadTimeout

from .models import Talk


MAX_API_CALL_RETRIES = 3
api_calls_limit = asyncio.Semaphore(5)


class Pretalx:
    BASE_URL = "https://pretalx.com/api"

    def __init__(self, event_slug: str, api_token: str):
        self.event_slug = event_slug
        self.api_token = api_token

    def _get_client(self):
        return AsyncClient()

    async def _request(
        self,
        client: AsyncClient,
        url: str,
        params: Optional[dict] = None,
        retries: int = MAX_API_CALL_RETRIES,
    ) -> dict:
        params = params or {}
        async with api_calls_limit:
            try:
                response = await client.get(url, params=params, timeout=10)
            except ReadTimeout:
                if retries > 1:
                    seconds = (MAX_API_CALL_RETRIES - retries + 1) * 2
                    await asyncio.sleep(seconds)
                    return await self._request(client, url, params, retries - 1)
                else:
                    raise
            try:
                response.raise_for_status()
            except HTTPError:
                raise Exception(
                    f"Error when calling EventBrite API. content={response.text!r}, url={url}, status_code={response.status_code}"
                )
        return response.json()

    async def talks(self):
        talks = []
        url = f"{self.BASE_URL}/events/{self.event_slug}/talks/"
        params = {
            "limit": 100
        }

        async with self._get_client() as client:
            while url:
                response = await self._request(client, url, params)
                logger.info(f"Talks returned from Pretalx. talks={len(response['results'])}, next={response['next']}")
                talks += [
                    Talk.from_pretalx(data)
                    for data in response["results"]
                ]
                url = response["next"]

        return talks