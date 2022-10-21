from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
from enum import Enum


MANAUS_TZ_OFFSET = timezone(timedelta(hours=-4))


@dataclass
class Talk:
    title: str
    speaker: str
    start: datetime
    end: datetime
    type: str
    _room: str
    youtube: str
    pretalx: str

    @staticmethod
    def get_speakers(data: dict):
        speakers = []
        for speaker in data["speakers"]:
            speakers.append(speaker["name"])

        return ", ".join(speakers)

    @staticmethod
    def get_datetime(date: str):
        return datetime.fromisoformat(date)

    @staticmethod
    def get_room(room: str):
        return room.replace(" - Vasco Vasquez", "")

    @staticmethod
    def get_pretalx_link(code: str) -> str:
        return f"https://pretalx.com/python-brasil-2022/talk/{code}"

    @staticmethod
    def get_youtube_link(description: str) -> str:
        try:
            return description.rsplit("Link:", 1)[1].strip()
        except IndexError:
            return ""

    @property
    def is_keynote(self):
        return "keynote" in self.title.lower()

    @property
    def room(self):
        return "keynote" if self.is_keynote else self._room

    @property
    def start_in_30_min(self) -> bool:
        now = datetime.now(tz=MANAUS_TZ_OFFSET)
        if self.start.date() != now.date():
            return False

        next_hour = now + timedelta(minutes=30)
        return now < self.start < next_hour

    @staticmethod
    def from_pretalx(data: dict):
        speakers = Talk.get_speakers(data)
        return Talk(
            title=data["title"],
            speaker=speakers,
            _room=Talk.get_room(data["slot"]["room"]["pt-BR"]),
            start=Talk.get_datetime(data["slot"]["start"]),
            end=Talk.get_datetime(data["slot"]["end"]),
            type=data["submission_type"]["pt-BR"],
            pretalx=Talk.get_pretalx_link(data["code"]),
            youtube=Talk.get_youtube_link(data["description"]),
        )
