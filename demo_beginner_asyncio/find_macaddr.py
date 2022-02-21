# -----------------------------------------------------------------------------
# System Imports
# -----------------------------------------------------------------------------
import asyncio
from typing import List, Optional
from dataclasses import dataclass

# -----------------------------------------------------------------------------
# Public Imports
# -----------------------------------------------------------------------------

from macaddr import MacAddress

# -----------------------------------------------------------------------------
# Private Imports
# -----------------------------------------------------------------------------

from .progressbar import Progress
from .arista_eos import Device

# -----------------------------------------------------------------------------
# Exports
# -----------------------------------------------------------------------------

__all__ = ["main"]

# -----------------------------------------------------------------------------
#
#                                 CODE BEGINS
#
# -----------------------------------------------------------------------------


@dataclass()
class FoundHostMacaddr:
    host: str
    interface: str


async def device_find_host_macaddr(
    host: str, macaddr: str
) -> Optional[FoundHostMacaddr]:

    async with Device(host=host) as dev:

        if not (interface := await dev.find_macaddr(macaddr)):
            return None

        if not await dev.is_edge_port(interface=interface):
            return None

    return FoundHostMacaddr(host=host, interface=interface)


async def locate_host_macaddr(
    inventory, macaddr: str, progressbar: Progress
) -> Optional[FoundHostMacaddr]:

    tasks = [device_find_host_macaddr(host=host, macaddr=macaddr) for host in inventory]

    pb_task = progressbar.add_task(description="Locating host", total=len(tasks))

    found = None

    for this_dev in asyncio.as_completed(tasks):
        found = await this_dev
        progressbar.update(pb_task, advance=1)
        if found:
            break

    return found


async def main(inventory: List[str], macaddr: MacAddress):

    # Arista EOS uses the xx:yy:zz:aa:bb:cc format.
    macaddr = macaddr.format(sep=":", size=2)

    with Progress() as progressbar:
        found = await locate_host_macaddr(
            inventory, macaddr=macaddr, progressbar=progressbar
        )

    if not found:
        print("Not found.")
        return

    print(f"Found on device {found.host}, interface {found.interface}")
