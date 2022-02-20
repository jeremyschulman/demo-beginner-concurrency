# -----------------------------------------------------------------------------
# System Imports
# -----------------------------------------------------------------------------

import asyncio
import os
import sys
from pathlib import Path

# -----------------------------------------------------------------------------
# Public Imports
# -----------------------------------------------------------------------------

import click
from rich.console import Console
from . import __version__

from . import inventory_transceivers
from . import inventory_versions

# -----------------------------------------------------------------------------
#
#                                 CODE BEGINS
#
# -----------------------------------------------------------------------------


@click.group()
@click.version_option(version=__version__)
def cli():
    """Beginner-Concurency Demo CLI"""
    pass


@cli.command(name="xcvrs")
def cli_inventory_xcvrs():
    """Run inventory transceivers demo"""
    inventory = Path("inventory.text").read_text().splitlines()
    asyncio.run(inventory_transceivers.main(inventory=inventory))


@cli.command(name="versions")
def cli_inventory_versions():
    """Run inventory OS versions demo"""
    inventory = Path("inventory.text").read_text().splitlines()
    asyncio.run(inventory_versions.main(inventory=inventory))


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
