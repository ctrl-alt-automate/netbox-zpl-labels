"""ZPL code generation for labels.

This module generates ZPL (Zebra Programming Language) code for labels
from NetBox objects. It supports various label sizes and includes
QR codes linking back to NetBox.

Supported object types:
- Cable: Cable labels with termination info
- Device: Device labels with location/rack info
- Interface: Interface labels (future)
- Rack: Rack labels (future)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from dcim.models import Cable, Device

    from ..models import LabelTemplate

# Supported object types for label generation
SUPPORTED_OBJECT_TYPES = [
    "cable",
    "device",
    "rack",
    "module",
    "circuit",
    "powerfeed",
    "powerpanel",
    "location",
    "site",
]


@dataclass
class LabelData:
    """Data container for label content.

    Attributes:
        cable_id: Cable identifier/label
        cable_url: Full URL to cable in NetBox
        term_a_device: Device name for termination A
        term_a_interface: Interface name for termination A
        term_b_device: Device name for termination B
        term_b_interface: Interface name for termination B
        length: Cable length with unit
        color: Cable color
        cable_type: Cable type (e.g., CAT6A, OM4)
        description: Cable description
        date: Current date
    """

    cable_id: str = ""
    cable_url: str = ""
    term_a_device: str = ""
    term_a_interface: str = ""
    term_b_device: str = ""
    term_b_interface: str = ""
    length: str = ""
    color: str = ""
    cable_type: str = ""
    description: str = ""
    date: str = ""

    @classmethod
    def from_cable(cls, cable: Cable, base_url: str = "") -> LabelData:
        """Create LabelData from a NetBox Cable object.

        Args:
            cable: NetBox Cable instance
            base_url: Base URL for NetBox (e.g., https://netbox.local)

        Returns:
            LabelData instance populated from cable
        """
        # Get termination A info
        term_a_device = ""
        term_a_interface = ""
        if cable.a_terminations:
            term_a = cable.a_terminations[0]
            if hasattr(term_a, "device") and term_a.device:
                term_a_device = str(term_a.device.name)
            term_a_interface = str(term_a)

        # Get termination B info
        term_b_device = ""
        term_b_interface = ""
        if cable.b_terminations:
            term_b = cable.b_terminations[0]
            if hasattr(term_b, "device") and term_b.device:
                term_b_device = str(term_b.device.name)
            term_b_interface = str(term_b)

        # Build cable URL
        cable_url = ""
        if base_url:
            base_url = base_url.rstrip("/")
            cable_url = f"{base_url}/dcim/cables/{cable.pk}/"

        # Get cable length
        length = ""
        if cable.length is not None:
            unit = cable.length_unit or "m"
            length = f"{cable.length}{unit}"

        # Get cable color
        color = ""
        if cable.color:
            color = cable.color

        # Get cable type
        cable_type = ""
        if cable.type:
            cable_type = str(cable.get_type_display())

        return cls(
            cable_id=cable.label or f"CBL-{cable.pk}",
            cable_url=cable_url,
            term_a_device=term_a_device,
            term_a_interface=term_a_interface,
            term_b_device=term_b_device,
            term_b_interface=term_b_interface,
            length=length,
            color=color,
            cable_type=cable_type,
            description=cable.description or "",
            date=date.today().isoformat(),
        )


@dataclass
class DeviceLabelData:
    """Data container for device label content.

    Attributes:
        device_name: Device name
        device_url: Full URL to device in NetBox
        device_type: Device type/model
        serial: Serial number
        asset_tag: Asset tag
        rack: Rack name
        position: Rack position (U)
        site: Site name
        location: Location name
        role: Device role
        status: Device status
        description: Device description
        date: Current date
    """

    device_name: str = ""
    device_url: str = ""
    device_type: str = ""
    serial: str = ""
    asset_tag: str = ""
    rack: str = ""
    position: str = ""
    site: str = ""
    location: str = ""
    role: str = ""
    status: str = ""
    description: str = ""
    date: str = ""

    @classmethod
    def from_device(cls, device: Device, base_url: str = "") -> DeviceLabelData:
        """Create DeviceLabelData from a NetBox Device object.

        Args:
            device: NetBox Device instance
            base_url: Base URL for NetBox (e.g., https://netbox.local)

        Returns:
            DeviceLabelData instance populated from device
        """
        # Build device URL
        device_url = ""
        if base_url:
            base_url = base_url.rstrip("/")
            device_url = f"{base_url}/dcim/devices/{device.pk}/"

        # Get rack position
        position = ""
        if device.position is not None:
            position = f"U{device.position}"

        return cls(
            device_name=device.name or "",
            device_url=device_url,
            device_type=str(device.device_type) if device.device_type else "",
            serial=device.serial or "",
            asset_tag=device.asset_tag or "",
            rack=str(device.rack) if device.rack else "",
            position=position,
            site=str(device.site) if device.site else "",
            location=str(device.location) if device.location else "",
            role=str(device.role) if device.role else "",
            status=device.get_status_display() if device.status else "",
            description=device.description or "",
            date=date.today().isoformat(),
        )

    def to_dict(self) -> dict[str, str]:
        """Convert to dictionary for template substitution."""
        return {
            "device_name": self.device_name,
            "device_url": self.device_url,
            "device_type": self.device_type,
            "serial": self.serial,
            "asset_tag": self.asset_tag,
            "rack": self.rack,
            "position": self.position,
            "site": self.site,
            "location": self.location,
            "role": self.role,
            "status": self.status,
            "description": self.description,
            "date": self.date,
        }


@dataclass
class RackLabelData:
    """Data container for rack label content."""

    rack_name: str = ""
    rack_url: str = ""
    site: str = ""
    location: str = ""
    facility_id: str = ""
    tenant: str = ""
    status: str = ""
    role: str = ""
    rack_type: str = ""
    u_height: str = ""
    description: str = ""
    date: str = ""

    @classmethod
    def from_rack(cls, rack: Any, base_url: str = "") -> "RackLabelData":
        """Create RackLabelData from a NetBox Rack object."""
        rack_url = ""
        if base_url:
            base_url = base_url.rstrip("/")
            rack_url = f"{base_url}/dcim/racks/{rack.pk}/"

        return cls(
            rack_name=rack.name or "",
            rack_url=rack_url,
            site=str(rack.site) if rack.site else "",
            location=str(rack.location) if rack.location else "",
            facility_id=rack.facility_id or "",
            tenant=str(rack.tenant) if rack.tenant else "",
            status=rack.get_status_display() if rack.status else "",
            role=str(rack.role) if rack.role else "",
            rack_type=rack.get_type_display() if rack.type else "",
            u_height=str(rack.u_height) if rack.u_height else "",
            description=rack.description or "",
            date=date.today().isoformat(),
        )

    def to_dict(self) -> dict[str, str]:
        """Convert to dictionary for template substitution."""
        return {
            "rack_name": self.rack_name,
            "rack_url": self.rack_url,
            "site": self.site,
            "location": self.location,
            "facility_id": self.facility_id,
            "tenant": self.tenant,
            "status": self.status,
            "role": self.role,
            "rack_type": self.rack_type,
            "u_height": self.u_height,
            "description": self.description,
            "date": self.date,
        }


@dataclass
class ModuleLabelData:
    """Data container for module label content."""

    module_name: str = ""
    module_url: str = ""
    device: str = ""
    module_bay: str = ""
    module_type: str = ""
    serial: str = ""
    asset_tag: str = ""
    status: str = ""
    description: str = ""
    date: str = ""

    @classmethod
    def from_module(cls, module: Any, base_url: str = "") -> "ModuleLabelData":
        """Create ModuleLabelData from a NetBox Module object."""
        module_url = ""
        if base_url:
            base_url = base_url.rstrip("/")
            module_url = f"{base_url}/dcim/modules/{module.pk}/"

        return cls(
            module_name=str(module) or "",
            module_url=module_url,
            device=str(module.device) if module.device else "",
            module_bay=str(module.module_bay) if module.module_bay else "",
            module_type=str(module.module_type) if module.module_type else "",
            serial=module.serial or "",
            asset_tag=module.asset_tag or "",
            status=module.get_status_display() if module.status else "",
            description=module.description or "",
            date=date.today().isoformat(),
        )

    def to_dict(self) -> dict[str, str]:
        """Convert to dictionary for template substitution."""
        return {
            "module_name": self.module_name,
            "module_url": self.module_url,
            "device": self.device,
            "module_bay": self.module_bay,
            "module_type": self.module_type,
            "serial": self.serial,
            "asset_tag": self.asset_tag,
            "status": self.status,
            "description": self.description,
            "date": self.date,
        }


@dataclass
class CircuitLabelData:
    """Data container for circuit label content."""

    circuit_id: str = ""
    circuit_url: str = ""
    provider: str = ""
    circuit_type: str = ""
    status: str = ""
    tenant: str = ""
    install_date: str = ""
    commit_rate: str = ""
    description: str = ""
    date: str = ""

    @classmethod
    def from_circuit(cls, circuit: Any, base_url: str = "") -> "CircuitLabelData":
        """Create CircuitLabelData from a NetBox Circuit object."""
        circuit_url = ""
        if base_url:
            base_url = base_url.rstrip("/")
            circuit_url = f"{base_url}/circuits/circuits/{circuit.pk}/"

        return cls(
            circuit_id=circuit.cid or "",
            circuit_url=circuit_url,
            provider=str(circuit.provider) if circuit.provider else "",
            circuit_type=str(circuit.type) if circuit.type else "",
            status=circuit.get_status_display() if circuit.status else "",
            tenant=str(circuit.tenant) if circuit.tenant else "",
            install_date=str(circuit.install_date) if circuit.install_date else "",
            commit_rate=str(circuit.commit_rate) if circuit.commit_rate else "",
            description=circuit.description or "",
            date=date.today().isoformat(),
        )

    def to_dict(self) -> dict[str, str]:
        """Convert to dictionary for template substitution."""
        return {
            "circuit_id": self.circuit_id,
            "circuit_url": self.circuit_url,
            "provider": self.provider,
            "circuit_type": self.circuit_type,
            "status": self.status,
            "tenant": self.tenant,
            "install_date": self.install_date,
            "commit_rate": self.commit_rate,
            "description": self.description,
            "date": self.date,
        }


@dataclass
class PowerFeedLabelData:
    """Data container for power feed label content."""

    powerfeed_name: str = ""
    powerfeed_url: str = ""
    power_panel: str = ""
    rack: str = ""
    status: str = ""
    feed_type: str = ""
    supply: str = ""
    phase: str = ""
    voltage: str = ""
    amperage: str = ""
    max_utilization: str = ""
    description: str = ""
    date: str = ""

    @classmethod
    def from_powerfeed(cls, powerfeed: Any, base_url: str = "") -> "PowerFeedLabelData":
        """Create PowerFeedLabelData from a NetBox PowerFeed object."""
        powerfeed_url = ""
        if base_url:
            base_url = base_url.rstrip("/")
            powerfeed_url = f"{base_url}/dcim/power-feeds/{powerfeed.pk}/"

        return cls(
            powerfeed_name=powerfeed.name or "",
            powerfeed_url=powerfeed_url,
            power_panel=str(powerfeed.power_panel) if powerfeed.power_panel else "",
            rack=str(powerfeed.rack) if powerfeed.rack else "",
            status=powerfeed.get_status_display() if powerfeed.status else "",
            feed_type=powerfeed.get_type_display() if powerfeed.type else "",
            supply=powerfeed.get_supply_display() if powerfeed.supply else "",
            phase=powerfeed.get_phase_display() if powerfeed.phase else "",
            voltage=str(powerfeed.voltage) if powerfeed.voltage else "",
            amperage=str(powerfeed.amperage) if powerfeed.amperage else "",
            max_utilization=f"{powerfeed.max_utilization}%" if powerfeed.max_utilization else "",
            description=powerfeed.description or "",
            date=date.today().isoformat(),
        )

    def to_dict(self) -> dict[str, str]:
        """Convert to dictionary for template substitution."""
        return {
            "powerfeed_name": self.powerfeed_name,
            "powerfeed_url": self.powerfeed_url,
            "power_panel": self.power_panel,
            "rack": self.rack,
            "status": self.status,
            "feed_type": self.feed_type,
            "supply": self.supply,
            "phase": self.phase,
            "voltage": self.voltage,
            "amperage": self.amperage,
            "max_utilization": self.max_utilization,
            "description": self.description,
            "date": self.date,
        }


@dataclass
class PowerPanelLabelData:
    """Data container for power panel label content."""

    powerpanel_name: str = ""
    powerpanel_url: str = ""
    site: str = ""
    location: str = ""
    description: str = ""
    date: str = ""

    @classmethod
    def from_powerpanel(cls, powerpanel: Any, base_url: str = "") -> "PowerPanelLabelData":
        """Create PowerPanelLabelData from a NetBox PowerPanel object."""
        powerpanel_url = ""
        if base_url:
            base_url = base_url.rstrip("/")
            powerpanel_url = f"{base_url}/dcim/power-panels/{powerpanel.pk}/"

        return cls(
            powerpanel_name=powerpanel.name or "",
            powerpanel_url=powerpanel_url,
            site=str(powerpanel.site) if powerpanel.site else "",
            location=str(powerpanel.location) if powerpanel.location else "",
            description=powerpanel.description or "",
            date=date.today().isoformat(),
        )

    def to_dict(self) -> dict[str, str]:
        """Convert to dictionary for template substitution."""
        return {
            "powerpanel_name": self.powerpanel_name,
            "powerpanel_url": self.powerpanel_url,
            "site": self.site,
            "location": self.location,
            "description": self.description,
            "date": self.date,
        }


@dataclass
class LocationLabelData:
    """Data container for location label content."""

    location_name: str = ""
    location_url: str = ""
    site: str = ""
    parent: str = ""
    status: str = ""
    tenant: str = ""
    facility: str = ""
    description: str = ""
    date: str = ""

    @classmethod
    def from_location(cls, location: Any, base_url: str = "") -> "LocationLabelData":
        """Create LocationLabelData from a NetBox Location object."""
        location_url = ""
        if base_url:
            base_url = base_url.rstrip("/")
            location_url = f"{base_url}/dcim/locations/{location.pk}/"

        return cls(
            location_name=location.name or "",
            location_url=location_url,
            site=str(location.site) if location.site else "",
            parent=str(location.parent) if location.parent else "",
            status=location.get_status_display() if location.status else "",
            tenant=str(location.tenant) if location.tenant else "",
            facility=location.facility or "",
            description=location.description or "",
            date=date.today().isoformat(),
        )

    def to_dict(self) -> dict[str, str]:
        """Convert to dictionary for template substitution."""
        return {
            "location_name": self.location_name,
            "location_url": self.location_url,
            "site": self.site,
            "parent": self.parent,
            "status": self.status,
            "tenant": self.tenant,
            "facility": self.facility,
            "description": self.description,
            "date": self.date,
        }


@dataclass
class SiteLabelData:
    """Data container for site label content."""

    site_name: str = ""
    site_url: str = ""
    status: str = ""
    region: str = ""
    site_group: str = ""
    tenant: str = ""
    facility: str = ""
    time_zone: str = ""
    physical_address: str = ""
    description: str = ""
    date: str = ""

    @classmethod
    def from_site(cls, site: Any, base_url: str = "") -> "SiteLabelData":
        """Create SiteLabelData from a NetBox Site object."""
        site_url = ""
        if base_url:
            base_url = base_url.rstrip("/")
            site_url = f"{base_url}/dcim/sites/{site.pk}/"

        return cls(
            site_name=site.name or "",
            site_url=site_url,
            status=site.get_status_display() if site.status else "",
            region=str(site.region) if site.region else "",
            site_group=str(site.group) if site.group else "",
            tenant=str(site.tenant) if site.tenant else "",
            facility=site.facility or "",
            time_zone=str(site.time_zone) if site.time_zone else "",
            physical_address=site.physical_address or "",
            description=site.description or "",
            date=date.today().isoformat(),
        )

    def to_dict(self) -> dict[str, str]:
        """Convert to dictionary for template substitution."""
        return {
            "site_name": self.site_name,
            "site_url": self.site_url,
            "status": self.status,
            "region": self.region,
            "site_group": self.site_group,
            "tenant": self.tenant,
            "facility": self.facility,
            "time_zone": self.time_zone,
            "physical_address": self.physical_address,
            "description": self.description,
            "date": self.date,
        }


def create_label_data(obj: Any, base_url: str = "") -> dict[str, str]:
    """Create label data dictionary from any supported NetBox object.

    Factory function that detects the object type and creates
    appropriate label data.

    Args:
        obj: NetBox object (Cable, Device, etc.)
        base_url: Base URL for NetBox

    Returns:
        Dictionary of label data suitable for template substitution

    Raises:
        ValueError: If object type is not supported
    """
    # Get the model class name
    model_name = obj.__class__.__name__.lower()

    if model_name == "cable":
        cable_data = LabelData.from_cable(obj, base_url)
        return {
            "cable_id": cable_data.cable_id,
            "cable_url": cable_data.cable_url,
            "term_a_device": cable_data.term_a_device,
            "term_a_interface": cable_data.term_a_interface,
            "term_b_device": cable_data.term_b_device,
            "term_b_interface": cable_data.term_b_interface,
            "length": cable_data.length,
            "color": cable_data.color,
            "type": cable_data.cable_type,
            "description": cable_data.description,
            "date": cable_data.date,
            # Common fields for cross-object templates
            "object_id": cable_data.cable_id,
            "object_url": cable_data.cable_url,
            "object_type": "Cable",
        }
    elif model_name == "device":
        device_data = DeviceLabelData.from_device(obj, base_url)
        result = device_data.to_dict()
        result["object_id"] = device_data.device_name
        result["object_url"] = device_data.device_url
        result["object_type"] = "Device"
        return result
    elif model_name == "rack":
        rack_data = RackLabelData.from_rack(obj, base_url)
        result = rack_data.to_dict()
        result["object_id"] = rack_data.rack_name
        result["object_url"] = rack_data.rack_url
        result["object_type"] = "Rack"
        return result
    elif model_name == "module":
        module_data = ModuleLabelData.from_module(obj, base_url)
        result = module_data.to_dict()
        result["object_id"] = module_data.module_name
        result["object_url"] = module_data.module_url
        result["object_type"] = "Module"
        return result
    elif model_name == "circuit":
        circuit_data = CircuitLabelData.from_circuit(obj, base_url)
        result = circuit_data.to_dict()
        result["object_id"] = circuit_data.circuit_id
        result["object_url"] = circuit_data.circuit_url
        result["object_type"] = "Circuit"
        return result
    elif model_name == "powerfeed":
        powerfeed_data = PowerFeedLabelData.from_powerfeed(obj, base_url)
        result = powerfeed_data.to_dict()
        result["object_id"] = powerfeed_data.powerfeed_name
        result["object_url"] = powerfeed_data.powerfeed_url
        result["object_type"] = "Power Feed"
        return result
    elif model_name == "powerpanel":
        powerpanel_data = PowerPanelLabelData.from_powerpanel(obj, base_url)
        result = powerpanel_data.to_dict()
        result["object_id"] = powerpanel_data.powerpanel_name
        result["object_url"] = powerpanel_data.powerpanel_url
        result["object_type"] = "Power Panel"
        return result
    elif model_name == "location":
        location_data = LocationLabelData.from_location(obj, base_url)
        result = location_data.to_dict()
        result["object_id"] = location_data.location_name
        result["object_url"] = location_data.location_url
        result["object_type"] = "Location"
        return result
    elif model_name == "site":
        site_data = SiteLabelData.from_site(obj, base_url)
        result = site_data.to_dict()
        result["object_id"] = site_data.site_name
        result["object_url"] = site_data.site_url
        result["object_type"] = "Site"
        return result
    else:
        raise ValueError(
            f"Unsupported object type: {model_name}. "
            f"Supported types: {', '.join(SUPPORTED_OBJECT_TYPES)}"
        )


# Dangerous ZPL commands that could affect printer configuration or security
# These commands can delete files, modify network settings, or execute stored formats
DANGEROUS_ZPL_COMMANDS = [
    "^ID",  # Image delete - deletes files from printer storage
    "^DF",  # Download format - stores data on printer flash
    "^XF",  # Recall format - executes stored format (potential code execution)
    "~DY",  # Download graphics/fonts - writes to flash storage
    "~DG",  # Download graphic - writes to flash storage
    "~DN",  # Delete network config
    "~NC",  # Set network configuration
    "~NR",  # Network reset
    "~JR",  # Power off after print
    "~PS",  # Print start toggle - can disable printing
    "~PP",  # Programmable pause
    "~HS",  # Host status return (info disclosure, less dangerous)
    "^HH",  # Print configuration label (info disclosure)
    "~WC",  # Print configuration label
    "^JU",  # Configuration update
    "~JC",  # Set clock
    "~RO",  # Reset advanced counter
]

# Pattern to detect dangerous commands (case-insensitive) - just matches the command prefix
DANGEROUS_ZPL_DETECT_PATTERN = re.compile(
    r"(" + "|".join(re.escape(cmd) for cmd in DANGEROUS_ZPL_COMMANDS) + r")",
    re.IGNORECASE,
)

# Pattern to remove dangerous commands WITH their parameters
# Matches command prefix followed by any characters until next ^ or ~ or end of string
DANGEROUS_ZPL_SANITIZE_PATTERN = re.compile(
    r"("
    + "|".join(re.escape(cmd) for cmd in DANGEROUS_ZPL_COMMANDS)
    + r")[^\^~]*",  # Match command + everything until next command or end
    re.IGNORECASE,
)


def validate_zpl_template(template: str) -> tuple[bool, list[str]]:
    """Validate a ZPL template for potentially dangerous commands.

    Args:
        template: ZPL template string to validate

    Returns:
        Tuple of (is_valid, list_of_dangerous_commands_found)
    """
    found_commands = DANGEROUS_ZPL_DETECT_PATTERN.findall(template.upper())
    # Remove duplicates while preserving order
    unique_commands = list(dict.fromkeys(found_commands))
    return len(unique_commands) == 0, unique_commands


def sanitize_zpl_template(template: str) -> str:
    """Remove dangerous commands and their parameters from a ZPL template.

    Args:
        template: ZPL template string to sanitize

    Returns:
        Sanitized ZPL template with dangerous commands and parameters removed
    """
    return DANGEROUS_ZPL_SANITIZE_PATTERN.sub("", template)


class ZPLGenerator:
    """Generator for ZPL label code.

    This class handles the generation of ZPL code from templates and data,
    including proper escaping and formatting.
    """

    # Characters that need escaping in ZPL field data
    ZPL_SPECIAL_CHARS = re.compile(r"[\^~\x00-\x1f]")

    def __init__(self, dpi: int = 300):
        """Initialize the ZPL generator.

        Args:
            dpi: Printer resolution (203 or 300)
        """
        self.dpi = dpi
        self.dots_per_mm = dpi / 25.4

    def mm_to_dots(self, mm: float) -> int:
        """Convert millimeters to printer dots.

        Args:
            mm: Value in millimeters

        Returns:
            Value in printer dots (rounded to integer)
        """
        return int(mm * self.dots_per_mm)

    def sanitize_field(self, value: str, max_length: int | None = None) -> str:
        """Sanitize a string for use in ZPL field data.

        Removes control characters and ZPL special characters that could
        break the ZPL parser.

        Args:
            value: Input string
            max_length: Optional maximum length

        Returns:
            Sanitized string safe for ZPL
        """
        # Convert to string if needed
        value = str(value) if value else ""

        # Remove ZPL special characters
        value = self.ZPL_SPECIAL_CHARS.sub("", value)

        # Truncate if needed
        if max_length and len(value) > max_length:
            value = value[: max_length - 3] + "..."

        return value

    def generate_qr_code(
        self,
        url: str,
        x: int,
        y: int,
        magnification: int = 4,
        model: int = 2,
    ) -> str:
        """Generate ZPL code for a QR code.

        Args:
            url: URL to encode in QR code
            x: X position in dots
            y: Y position in dots
            magnification: QR code size (1-10)
            model: QR code model (1 or 2)

        Returns:
            ZPL code string for QR code
        """
        # Clamp magnification to valid range
        magnification = max(1, min(10, magnification))

        # Use automatic input mode with LA prefix
        return f"^FO{x},{y}^BQN,{model},{magnification}^FDLA,{url}^FS"

    def generate_text_field(
        self,
        text: str,
        x: int,
        y: int,
        font_height: int = 28,
        font_width: int | None = None,
        max_width: int | None = None,
        justify: str = "L",
    ) -> str:
        """Generate ZPL code for a text field.

        Args:
            text: Text content
            x: X position in dots
            y: Y position in dots
            font_height: Font height in dots
            font_width: Font width in dots (default: ~0.87 × height)
            max_width: Maximum field width for block text
            justify: Justification (L=left, C=center, R=right)

        Returns:
            ZPL code string for text field
        """
        if font_width is None:
            font_width = int(font_height * 0.87)

        text = self.sanitize_field(text)

        zpl = f"^FO{x},{y}^A0N,{font_height},{font_width}"

        # Add field block for max width / justification
        if max_width:
            zpl += f"^FB{max_width},1,0,{justify}"

        zpl += f"^FD{text}^FS"
        return zpl

    def generate_box(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        thickness: int = 2,
    ) -> str:
        """Generate ZPL code for a graphic box (line/rectangle).

        Args:
            x: X position in dots
            y: Y position in dots
            width: Box width in dots
            height: Box height in dots
            thickness: Line thickness in dots

        Returns:
            ZPL code string for box
        """
        return f"^FO{x},{y}^GB{width},{height},{thickness}^FS"

    def generate_from_template(
        self,
        template: str,
        data: LabelData | dict[str, Any],
        quantity: int = 1,
    ) -> str:
        """Generate ZPL code from a template with variable substitution.

        Args:
            template: ZPL template with {variable} placeholders
            data: LabelData instance or dict with values
            quantity: Number of labels to print

        Returns:
            Complete ZPL code string
        """
        # Convert LabelData to dict if needed
        if isinstance(data, LabelData):
            values = {
                "cable_id": data.cable_id,
                "cable_url": data.cable_url,
                "term_a_device": data.term_a_device,
                "term_a_interface": data.term_a_interface,
                "term_b_device": data.term_b_device,
                "term_b_interface": data.term_b_interface,
                "length": data.length,
                "color": data.color,
                "type": data.cable_type,
                "description": data.description,
                "date": data.date,
            }
        else:
            values = data

        # Sanitize all values
        sanitized = {k: self.sanitize_field(str(v)) for k, v in values.items()}

        # Perform substitution
        zpl = template.format_map(SafeDict(sanitized))

        # Update print quantity if needed
        if quantity > 1:
            # Replace existing ^PQ or add before ^XZ
            if "^PQ" in zpl:
                zpl = re.sub(r"\^PQ\d+[^Z]*", f"^PQ{quantity},0,1,Y", zpl)
            else:
                zpl = zpl.replace("^XZ", f"^PQ{quantity},0,1,Y^XZ")

        return zpl


class SafeDict(dict):
    """Dictionary that returns placeholder for missing keys.

    Used for safe string formatting where missing keys should
    show as {key} instead of raising KeyError.
    """

    def __missing__(self, key: str) -> str:
        return f"{{{key}}}"


def generate_cable_label(
    cable: Cable,
    template: LabelTemplate,
    quantity: int = 1,
    base_url: str = "",
) -> str:
    """Generate ZPL code for a cable label.

    Convenience function that creates a ZPLGenerator and generates
    label code from a Cable and LabelTemplate.

    Args:
        cable: NetBox Cable instance
        template: LabelTemplate instance
        quantity: Number of labels to print
        base_url: Base URL for NetBox

    Returns:
        Complete ZPL code string
    """
    generator = ZPLGenerator(dpi=template.dpi)
    data = LabelData.from_cable(cable, base_url)
    return generator.generate_from_template(
        template=template.zpl_template,
        data=data,
        quantity=quantity,
    )


def generate_device_label(
    device: Device,
    template: LabelTemplate,
    quantity: int = 1,
    base_url: str = "",
) -> str:
    """Generate ZPL code for a device label.

    Convenience function that creates a ZPLGenerator and generates
    label code from a Device and LabelTemplate.

    Args:
        device: NetBox Device instance
        template: LabelTemplate instance
        quantity: Number of labels to print
        base_url: Base URL for NetBox

    Returns:
        Complete ZPL code string
    """
    generator = ZPLGenerator(dpi=template.dpi)
    data = DeviceLabelData.from_device(device, base_url)
    return generator.generate_from_template(
        template=template.zpl_template,
        data=data.to_dict(),
        quantity=quantity,
    )


def generate_label(
    obj: Any,
    template: LabelTemplate,
    quantity: int = 1,
    base_url: str = "",
) -> str:
    """Generate ZPL code for any supported object.

    Generic label generation function that determines the object type
    and generates appropriate label data.

    Args:
        obj: NetBox object (Cable, Device, Rack, etc.)
        template: LabelTemplate instance
        quantity: Number of labels to print
        base_url: Base URL for NetBox

    Returns:
        Complete ZPL code string

    Raises:
        ValueError: If object type is not supported
    """
    generator = ZPLGenerator(dpi=template.dpi)
    data = create_label_data(obj, base_url)
    return generator.generate_from_template(
        template=template.zpl_template,
        data=data,
        quantity=quantity,
    )
