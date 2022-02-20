# -----------------------------------------------------------------------------
# System Imports
# -----------------------------------------------------------------------------

import asyncio
import sys
from pathlib import Path

# -----------------------------------------------------------------------------
# Public Imports
# -----------------------------------------------------------------------------

import click
from rich.console import Console
from . import __version__

try:
    from . import inventory_transceivers
    from . import inventory_versions

except Exception:
    Console().print_exception(show_locals=True)
    sys.exit(1)

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
    """ """
    try:
        cli()

    except Exception:
        Console().print_exception(show_locals=True)
        sys.exit(1)
