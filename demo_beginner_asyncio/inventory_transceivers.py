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


async def main(inventory: List[str]):
    """
    The main entrypoint for gathering information about the transceivers used
    in the network.  As a result of running this function, the User will
    see a set of tabular output for:

        (1) Table of all transceiver types and their count
        (2) Table of interfaces with transcievers, operationally down
        (3) Table of the "down interfaces" transceiver types and their count

    Parameters
    ----------
    inventory: List[str]
        The list of network devices to collect transceiver information.
    """

    with Progress() as progressbar:
        ifx_types, ifs_down = await _inventory_network(inventory, progressbar)

    console = Console()
    console.print(
        "\n",
        _build_table_ifxcount(
            ifx_types, title=f"{sum(ifx_types.values())} Total Transceivers by Type"
        ),
    )

    if not ifs_down:
        return

    cntr_ifs_down = Counter()
    ifs_down_table = Table(
        "Device",
        "Interface",
        "Descr",
        "Media Type",
        title_justify="left",
    )

    for host, xcvr_status in ifs_down:
        ifs_down_table.add_row(
            host, xcvr_status.intf_name, xcvr_status.intf_desc, xcvr_status.media_type
        )
        cntr_ifs_down[xcvr_status.media_type] += 1

    total_ifs_down = sum(cntr_ifs_down.values())
    ifs_down_table.title = (
        f"{total_ifs_down} Interfaces with potentially unused transceivers"
    )
    console.print("\n", ifs_down_table)
    console.print(
        "\n",
        _build_table_ifxcount(
            cntr_ifs_down,
            title=f"{total_ifs_down} Unused Transceivers by Type",
        ),
    )


# -----------------------------------------------------------------------------
#
#                                 PRIVATE CODE BEGINS
#
# -----------------------------------------------------------------------------


async def _inventory_network(
    inventory: List[str], progressbar: Progress
) -> Tuple[Counter, List[Tuple[str, XcvrStatus]]]:
    """
    This function retrieves the transceivers for each network device in the
    inventory provided.

    Parameters
    ----------
    inventory: List[str]
        The network devices to gather transceiver information from.

    progressbar: Progress
        A progress bar CLI widget to show progress to the User.

    Returns
    -------
    Tuple:
        Counter - key is the transceiver media-type, value is the number of this type
        List - network device interfaces that are operationally down
    """
    tasks = [_device_get_transceivers(device) for device in inventory]
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

            if not each_xcvr.intf_oper_up:
                intfs_down.append((dev_name, each_xcvr))

    return c_xcvr_types, intfs_down


async def _device_get_transceivers(device: str) -> Tuple[str, List[XcvrStatus]]:
    """
    This function returns the transceiver status information for a given
    network device.

    Parameters
    ----------
    device: str
        The network device hostname

    Returns
    -------
    Tuple:
        str - the network device hostname
        List - the list of transceivers on the device

    Notes
    -----
    The device hostname is returned via the Tuple so that the calling asyncio
    as_completed results has the context of the results.
    """

    async with Device(host=device) as dev:
        intfs_xcvrs = await dev.inventory_xcvrs()

    return device, intfs_xcvrs


def _build_table_ifxcount(ifx_types: Counter, title) -> Table:
    """
    This function returns a rich.Table containing the transceiver media-type
    names as associated count values.

    Parameters
    ----------
    ifx_types: Counter
        The instance of media-type coounts

    title: str
        The table title

    Returns
    -------
    As described
    """
    report_table = Table("Media Type", "Count", title=title, title_justify="left")

    for ifx_type, count in sorted(ifx_types.items()):
        report_table.add_row(ifx_type, str(count))

    return report_table
