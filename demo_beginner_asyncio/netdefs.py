import os
from dataclasses import dataclass

from httpx import BasicAuth

VENDORS_IN_NETWORK = ("cisco", "arista", "extreme")

NETUSER_BASICAUTH = BasicAuth(
    username=os.environ["NETWORK_USERNAME"], password=os.environ["NETWORK_PASSWORD"]
)


@dataclass()
class XcvrStatus:
    intf_name: str
    intf_desc: str
    intf_oper_up: bool
    media_type: str
