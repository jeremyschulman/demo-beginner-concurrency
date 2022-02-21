# -----------------------------------------------------------------------------
# System Imports
# -----------------------------------------------------------------------------

from typing import Tuple, List
import asyncio
from collections import Counter

# -----------------------------------------------------------------------------
# Public Imports
# -----------------------------------------------------------------------------

from rich.console import Console
from rich.table import Table

# -----------------------------------------------------------------------------
# Private Imports
# -----------------------------------------------------------------------------

from .arista_eos import Device
from .progressbar import Progress
from .netdefs import XcvrStatus

# -----------------------------------------------------------------------------
# Exports
# -----------------------------------------------------------------------------

__all__ = ["main"]

# -----------------------------------------------------------------------------
#
#                                 CODE BEGINS
#
# -----------------------------------------------------------------------------


async def get_transceivers(host: str) -> Tuple[str, List[XcvrStatus]]:

    async with Device(host=host) as dev:
        intfs_xcvrs = await dev.inventory_xcvrs()

    return host, intfs_xcvrs


async def inventory_transceivers(
    inventory: List[str], progressbar: Progress
) -> Tuple[Counter, List]:

    tasks = [get_transceivers(host=host) for host in inventory]
    intfs_down = list()
    c_xcvr_types = Counter()

    pgt = progressbar.add_task(description="Inventory transceivers", total=len(tasks))

    for this_dev in asyncio.as_completed(tasks):

        dev_xcvrs: List[XcvrStatus]
        dev_name, dev_xcvrs = await this_dev
        progressbar.advance(task_id=pgt, advance=1)

        # inventory each interface transceiver.  If the interfaces is not UP
        # then mark it as a potential unused transceiver for reclamation.

        for each_xcvr in dev_xcvrs:
            c_xcvr_types[each_xcvr.media_type] += 1
            if each_xcvr.intf_oper_up is False:
                intfs_down.append((dev_name, each_xcvr))

    return c_xcvr_types, intfs_down


def build_table_ifxcount(ifx_types, title=None) -> Table:
    report_table = Table("Media Type", "Count", title=title, title_justify="left")

    for ifx_type, count in sorted(ifx_types.items()):
        report_table.add_row(ifx_type, str(count))

    return report_table


async def main(inventory: List[str]):

    with Progress() as progressbar:
        ifx_types, ifs_down = await inventory_transceivers(inventory, progressbar)

    console = Console()
    console.print(
        "\n",
        build_table_ifxcount(
            ifx_types, title=f"{sum(ifx_types.values())} Total Transceivers by Type"
        ),
    )

    if not ifs_down:
        return

    ifs_down_count = Counter()
    ifs_down_table = Table(
        "Device",
        "Interface",
        "Descr",
        "Media Type",
        title="Interfaces with unused transceivers",
        title_justify="left",
    )

    xcvr_status: XcvrStatus
    for host, xcvr_status in ifs_down:
        ifs_down_table.add_row(
            host, xcvr_status.intf_name, xcvr_status.intf_desc, xcvr_status.media_type
        )
        ifs_down_count[xcvr_status.media_type] += 1

    console.print("\n", ifs_down_table)
    console.print(
        "\n",
        build_table_ifxcount(
            ifs_down_count,
            title=f"{sum(ifs_down_count.values())} Unused Transceivers by Type",
        ),
    )
