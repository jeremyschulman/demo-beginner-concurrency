# -----------------------------------------------------------------------------
# System Imports
# -----------------------------------------------------------------------------

from typing import List
from multiprocessing import Pool
from itertools import islice
import asyncio
from timeit import default_timer as timer
from collections import Counter

# -----------------------------------------------------------------------------
# Private Imports
# -----------------------------------------------------------------------------

from .progressbar import Progress
from . import inventory_transceivers as its


def chunk(it, size):
    """
    https://stackoverflow.com/questions/312443/how-do-you-split-a-list-into-evenly-sized-chunks
    """
    it = iter(it)
    return iter(lambda: list(islice(it, size)), [])


def proc_main(inventory: List[str]):
    """
    Per multiprocessor Process main.  Takes slice of the inventory to
    process and returns the results
    """
    with Progress() as progressbar:
        return asyncio.run(its._inventory_network(inventory, progressbar))


def main(inventory: List[str]):
    """
    Using a multiprocessor approach, perform the inventory of transceivers
    demonstration.
    """

    workers = 4

    # split the inventory into "workers" chunks so that multiprocessors can
    # work on each chunk.

    chunk_c, rem = divmod(len(inventory), workers)
    pieces: List[List[str]] = list(chunk(inventory, len(inventory) // workers))
    if rem:
        rem_p = pieces.pop()
        pieces[-1].extend(rem_p)

    # run the inventory using a multiprocessor Pool constructure

    start_ts = timer()

    with Pool(processes=4) as pool:
        res = pool.map(proc_main, pieces)

    end_ts = timer()

    # Now we need to recombine the results of each of the Process into a single
    # structure for the reporting

    ifx_types = Counter()
    ifs_down = list()

    for part_ifx_types, part_ifs_down in res:
        ifx_types.update(part_ifx_types)
        ifs_down.extend(part_ifs_down)

    its._report(ifx_types, ifs_down)
    print(f"elapsed time: {end_ts - start_ts}")
