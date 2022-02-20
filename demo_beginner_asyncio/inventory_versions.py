# -----------------------------------------------------------------------------
# System Imports
# -----------------------------------------------------------------------------

import asyncio
import os
from collections import Counter

# -----------------------------------------------------------------------------
# Public Imports
# -----------------------------------------------------------------------------

from aioeapi import Device
from httpx import BasicAuth
from rich.console import Console
from rich.table import Table
from rich.progress import Progress


auth = BasicAuth(
    username=os.environ["NETWORK_USERNAME"], password=os.environ["NETWORK_PASSWORD"]
)


async def get_version(host: str):
    async with Device(host=host, auth=auth) as dev:
        return await dev.cli("show version")


async def inventory_versions(inventory):
    tasks = [get_version(host=host) for host in inventory]
    results = Counter()

    with Progress() as progress:
        pgt = progress.add_task(description="Inventory versions", total=len(tasks))

        for this_dev in asyncio.as_completed(tasks):
            ver_info = await this_dev
            results[ver_info["version"]] += 1
            progress.advance(task_id=pgt, advance=1)

    return results


async def main(inventory):
    results = await inventory_versions(inventory)
    table = Table("Version", "Count")
    for version, count in sorted(results.items()):
        table.add_row(version, str(count))

    Console().print(table)
