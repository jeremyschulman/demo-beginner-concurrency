# -----------------------------------------------------------------------------
# System Imports
# -----------------------------------------------------------------------------

from typing import Tuple, Dict, List
import asyncio
from collections import Counter, defaultdict

# -----------------------------------------------------------------------------
# Public Imports
# -----------------------------------------------------------------------------

from aioeapi import Device
from rich.console import Console
from rich.table import Table

# -----------------------------------------------------------------------------
# Private Imports
# -----------------------------------------------------------------------------

from .progressbar import Progress
from .auth import get_network_auth

# -----------------------------------------------------------------------------
# Exports
# -----------------------------------------------------------------------------

__all__ = ["main"]

# -----------------------------------------------------------------------------
#
#                                 CODE BEGINS
#
# -----------------------------------------------------------------------------


async def get_transceivers(host: str, auth) -> Tuple[str, Dict]:
    ifs_data = defaultdict(dict)

    async with Device(host=host, auth=auth) as dev:
        ifs_xcvr, ifs_status = await dev.cli(
            commands=["show interfaces transceiver hardware", "show interfaces status"]
        )

    ifs_xcvr = ifs_xcvr["interfaces"]
    ifs_status = ifs_status["interfaceStatuses"]

    for ifx_name, ifx_data in ifs_xcvr.items():
        if not (if_status := ifs_status.get(ifx_name)):
            continue

        # filter out interfaces like 2.5GB that are not transceivers, but still
        # report results

        if (ifx_type := ifx_data["detectedMediaType"]) != ifx_data["mediaType"]:
            continue

        ifs_data[ifx_name]["xcvr_type"] = ifx_type
        ifs_data[ifx_name].update(if_status)

    return host, ifs_data


async def inventory_transceivers(
    inventory: List[str], progressbar: Progress
) -> Tuple[Counter, List]:

    auth = get_network_auth()

    tasks = [get_transceivers(host=host, auth=auth) for host in inventory]
    ifs_down = list()
    ifx_types = Counter()

    pgt = progressbar.add_task(description="Inventory transceivers", total=len(tasks))

    for this_dev in asyncio.as_completed(tasks):

        host, ifx_data = await this_dev
        progressbar.advance(task_id=pgt, advance=1)

        # inventory each interface transceiver.  If the interfaces is not UP
        # then mark it as a potential unused transceiver for reclamation.

        for if_name, if_data in ifx_data.items():
            ifx_types[if_data["xcvr_type"]] += 1
            if if_data["lineProtocolStatus"] != "up":
                ifs_down.append((host, if_name, if_data))

    return ifx_types, ifs_down


def build_table_ifxcount(ifx_types) -> Table:
    report_table = Table("Media Type", "Count")

    for ifx_type, count in sorted(ifx_types.items()):
        report_table.add_row(ifx_type, str(count))

    return report_table


async def main(inventory: List[str]):

    with Progress() as progressbar:
        ifx_types, ifs_down = await inventory_transceivers(inventory, progressbar)

    console = Console()
    console.print(build_table_ifxcount(ifx_types))

    if not ifs_down:
        return

    ifs_down_count = Counter()
    ifs_down_table = Table("Device", "Interface", "Descr", "Media Type")

    for host, if_name, if_data in ifs_down:
        ifx_type = if_data["xcvr_type"]
        ifs_down_table.add_row(host, if_name, if_data["description"], ifx_type)
        ifs_down_count[ifx_type] += 1

    console.print(ifs_down_table)
    console.print(build_table_ifxcount(ifs_down_count))
