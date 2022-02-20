import os
from httpx import BasicAuth

__all__ = ["g_auth"]


try:
    g_auth = BasicAuth(
        username=os.environ["NETWORK_USERNAME"], password=os.environ["NETWORK_PASSWORD"]
    )

except KeyError as exc:
    raise RuntimeError(f"Missing environ {exc.args[0]}")
