import factory

from pybr2022.auth.models import Attendee


class AttendeeFactory(factory.Factory):
    class Meta:
        model = Attendee

    email = factory.Faker("email")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    order_id = factory.Faker("email")
