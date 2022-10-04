from dataclasses import dataclass


@dataclass
class Attendee:
    order_id: str
    first_name: str
    last_name: str
    email: str

    @staticmethod
    def from_eventbrite(data: dict):
        return Attendee.from_cache(data | data["profile"])

    @staticmethod
    def from_cache(data: dict):
        return Attendee(
            order_id=data["order_id"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            email=data["email"],
        )
