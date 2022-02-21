import os
from httpx import BasicAuth

VENDORS_IN_NETWORK = ("cisco", "arista", "extreme")

NETUSER_BASICAUTH = BasicAuth(
    username=os.environ["NETWORK_USERNAME"], password=os.environ["NETWORK_PASSWORD"]
)
