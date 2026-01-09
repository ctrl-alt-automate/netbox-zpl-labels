"""Predefined ZPL label templates for cable labels.

This module provides default ZPL templates for various
TE Connectivity Raychem SBP label sizes.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


@dataclass
class TemplateDefinition:
    """Definition for a default label template.

    Attributes:
        name: Template name
        description: Human-readable description
        label_size: TE SBP label size code
        width_mm: Print area width in mm
        height_mm: Print area height in mm
        zpl_template: ZPL code with placeholders
        include_qr: Whether template includes QR code
        qr_magnification: QR code magnification level
    """

    name: str
    description: str
    label_size: str
    width_mm: float
    height_mm: float
    zpl_template: str
    include_qr: bool = True
    qr_magnification: int = 4


# Template for SBP100375WE - Full featured label (25.4mm × 38mm print area)
TEMPLATE_SBP100375_FULL = TemplateDefinition(
    name="SBP100375 Full",
    description="Full featured cable label with QR code, terminations, and details",
    label_size="sbp100375",
    width_mm=25.4,
    height_mm=38.0,
    include_qr=True,
    qr_magnification=5,
    zpl_template="""^XA
^MMT
^PW300
^LL450
^LS0

^FO24,24
^A0N,42,36
^FB252,1,0,C
^FD{cable_id}^FS

^FO180,20
^BQN,2,5
^FDLA,{cable_url}^FS

^FO24,75
^A0N,22,18
^FDFrom: {term_a_device}^FS

^FO24,100
^A0N,20,16
^FD  {term_a_interface}^FS

^FO24,130
^A0N,22,18
^FDTo: {term_b_device}^FS

^FO24,155
^A0N,20,16
^FD  {term_b_interface}^FS

^FO24,185
^GB252,2,2^FS

^FO24,195
^A0N,20,16
^FD{type} {length}^FS

^FO24,220
^A0N,18,14
^FD{date}^FS

^PQ1,0,1,Y
^XZ""",
)


# Template for SBP100375WE - Compact version
TEMPLATE_SBP100375_COMPACT = TemplateDefinition(
    name="SBP100375 Compact",
    description="Compact cable label focusing on ID and QR code",
    label_size="sbp100375",
    width_mm=25.4,
    height_mm=38.0,
    include_qr=True,
    qr_magnification=5,
    zpl_template="""^XA
^MMT
^PW300
^LL450
^LS0

^FO24,30
^A0N,50,44
^FB252,1,0,C
^FD{cable_id}^FS

^FO75,100
^BQN,2,6
^FDLA,{cable_url}^FS

^FO24,340
^A0N,24,20
^FB252,1,0,C
^FD{term_a_device}^FS

^FO24,370
^A0N,18,14
^FB252,1,0,C
^FD-> {term_b_device}^FS

^PQ1,0,1,Y
^XZ""",
)


# Template for SBP100225WE - Medium label (19.1mm × 25mm print area)
TEMPLATE_SBP100225_STANDARD = TemplateDefinition(
    name="SBP100225 Standard",
    description="Standard medium-sized cable label",
    label_size="sbp100225",
    width_mm=19.1,
    height_mm=25.0,
    include_qr=True,
    qr_magnification=4,
    zpl_template="""^XA
^MMT
^PW225
^LL295
^LS0

^FO20,20
^A0N,36,30
^FD{cable_id}^FS

^FO130,15
^BQN,2,4
^FDLA,{cable_url}^FS

^FO20,65
^A0N,20,16
^FDA:{term_a_device}^FS

^FO20,90
^A0N,20,16
^FDB:{term_b_device}^FS

^FO20,120
^A0N,18,14
^FD{type} {length}^FS

^PQ1,0,1,Y
^XZ""",
)


# Template for SBP100143WE - Small label (12.7mm × 18mm print area)
TEMPLATE_SBP100143_MINIMAL = TemplateDefinition(
    name="SBP100143 Minimal",
    description="Minimal small label with ID and QR only",
    label_size="sbp100143",
    width_mm=12.7,
    height_mm=18.0,
    include_qr=True,
    qr_magnification=3,
    zpl_template="""^XA
^MMT
^PW150
^LL212
^LS0

^FO15,15
^A0N,30,24
^FD{cable_id}^FS

^FO40,55
^BQN,2,3
^FDLA,{cable_url}^FS

^PQ1,0,1,Y
^XZ""",
)


# Template for text-only labels (no QR code)
TEMPLATE_SBP100375_TEXT = TemplateDefinition(
    name="SBP100375 Text Only",
    description="Text-only label without QR code - maximum text space",
    label_size="sbp100375",
    width_mm=25.4,
    height_mm=38.0,
    include_qr=False,
    qr_magnification=0,
    zpl_template="""^XA
^MMT
^PW300
^LL450
^LS0

^FO24,20
^A0N,50,44
^FB252,1,0,C
^FD{cable_id}^FS

^FO24,80
^GB252,2,2^FS

^FO24,95
^A0N,24,20
^FDFrom:^FS

^FO24,125
^A0N,22,18
^FB252,1,0,L
^FD{term_a_device}^FS

^FO24,150
^A0N,20,16
^FD{term_a_interface}^FS

^FO24,185
^A0N,24,20
^FDTo:^FS

^FO24,215
^A0N,22,18
^FB252,1,0,L
^FD{term_b_device}^FS

^FO24,240
^A0N,20,16
^FD{term_b_interface}^FS

^FO24,280
^GB252,2,2^FS

^FO24,295
^A0N,22,18
^FD{type}^FS

^FO24,320
^A0N,22,18
^FDLength: {length}^FS

^FO24,350
^A0N,18,14
^FD{date}^FS

^PQ1,0,1,Y
^XZ""",
)


# Stored template format for batch printing efficiency
TEMPLATE_STORED_FORMAT = TemplateDefinition(
    name="Stored Format (Batch)",
    description="Template to store on printer for efficient batch printing",
    label_size="sbp100375",
    width_mm=25.4,
    height_mm=38.0,
    include_qr=True,
    qr_magnification=5,
    zpl_template="""^XA
^DFE:NETBOX.ZPL^FS
^MMT^PW300^LL450^LS0
^FO24,24^A0N,42,36^FB252,1,0,C^FN1"CABLE_ID"^FS
^FO180,20^BQN,2,5^FN2"QR_URL"^FS
^FO24,75^A0N,22,18^FN3"FROM"^FS
^FO24,100^A0N,20,16^FN4"A_INT"^FS
^FO24,130^A0N,22,18^FN5"TO"^FS
^FO24,155^A0N,20,16^FN6"B_INT"^FS
^FO24,185^GB252,2,2^FS
^FO24,195^A0N,20,16^FN7"TYPE"^FS
^FO24,220^A0N,18,14^FN8"DATE"^FS
^XZ""",
)


# Template for recalling stored format
TEMPLATE_RECALL_FORMAT = """^XA
^XFE:NETBOX.ZPL^FS
^FN1^FD{cable_id}^FS
^FN2^FDLA,{cable_url}^FS
^FN3^FDFrom: {term_a_device}^FS
^FN4^FD  {term_a_interface}^FS
^FN5^FDTo: {term_b_device}^FS
^FN6^FD  {term_b_interface}^FS
^FN7^FD{type} {length}^FS
^FN8^FD{date}^FS
^PQ{quantity}
^XZ"""


# Collection of all default templates
DEFAULT_TEMPLATES = [
    TEMPLATE_SBP100375_FULL,
    TEMPLATE_SBP100375_COMPACT,
    TEMPLATE_SBP100225_STANDARD,
    TEMPLATE_SBP100143_MINIMAL,
    TEMPLATE_SBP100375_TEXT,
]


def get_default_template(label_size: str = "sbp100375") -> TemplateDefinition | None:
    """Get the default template for a given label size.

    Args:
        label_size: TE SBP label size code

    Returns:
        TemplateDefinition for the label size, or None if not found
    """
    for template in DEFAULT_TEMPLATES:
        if template.label_size == label_size:
            return template
    return None


def get_template_by_name(name: str) -> TemplateDefinition | None:
    """Get a template by its name.

    Args:
        name: Template name

    Returns:
        TemplateDefinition with matching name, or None
    """
    for template in DEFAULT_TEMPLATES:
        if template.name == name:
            return template
    return None
