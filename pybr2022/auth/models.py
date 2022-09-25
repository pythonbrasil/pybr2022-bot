from dataclasses import dataclass


@dataclass
class Attendee:
    order_id: str
    first_name: str
    last_name: str
    email: str

    @staticmethod
    def deserialize(data: dict):
        return Attendee(
            order_id=data["order_id"],
            first_name=data["profile"]["first_name"],
            last_name=data["profile"]["last_name"],
            email=data["profile"]["email"],
        )
