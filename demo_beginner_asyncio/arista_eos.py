from typing import Optional

from aioeapi import Device as _Device

from .consts import VENDORS_IN_NETWORK, NETUSER_BASICAUTH


class Device(_Device):
    auth = NETUSER_BASICAUTH

    async def is_edge_port(self, interface: str) -> bool:
        # if the interface name is not an Ethernet<X> port, then it is not an
        # edge port

        if not interface.startswith("Eth"):
            return False

        res = await self.cli(f"show lldp neighbors {interface} detail")

        # if there is no LLDP neighbor, then it is by default an edge port.
        if not (nei_data := res["lldpNeighbors"][interface]["lldpNeighborInfo"]):
            return True

        # if there is LLDP data, then let's ensure it is not another network device
        # for demo purposes, checking the sysDesc value for name of known vendors
        # Only going to look at the first entry in this table (demo purposes) if
        # LLDP neighbor is a network vendor, then it is not an edge-port.

        sys_desc = nei_data[0]["neighborInterfaceInfo"]["systemDescription"].lower()
        if any(vendor in sys_desc for vendor in VENDORS_IN_NETWORK):
            return False

        # If LLDP neighbor exists is not a known network vendor, then this is an
        # edge-port.

        return True

    async def find_macaddr(self, macaddr: str) -> Optional[str]:
        res = await self.cli(command=f"show mac address-table address {macaddr}")
        # If the MAC address does not exist on the device, then return None.

        if not (table_entries := res["unicastTable"]["tableEntries"]):
            return None

        # The MAC address should only be on one port; could be on multiple
        # VLANs, so only examinging the first table record.

        return table_entries[0]["interface"]
