from kernel.common.event import Event

EVENT_USER_LOGGED_IN = "user.logged_in"
EVENT_USER_REGISTERED = "user.registered"


def make_user_logged_in_event(data: dict, correlation_id: str = "") -> Event:
    return Event(type=EVENT_USER_LOGGED_IN, source="user_agent", data=data, correlation_id=correlation_id)


def make_user_registered_event(data: dict, correlation_id: str = "") -> Event:
    return Event(type=EVENT_USER_REGISTERED, source="user_agent", data=data, correlation_id=correlation_id)


SUBSCRIPTIONS: dict = {}
