#!/usr/bin/env python3
"""Create test data for NetBox ZPL Labels plugin testing.

This script creates a realistic office environment with:
- 1 Building with 1 floor
- 1 SER (Satellite Equipment Room) with rack
- 1 HPE Aruba 48-port switch
- 1 48-port patch panel
- 30 workstations with wall outlets and iMacs
- All necessary cabling between components

Usage:
    python scripts/create_test_data.py

Environment variables (or use .env file):
    NETBOX_URL: NetBox instance URL
    NETBOX_BEARER_TOKEN: Full bearer token (nbt_key.secret format)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import requests

# Load .env file if present
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())

# Configuration
NETBOX_URL = os.environ.get("NETBOX_URL", "").rstrip("/")
NETBOX_TOKEN = os.environ.get("NETBOX_BEARER_TOKEN", "")

if not NETBOX_URL or not NETBOX_TOKEN:
    print("Error: NETBOX_URL and NETBOX_BEARER_TOKEN must be set")
    print("Set them in .env file or as environment variables")
    sys.exit(1)

# API session
session = requests.Session()
session.headers.update({
    "Authorization": f"Bearer {NETBOX_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json",
})


def api_get(endpoint: str, params: dict | None = None) -> dict:
    """GET request to NetBox API."""
    url = f"{NETBOX_URL}/api/{endpoint}"
    response = session.get(url, params=params)
    response.raise_for_status()
    return response.json()


def api_post(endpoint: str, data: dict) -> dict:
    """POST request to NetBox API."""
    url = f"{NETBOX_URL}/api/{endpoint}"
    response = session.post(url, json=data)
    if response.status_code >= 400:
        print(f"Error creating {endpoint}: {response.status_code}")
        print(f"Request data: {data}")
        print(f"Response: {response.text}")
        response.raise_for_status()
    return response.json()


def get_or_create(endpoint: str, lookup: dict, data: dict) -> tuple[dict, bool]:
    """Get existing object or create new one."""
    # Try to find existing
    result = api_get(endpoint, params=lookup)
    if result.get("count", 0) > 0:
        return result["results"][0], False

    # Create new
    full_data = {**lookup, **data}
    obj = api_post(endpoint, full_data)
    return obj, True


def create_manufacturers() -> dict[str, int]:
    """Create manufacturers."""
    print("\n=== Creating Manufacturers ===")
    manufacturers = {}

    mfrs = [
        {"name": "HPE", "slug": "hpe", "description": "Hewlett Packard Enterprise"},
        {"name": "Apple", "slug": "apple", "description": "Apple Inc."},
        {"name": "Generic", "slug": "generic", "description": "Generic/Unbranded"},
    ]

    for mfr in mfrs:
        obj, created = get_or_create(
            "dcim/manufacturers/",
            {"slug": mfr["slug"]},
            {"name": mfr["name"], "description": mfr.get("description", "")}
        )
        manufacturers[mfr["slug"]] = obj["id"]
        status = "Created" if created else "Exists"
        print(f"  {status}: {mfr['name']}")

    return manufacturers


def create_device_roles() -> dict[str, int]:
    """Create device roles."""
    print("\n=== Creating Device Roles ===")
    roles = {}

    role_data = [
        {"name": "Network Switch", "slug": "network-switch", "color": "2196f3"},
        {"name": "Patch Panel", "slug": "patch-panel", "color": "9e9e9e"},
        {"name": "Network Outlet", "slug": "network-outlet", "color": "607d8b"},
        {"name": "Workstation", "slug": "workstation", "color": "4caf50"},
    ]

    for role in role_data:
        obj, created = get_or_create(
            "dcim/device-roles/",
            {"slug": role["slug"]},
            {"name": role["name"], "color": role["color"]}
        )
        roles[role["slug"]] = obj["id"]
        status = "Created" if created else "Exists"
        print(f"  {status}: {role['name']}")

    return roles


def create_device_types(manufacturers: dict[str, int]) -> dict[str, int]:
    """Create device types."""
    print("\n=== Creating Device Types ===")
    device_types = {}

    types = [
        {
            "manufacturer": manufacturers["hpe"],
            "model": "Aruba CX 6300M-48",
            "slug": "aruba-cx-6300m-48",
            "u_height": 1,
            "is_full_depth": True,
            "description": "HPE Aruba CX 6300M 48-port PoE+ Switch",
        },
        {
            "manufacturer": manufacturers["generic"],
            "model": "48-Port Patch Panel",
            "slug": "48-port-patch-panel",
            "u_height": 2,
            "is_full_depth": False,
            "description": "Generic 48-port Cat6A patch panel",
        },
        {
            "manufacturer": manufacturers["generic"],
            "model": "Network Wall Outlet",
            "slug": "network-wall-outlet",
            "u_height": 0,
            "is_full_depth": False,
            "description": "Single-port network wall outlet",
        },
        {
            "manufacturer": manufacturers["apple"],
            "model": "iMac 24\" M3",
            "slug": "imac-24-m3",
            "u_height": 0,
            "is_full_depth": False,
            "description": "Apple iMac 24-inch with M3 chip",
        },
    ]

    for dt in types:
        obj, created = get_or_create(
            "dcim/device-types/",
            {"slug": dt["slug"]},
            dt
        )
        device_types[dt["slug"]] = obj["id"]
        status = "Created" if created else "Exists"
        print(f"  {status}: {dt['model']}")

    return device_types


def create_interface_templates(device_types: dict[str, int]) -> None:
    """Create interface templates for device types."""
    print("\n=== Creating Interface Templates ===")

    # Switch - 48 ethernet ports
    switch_type_id = device_types["aruba-cx-6300m-48"]
    existing = api_get("dcim/interface-templates/", {"devicetype_id": switch_type_id})
    if existing["count"] == 0:
        print("  Creating 48 switch ports...")
        for i in range(1, 49):
            api_post("dcim/interface-templates/", {
                "device_type": switch_type_id,
                "name": f"1/1/{i}",
                "type": "1000base-t",
                "description": f"Ethernet port {i}",
            })
        print("  Created: 48 switch interface templates")
    else:
        print("  Exists: Switch interface templates")

    # iMac - 1 ethernet port
    imac_type_id = device_types["imac-24-m3"]
    existing = api_get("dcim/interface-templates/", {"devicetype_id": imac_type_id})
    if existing["count"] == 0:
        api_post("dcim/interface-templates/", {
            "device_type": imac_type_id,
            "name": "Ethernet",
            "type": "1000base-t",
            "description": "Built-in Ethernet adapter",
        })
        print("  Created: iMac interface template")
    else:
        print("  Exists: iMac interface template")


def create_rear_port_templates(device_types: dict[str, int]) -> None:
    """Create rear port templates for patch panels and outlets."""
    print("\n=== Creating Rear Port Templates ===")

    # Patch Panel - 48 rear ports
    pp_type_id = device_types["48-port-patch-panel"]
    existing = api_get("dcim/rear-port-templates/", {"devicetype_id": pp_type_id})
    if existing["count"] == 0:
        print("  Creating 48 patch panel rear ports...")
        for i in range(1, 49):
            api_post("dcim/rear-port-templates/", {
                "device_type": pp_type_id,
                "name": f"Port {i} Rear",
                "type": "8p8c",
                "positions": 1,
            })
        print("  Created: 48 patch panel rear port templates")
    else:
        print("  Exists: Patch panel rear port templates")

    # Wall Outlet - 1 rear port
    outlet_type_id = device_types["network-wall-outlet"]
    existing = api_get("dcim/rear-port-templates/", {"devicetype_id": outlet_type_id})
    if existing["count"] == 0:
        api_post("dcim/rear-port-templates/", {
            "device_type": outlet_type_id,
            "name": "Rear",
            "type": "8p8c",
            "positions": 1,
        })
        print("  Created: Wall outlet rear port template")
    else:
        print("  Exists: Wall outlet rear port template")


def create_front_port_templates(device_types: dict[str, int]) -> None:
    """Create front port templates for patch panels and outlets."""
    print("\n=== Creating Front Port Templates ===")

    # We need to get rear port template IDs first
    pp_type_id = device_types["48-port-patch-panel"]
    outlet_type_id = device_types["network-wall-outlet"]

    # Patch Panel - 48 front ports
    existing = api_get("dcim/front-port-templates/", {"devicetype_id": pp_type_id})
    if existing["count"] == 0:
        print("  Creating 48 patch panel front ports...")
        rear_ports = api_get("dcim/rear-port-templates/", {"devicetype_id": pp_type_id, "limit": 50})
        rear_port_map = {rp["name"]: rp["id"] for rp in rear_ports["results"]}

        for i in range(1, 49):
            rear_name = f"Port {i} Rear"
            if rear_name in rear_port_map:
                api_post("dcim/front-port-templates/", {
                    "device_type": pp_type_id,
                    "name": f"Port {i}",
                    "type": "8p8c",
                    "rear_port": rear_port_map[rear_name],
                    "rear_port_position": 1,
                })
        print("  Created: 48 patch panel front port templates")
    else:
        print("  Exists: Patch panel front port templates")

    # Wall Outlet - 1 front port
    existing = api_get("dcim/front-port-templates/", {"devicetype_id": outlet_type_id})
    if existing["count"] == 0:
        rear_ports = api_get("dcim/rear-port-templates/", {"devicetype_id": outlet_type_id})
        if rear_ports["results"]:
            rear_port_id = rear_ports["results"][0]["id"]
            api_post("dcim/front-port-templates/", {
                "device_type": outlet_type_id,
                "name": "Front",
                "type": "8p8c",
                "rear_port": rear_port_id,
                "rear_port_position": 1,
            })
            print("  Created: Wall outlet front port template")
    else:
        print("  Exists: Wall outlet front port template")


def create_site() -> int:
    """Create site."""
    print("\n=== Creating Site ===")
    obj, created = get_or_create(
        "dcim/sites/",
        {"slug": "main-office"},
        {
            "name": "Main Office",
            "status": "active",
            "description": "Main office building",
        }
    )
    status = "Created" if created else "Exists"
    print(f"  {status}: Main Office")
    return obj["id"]


def create_locations(site_id: int) -> dict[str, int]:
    """Create locations (floor, SER, workstations)."""
    print("\n=== Creating Locations ===")
    locations = {}

    # Floor 1
    floor, created = get_or_create(
        "dcim/locations/",
        {"slug": "floor-1", "site_id": site_id},
        {"name": "Floor 1", "site": site_id, "description": "First floor"}
    )
    locations["floor-1"] = floor["id"]
    print(f"  {'Created' if created else 'Exists'}: Floor 1")

    # SER
    ser, created = get_or_create(
        "dcim/locations/",
        {"slug": "ser-01", "site_id": site_id},
        {
            "name": "SER-01",
            "site": site_id,
            "parent": floor["id"],
            "description": "Satellite Equipment Room"
        }
    )
    locations["ser-01"] = ser["id"]
    print(f"  {'Created' if created else 'Exists'}: SER-01")

    # Workstation area
    ws_area, created = get_or_create(
        "dcim/locations/",
        {"slug": "workstation-area", "site_id": site_id},
        {
            "name": "Workstation Area",
            "site": site_id,
            "parent": floor["id"],
            "description": "Open office workstation area"
        }
    )
    locations["workstation-area"] = ws_area["id"]
    print(f"  {'Created' if created else 'Exists'}: Workstation Area")

    # Individual workstations
    print("  Creating 30 workstation locations...")
    for i in range(1, 31):
        slug = f"ws-{i:02d}"
        ws, created = get_or_create(
            "dcim/locations/",
            {"slug": slug, "site_id": site_id},
            {
                "name": f"Workstation {i:02d}",
                "site": site_id,
                "parent": ws_area["id"],
                "description": f"Workstation {i:02d}"
            }
        )
        locations[slug] = ws["id"]
    print("  Created/verified: 30 workstation locations")

    return locations


def create_rack(site_id: int, location_id: int) -> int:
    """Create rack in SER."""
    print("\n=== Creating Rack ===")
    obj, created = get_or_create(
        "dcim/racks/",
        {"name": "SER-RACK-01", "site_id": site_id},
        {
            "name": "SER-RACK-01",
            "site": site_id,
            "location": location_id,
            "status": "active",
            "u_height": 42,
            "width": 19,
            "description": "Main network rack in SER",
        }
    )
    status = "Created" if created else "Exists"
    print(f"  {status}: SER-RACK-01")
    return obj["id"]


def create_devices(
    site_id: int,
    locations: dict[str, int],
    rack_id: int,
    device_types: dict[str, int],
    roles: dict[str, int],
) -> dict[str, int]:
    """Create all devices."""
    print("\n=== Creating Devices ===")
    devices = {}

    # Switch
    switch, created = get_or_create(
        "dcim/devices/",
        {"name": "SER-SW-01", "site_id": site_id},
        {
            "name": "SER-SW-01",
            "device_type": device_types["aruba-cx-6300m-48"],
            "role": roles["network-switch"],
            "site": site_id,
            "location": locations["ser-01"],
            "rack": rack_id,
            "position": 40,
            "face": "front",
            "status": "active",
            "description": "Main floor switch",
        }
    )
    devices["switch"] = switch["id"]
    print(f"  {'Created' if created else 'Exists'}: SER-SW-01 (Switch)")

    # Patch Panel
    pp, created = get_or_create(
        "dcim/devices/",
        {"name": "SER-PP-01", "site_id": site_id},
        {
            "name": "SER-PP-01",
            "device_type": device_types["48-port-patch-panel"],
            "role": roles["patch-panel"],
            "site": site_id,
            "location": locations["ser-01"],
            "rack": rack_id,
            "position": 38,
            "face": "front",
            "status": "active",
            "description": "Main patch panel",
        }
    )
    devices["patch-panel"] = pp["id"]
    print(f"  {'Created' if created else 'Exists'}: SER-PP-01 (Patch Panel)")

    # Wall Outlets and iMacs
    print("  Creating 30 wall outlets and 30 iMacs...")
    for i in range(1, 31):
        ws_location = locations[f"ws-{i:02d}"]

        # Wall Outlet
        outlet, _ = get_or_create(
            "dcim/devices/",
            {"name": f"WS-{i:02d}-OUTLET", "site_id": site_id},
            {
                "name": f"WS-{i:02d}-OUTLET",
                "device_type": device_types["network-wall-outlet"],
                "role": roles["network-outlet"],
                "site": site_id,
                "location": ws_location,
                "status": "active",
                "description": f"Wall outlet at workstation {i:02d}",
            }
        )
        devices[f"outlet-{i:02d}"] = outlet["id"]

        # iMac
        imac, _ = get_or_create(
            "dcim/devices/",
            {"name": f"WS-{i:02d}-IMAC", "site_id": site_id},
            {
                "name": f"WS-{i:02d}-IMAC",
                "device_type": device_types["imac-24-m3"],
                "role": roles["workstation"],
                "site": site_id,
                "location": ws_location,
                "status": "active",
                "serial": f"C02{i:02d}12345ABC",
                "asset_tag": f"ASSET-IMAC-{i:03d}",
                "description": f"iMac at workstation {i:02d}",
            }
        )
        devices[f"imac-{i:02d}"] = imac["id"]

    print("  Created/verified: 30 wall outlets + 30 iMacs")
    return devices


def create_device_components(devices: dict[str, int]) -> None:
    """Create ports and interfaces on devices that need them."""
    print("\n=== Creating Device Components ===")

    # Create interfaces on iMacs
    print("  Creating Ethernet interfaces on iMacs...")
    imac_interfaces_created = 0
    for i in range(1, 31):
        imac_id = devices[f"imac-{i:02d}"]
        existing = api_get("dcim/interfaces/", {"device_id": imac_id})
        if existing["count"] == 0:
            api_post("dcim/interfaces/", {
                "device": imac_id,
                "name": "Ethernet",
                "type": "1000base-t",
                "description": "Built-in Ethernet adapter",
            })
            imac_interfaces_created += 1
    print(f"    Created {imac_interfaces_created} iMac interfaces")

    # Create rear ports on wall outlets
    print("  Creating rear ports on wall outlets...")
    rear_ports_created = 0
    for i in range(1, 31):
        outlet_id = devices[f"outlet-{i:02d}"]
        existing = api_get("dcim/rear-ports/", {"device_id": outlet_id})
        if existing["count"] == 0:
            api_post("dcim/rear-ports/", {
                "device": outlet_id,
                "name": "Rear",
                "type": "8p8c",
                "positions": 1,
            })
            rear_ports_created += 1
    print(f"    Created {rear_ports_created} wall outlet rear ports")

    # Create front ports on wall outlets (linked to rear ports)
    print("  Creating front ports on wall outlets...")
    front_ports_created = 0
    for i in range(1, 31):
        outlet_id = devices[f"outlet-{i:02d}"]
        existing = api_get("dcim/front-ports/", {"device_id": outlet_id})
        if existing["count"] == 0:
            rear_port = api_get("dcim/rear-ports/", {"device_id": outlet_id})
            if rear_port["count"] > 0:
                api_post("dcim/front-ports/", {
                    "device": outlet_id,
                    "name": "Front",
                    "type": "8p8c",
                    "rear_port": rear_port["results"][0]["id"],
                    "rear_port_position": 1,
                })
                front_ports_created += 1
    print(f"    Created {front_ports_created} wall outlet front ports")


def get_interface(device_id: int, name: str) -> dict | None:
    """Get interface by device and name."""
    result = api_get("dcim/interfaces/", {"device_id": device_id, "name": name})
    if result["count"] > 0:
        return result["results"][0]
    return None


def get_front_port(device_id: int, name: str) -> dict | None:
    """Get front port by device and name."""
    result = api_get("dcim/front-ports/", {"device_id": device_id, "name": name})
    if result["count"] > 0:
        return result["results"][0]
    return None


def get_rear_port(device_id: int, name: str) -> dict | None:
    """Get rear port by device and name."""
    result = api_get("dcim/rear-ports/", {"device_id": device_id, "name": name})
    if result["count"] > 0:
        return result["results"][0]
    return None


def create_cables(devices: dict[str, int]) -> None:
    """Create all cables."""
    print("\n=== Creating Cables ===")

    switch_id = devices["switch"]
    pp_id = devices["patch-panel"]

    # Check existing cables
    existing_cables = api_get("dcim/cables/", {"limit": 1})
    if existing_cables["count"] > 0:
        print(f"  Found {existing_cables['count']} existing cables, checking for completion...")

    cables_created = 0

    # 1. Switch to Patch Panel (30 patch cables)
    print("  Creating Switch ↔ Patch Panel cables...")
    for i in range(1, 31):
        switch_if = get_interface(switch_id, f"1/1/{i}")
        pp_front = get_front_port(pp_id, f"Port {i}")

        if switch_if and pp_front:
            # Check if cable already exists
            if switch_if.get("cable") or pp_front.get("cable"):
                continue

            try:
                api_post("dcim/cables/", {
                    "a_terminations": [{"object_type": "dcim.interface", "object_id": switch_if["id"]}],
                    "b_terminations": [{"object_type": "dcim.frontport", "object_id": pp_front["id"]}],
                    "type": "cat6a",
                    "status": "connected",
                    "color": "0000ff",  # Blue
                    "length": 1,
                    "length_unit": "m",
                    "label": f"PATCH-SW-PP-{i:02d}",
                    "description": f"Patch cable from switch port {i} to patch panel port {i}",
                })
                cables_created += 1
            except Exception as e:
                print(f"    Warning: Could not create cable {i}: {e}")

    print(f"    Created {cables_created} switch-to-patch-panel cables")
    cables_created = 0

    # 2. Patch Panel (rear) to Wall Outlets (rear) - structured cabling
    print("  Creating Patch Panel ↔ Wall Outlet cables (structured cabling)...")
    for i in range(1, 31):
        pp_rear = get_rear_port(pp_id, f"Port {i} Rear")
        outlet_id = devices[f"outlet-{i:02d}"]
        outlet_rear = get_rear_port(outlet_id, "Rear")

        if pp_rear and outlet_rear:
            if pp_rear.get("cable") or outlet_rear.get("cable"):
                continue

            try:
                api_post("dcim/cables/", {
                    "a_terminations": [{"object_type": "dcim.rearport", "object_id": pp_rear["id"]}],
                    "b_terminations": [{"object_type": "dcim.rearport", "object_id": outlet_rear["id"]}],
                    "type": "cat6a",
                    "status": "connected",
                    "color": "808080",  # Gray
                    "length": 25,
                    "length_unit": "m",
                    "label": f"STRUCT-PP-WS{i:02d}",
                    "description": f"Structured cabling to workstation {i:02d}",
                })
                cables_created += 1
            except Exception as e:
                print(f"    Warning: Could not create cable {i}: {e}")

    print(f"    Created {cables_created} structured cabling cables")
    cables_created = 0

    # 3. Wall Outlets (front) to iMacs - patch cables
    print("  Creating Wall Outlet ↔ iMac cables...")
    for i in range(1, 31):
        outlet_id = devices[f"outlet-{i:02d}"]
        imac_id = devices[f"imac-{i:02d}"]

        outlet_front = get_front_port(outlet_id, "Front")
        imac_eth = get_interface(imac_id, "Ethernet")

        if outlet_front and imac_eth:
            if outlet_front.get("cable") or imac_eth.get("cable"):
                continue

            try:
                api_post("dcim/cables/", {
                    "a_terminations": [{"object_type": "dcim.frontport", "object_id": outlet_front["id"]}],
                    "b_terminations": [{"object_type": "dcim.interface", "object_id": imac_eth["id"]}],
                    "type": "cat6a",
                    "status": "connected",
                    "color": "ffffff",  # White
                    "length": 2,
                    "length_unit": "m",
                    "label": f"PATCH-WS{i:02d}-IMAC",
                    "description": f"Patch cable from outlet to iMac at workstation {i:02d}",
                })
                cables_created += 1
            except Exception as e:
                print(f"    Warning: Could not create cable {i}: {e}")

    print(f"    Created {cables_created} outlet-to-iMac cables")


def print_summary() -> None:
    """Print summary of created data."""
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    endpoints = [
        ("Sites", "dcim/sites/"),
        ("Locations", "dcim/locations/"),
        ("Racks", "dcim/racks/"),
        ("Manufacturers", "dcim/manufacturers/"),
        ("Device Types", "dcim/device-types/"),
        ("Device Roles", "dcim/device-roles/"),
        ("Devices", "dcim/devices/"),
        ("Interfaces", "dcim/interfaces/"),
        ("Front Ports", "dcim/front-ports/"),
        ("Rear Ports", "dcim/rear-ports/"),
        ("Cables", "dcim/cables/"),
    ]

    for name, endpoint in endpoints:
        result = api_get(endpoint)
        print(f"  {name}: {result['count']}")

    print("\n" + "=" * 60)
    print("Test data creation complete!")
    print(f"NetBox URL: {NETBOX_URL}")
    print("=" * 60)


def main() -> None:
    """Main entry point."""
    print("=" * 60)
    print("NetBox Test Data Creator")
    print("=" * 60)
    print(f"Target: {NETBOX_URL}")

    # Verify connection
    print("\nVerifying connection...")
    try:
        status = api_get("status/")
        print(f"  Connected to NetBox {status['netbox-version']}")
    except Exception as e:
        print(f"  Error connecting: {e}")
        sys.exit(1)

    # Create all data
    manufacturers = create_manufacturers()
    roles = create_device_roles()
    device_types = create_device_types(manufacturers)
    create_interface_templates(device_types)
    create_rear_port_templates(device_types)
    create_front_port_templates(device_types)

    site_id = create_site()
    locations = create_locations(site_id)
    rack_id = create_rack(site_id, locations["ser-01"])
    devices = create_devices(site_id, locations, rack_id, device_types, roles)
    create_device_components(devices)
    create_cables(devices)

    print_summary()


if __name__ == "__main__":
    main()
