# =============================================================================
# Purpose:
# --------
#    This file contains the main async funciton responsible for finding a
#    connected end-host on the network, given the host's MAC address value.
# =============================================================================

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
class FindHostSearchResults:
    """Identifies where the end-host was found on the network"""

    device: str  # the network device hostname
    interface: str  # the interface on the network device


async def main(inventory: List[str], macaddr: MacAddress):
    """
    Given an inventory of devices and the MAC address to locate, try to find
    the location of the end-host.  As a result of checking the network, the
    User will see an output of either "found" identifying the network device
    and port, or "Not found".

    Parameters
    ----------
    inventory: List[str]
        The list of network devices to check.

    macaddr: MacAddress
        The end-host MAC addresss to locate
    """

    with Progress() as progressbar:
        found = await _search_network(
            inventory, macaddr=macaddr, progressbar=progressbar
        )

    if not found:
        print("Not found.")
        return

    print(f"Found on device {found.device}, interface {found.interface}")


# -----------------------------------------------------------------------------
#
#                                 PRIVATE CODE BEGINS
#
# -----------------------------------------------------------------------------


async def _search_network(
    inventory: List[str], macaddr: MacAddress, progressbar: Progress
) -> Optional[FindHostSearchResults]:
    """
    This function searches the network of the given inventory for the end-host
    with thive MAC address.  If the end-host is found then the results are
    retured in a "search results" dataclass. If not found, then return None.

    Parameters
    ----------
    inventory: List[str]
        The list of network devices to check.

    macaddr: MacAddress
        The end-host MAC addresss to locate

    progressbar: Progress
        A progress-bar CLI widget to indicate progress to the User.

    Returns
    -------
    Optional[FindHostSearchResults] - as described.
    """

    tasks = [
        _device_find_host_macaddr(device=device, macaddr=macaddr)
        for device in inventory
    ]

    pb_task = progressbar.add_task(description="Locating host", total=len(tasks))

    for this_dev in asyncio.as_completed(tasks):
        progressbar.update(pb_task, advance=1)

        if found := await this_dev:
            return found

    # not found in the inventory of devices
    return None


async def _device_find_host_macaddr(
    device: str, macaddr: MacAddress
) -> Optional[FindHostSearchResults]:
    """
    This function examines a specific network device for the given end-host MAC
    address.  If the MAC address is found on a network "edge-port" then return
    the search results.  Otherwise, return None.

    Parameters
    ----------
    device: str
        The network device hostname

    macaddr: MacAddress
        The end-host MAC address

    Returns
    -------
    Optional[FindHostSearchResults] - as described.
    """

    async with Device(host=device) as dev:

        # if the MAC address is not on this device, then return None.
        if not (interface := await dev.find_macaddr(macaddr)):
            return None

        # if the MAC address is found, but not on an edge-port, then return
        # None.
        if not await dev.is_edge_port(interface=interface):
            return None

        # If here, then the MAC address was found on this device on an edge-port.
        return FindHostSearchResults(device=device, interface=interface)
