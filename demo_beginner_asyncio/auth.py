import os
from httpx import BasicAuth

__all__ = ["get_network_auth"]


def get_network_auth():
    return BasicAuth(
        username=os.environ["NETWORK_USERNAME"], password=os.environ["NETWORK_PASSWORD"]
    )
