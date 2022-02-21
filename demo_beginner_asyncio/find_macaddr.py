# -----------------------------------------------------------------------------
# System Imports
# -----------------------------------------------------------------------------
import asyncio
from typing import List, Optional
from dataclasses import dataclass

# -----------------------------------------------------------------------------
# Public Imports
# -----------------------------------------------------------------------------
import httpx
from aioeapi import Device
from macaddr import MacAddress

# -----------------------------------------------------------------------------
# Private Imports
# -----------------------------------------------------------------------------

from .auth import get_network_auth
from .progressbar import Progress

# -----------------------------------------------------------------------------
# Exports
# -----------------------------------------------------------------------------

__all__ = ["main"]

# -----------------------------------------------------------------------------
#
#                                 CODE BEGINS
#
# -----------------------------------------------------------------------------


VENDORS_IN_NETWORK = ("cisco", "arista", "extreme")
g_htpx_limits = httpx.Limits(max_keepalive_connections=0, max_connections=1)


@dataclass()
class FoundHostMacaddr:
    host: str
    interface: str


async def is_edge_port(device: Device, interface: str) -> bool:

    res = await device.cli(f"show lldp neighbors {interface} detail")

    # if there is no LLDP neighbor, then it is by default an edge port.
    if not (nei_data := res["lldpNeighbors"][interface]["lldpNeighborInfo"]):
        return True

    # if there is LLDP data, then let's ensure it is not another network device
    # for demo purposes, checking the sysDesc value for name of known vendors
    # Only going to look at the first entry in this table (demo purposes) if
    # LLDP neighbor is a network vendor, then it is not an edge-port.

    sys_desc = nei_data[0]["neighborInterfaceInfo"]["systemDescription"].lower()
    if any(vendor in sys_desc for vendor in VENDORS_IN_NETWORK):
        return False

    # If LLDP neighbor exists is not a known network vendor, then this is an
    # edge-port.

    return True


async def device_find_host_macaddr(
    host: str, auth, macaddr: str
) -> Optional[FoundHostMacaddr]:

    async with Device(host=host, auth=auth, limits=g_htpx_limits) as dev:
        res = await dev.cli(command=f"show mac address-table address {macaddr}")
        # If the MAC address does not exist on the device, then return None.

        if not (table_entries := res["unicastTable"]["tableEntries"]):
            return None

        # The MAC address should only be on one port; could be on multiple
        # VLANs, so only examinging the first table record.  Also, only check
        # actual phyiscal ethernet ports.

        interface = table_entries[0]["interface"]
        if not interface.startswith("Eth"):
            return None

        if await is_edge_port(device=dev, interface=interface):
            return FoundHostMacaddr(host=host, interface=interface)

    # not found device edge-port
    return None


async def locate_host_macaddr(
    inventory, macaddr: str, progressbar: Progress
) -> Optional[FoundHostMacaddr]:

    auth = get_network_auth()

    tasks = [
        asyncio.create_task(device_find_host_macaddr(host=host, auth=auth, macaddr=macaddr))
        for host in inventory
    ]

    pb_task = progressbar.add_task(description="Locating host", total=len(tasks))

    for this_dev in asyncio.as_completed(tasks):
        found = await this_dev
        progressbar.update(pb_task, advance=1)
        if found:
            break
    else:
        return None

    for task in asyncio.all_tasks():
        task.cancel()

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
