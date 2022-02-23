# -----------------------------------------------------------------------------
# System Imports
# -----------------------------------------------------------------------------
import contextlib
from typing import Optional, List

# -----------------------------------------------------------------------------
# Public Imports
# -----------------------------------------------------------------------------

from httpx import AsyncHTTPTransport

from aioeapi import Device as _Device
from macaddr import MacAddress

# -----------------------------------------------------------------------------
# Private Imports
# -----------------------------------------------------------------------------

from .netdefs import VENDORS_IN_NETWORK, NETUSER_BASICAUTH, XcvrStatus

# -----------------------------------------------------------------------------
# Exports
# -----------------------------------------------------------------------------

__all__ = ["Device"]


# -----------------------------------------------------------------------------
#
#                                 CODE BEGINS
#
# -----------------------------------------------------------------------------


class SafeAsyncHTTPTransport(AsyncHTTPTransport):
    async def __aexit__(self, *vargs):
        """
        Override the async exit context manager since closing a session with
        requests in-flight is causing RuntimeError exceptions in httpcore
        verision 0.14.7 (latest at this time).  See source code:
        https://github.com/encode/httpcore/blob/master/httpcore/_async/connection_pool.py#L299

        Notes
        -----
        TODO:   this code should likely go into the aio-eapi package.  Awaiting
                further feedback on the open github issue:
                https://github.com/encode/httpcore/issues/510

        using httpcore==0.14.5 does not result in the above issue, fwiw.
        """
        with contextlib.suppress(RuntimeError):
            await super().__aexit__(*vargs)


class Device(_Device):
    """
    Subclass the Arista EOS async client to define methods we use for the
    network use-case demonstrations.
    """

    def __init__(self, *vargs, **kwargs):
        super(Device, self).__init__(
            *vargs, transport=SafeAsyncHTTPTransport(verify=False), **kwargs
        )

    # Arista eAPI uses basic-auth authentication.  Assigning this value once is
    # used by all instances upon construction.
    auth = NETUSER_BASICAUTH

    async def is_edge_port(self, interface: str) -> bool:
        """
        This function returns True if the given interface is considered and "edge-port"
        where an end-host is connected, False otherwise.

        The criteria to determine an edge-port:

            (1) Must be an Ethernet port, not any virtual-port construct like Port Channel.
                For demo purposes, not a "real-world" criteria, however.

            (2a) If host provides LLDP, then the host-system must not be a known network
                vendor

            (2b) If host is not using LLDP

        Parameters
        ----------
        interface: str

        Returns
        -------
        bool
        """

        # if the interface name is not an Ethernet<X> port, then it is not an
        # edge port

        if not interface.startswith("Eth"):
            return False

        # Check LLDP status
        res = await self.cli(f"show lldp neighbors {interface} detail")

        # if there is no LLDP neighbor, then it is by default an edge port.
        if not (nei_data := res["lldpNeighbors"][interface]["lldpNeighborInfo"]):
            return True

        # if there is LLDP data, then let's ensure it is not another network device
        # for demo purposes, checking the sysDesc value for name of known vendors
        # Only going to look at the first entry in this table (demo purposes) if
        # LLDP neighbor is a network vendor, then it is not an edge-port.

        nei_rec = nei_data[0]

        sys_desc = (
            nei_rec.get("systemDescription")
            or nei_rec.get("neighborInterfaceInfo", {}).get("systemDescription")
            or ""
        )

        if any(vendor in sys_desc for vendor in VENDORS_IN_NETWORK):
            return False

        # If LLDP neighbor exists is not a known network vendor, then this is an
        # edge-port.

        return True

    async def find_macaddr(self, macaddr: MacAddress) -> Optional[str]:
        """
        This function returns the interface name if the given MAC address
        is found on the device.  If the MAC address is not found, then
        return None.

        Parameters
        ----------
        macaddr: str
            The MAC address to locate

        Returns
        -------
        Optonal[str]
        """

        # Arista EOS uses the xx:yy:zz:aa:bb:cc format.
        macaddr = macaddr.format(sep=":", size=2)

        res = await self.cli(command=f"show mac address-table address {macaddr}")
        # If the MAC address does not exist on the device, then return None.

        if not (table_entries := res["unicastTable"]["tableEntries"]):
            return None

        # The MAC address should only be on one port; could be on multiple
        # VLANs, so only examinging the first table record.

        return table_entries[0]["interface"]

    async def inventory_xcvrs(self) -> List[XcvrStatus]:
        """
        This function returns a list containing each interface equipped with a transceiver.
        Each list item is a XcvrStatus dataclass used to normalize the EOS specific CLI
        payload values.

        Returns
        -------
        List - could be empty.
        """
        results = list()

        ifs_xcvr, ifs_status = await self.cli(
            commands=["show interfaces transceiver hardware", "show interfaces status"]
        )

        ifs_xcvr = ifs_xcvr["interfaces"]
        ifs_status = ifs_status["interfaceStatuses"]

        for ifx_name, ifx_data in ifs_xcvr.items():

            # the transceiver interface output will include each optic lane for
            # a physical port, for example Ethernet50/1, Ethernet50/2, .... need
            # to ensure that the xcvr interface-name is actually used; and if
            # not, then stip the transceiver record.

            if not (if_status := ifs_status.get(ifx_name)):
                continue

            # filter out interfaces like 2.5GB that are not transceivers, but still
            # report results

            if (ifx_type := ifx_data["detectedMediaType"]) != ifx_data["mediaType"]:
                continue

            # add a transceiver status record for the given interface

            results.append(
                XcvrStatus(
                    media_type=ifx_type,
                    intf_oper_up=if_status["lineProtocolStatus"] == "up",
                    intf_name=ifx_name,
                    intf_desc=if_status["description"],
                )
            )

        return results
