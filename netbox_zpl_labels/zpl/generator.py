"""ZPL code generation for cable labels.

This module generates ZPL (Zebra Programming Language) code for cable labels
from NetBox Cable objects. It supports various label sizes and includes
QR codes linking back to NetBox.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from dcim.models import Cable

    from ..models import LabelTemplate


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
