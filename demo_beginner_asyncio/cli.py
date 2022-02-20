# -----------------------------------------------------------------------------
# System Imports
# -----------------------------------------------------------------------------

import asyncio
from typing import List
import os
import sys
from pathlib import Path

# -----------------------------------------------------------------------------
# Public Imports
# -----------------------------------------------------------------------------

import click
from rich.console import Console
from macaddr import MacAddress

# -----------------------------------------------------------------------------
# Private Imports
# -----------------------------------------------------------------------------

from . import __version__
from . import inventory_transceivers
from . import inventory_versions
from . import find_macaddr

# -----------------------------------------------------------------------------
#
#                                 CODE BEGINS
#
# -----------------------------------------------------------------------------


def _opt_inventory(ctx: click.Context, param, value):
    try:
        return Path(value).read_text().splitlines()
    except Exception as exc:
        ctx.fail(f"Unable to load inventory file '{value}': {str(exc)}")


@click.group()
@click.version_option(version=__version__)
def cli():
    """Beginner-Concurency Demo CLI"""
    pass


@cli.command(name="xcvrs")
@click.option("-i", "--inventory", default="inventory.text", callback=_opt_inventory)
def cli_inventory_xcvrs(inventory):
    """Run inventory transceivers demo"""
    asyncio.run(inventory_transceivers.main(inventory=inventory))


@cli.command(name="versions")
@click.option("-i", "--inventory", default="inventory.text", callback=_opt_inventory)
def cli_inventory_versions(inventory):
    """Run inventory OS versions demo"""
    asyncio.run(inventory_versions.main(inventory=inventory))


@cli.command(name="find-macaddr")
@click.option("-i", "--inventory", default="inventory.text", callback=_opt_inventory)
@click.option("-m", "--macaddr", help="mac-address", required=True)
@click.pass_context
def cli_find_macaddr(ctx: click.Context, inventory: List[str], macaddr: str):
    """Find switch-port where host with mac-addresss"""

    try:
        macaddr = MacAddress(macaddr)
    except ValueError:
        ctx.fail(f"Not a valid MAC address: {macaddr}")

    print(f"Locating switch-port for host with MAC-Address {macaddr}")
    asyncio.run(find_macaddr.main(inventory=inventory, macaddr=macaddr))


# -----------------------------------------------------------------------------
#
#                                MAIN CLI ENTRYPOINT
#
# -----------------------------------------------------------------------------


def main():
    """
    Main entrypoint for demonstration CLI script.
    """
    try:
        cli()

    except Exception:
        Console().print_exception(suppress=os.environ)
        sys.exit(1)
