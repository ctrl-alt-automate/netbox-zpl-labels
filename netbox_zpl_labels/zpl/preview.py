"""Label preview generation using Labelary API.

This module provides preview image generation for ZPL labels
using the free Labelary API (http://labelary.com).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING
from urllib.parse import quote

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@dataclass
class PreviewResult:
    """Result of a preview generation operation.

    Attributes:
        success: Whether preview generation was successful
        image_data: PNG image bytes if successful
        error: Error message if failed
        content_type: MIME type of the image
    """

    success: bool
    image_data: bytes | None = None
    error: str | None = None
    content_type: str = "image/png"


class LabelaryPreview:
    """Client for Labelary ZPL preview API.

    Labelary provides free ZPL rendering without requiring
    a physical printer. Useful for previewing labels before
    printing.
    """

    BASE_URL = "http://api.labelary.com/v1/printers"

    # DPI mapping to Labelary's dpmm parameter
    DPI_TO_DPMM = {
        152: "6dpmm",
        203: "8dpmm",
        300: "12dpmm",
        600: "24dpmm",
    }

    def __init__(
        self,
        dpi: int = 300,
        label_width_inches: float = 1.0,
        label_height_inches: float = 1.5,
    ):
        """Initialize the Labelary preview client.

        Args:
            dpi: Printer DPI (152, 203, 300, or 600)
            label_width_inches: Label width in inches
            label_height_inches: Label height in inches
        """
        self.dpi = dpi
        self.label_width = label_width_inches
        self.label_height = label_height_inches

    @property
    def dpmm(self) -> str:
        """Get Labelary dpmm parameter for current DPI."""
        return self.DPI_TO_DPMM.get(self.dpi, "12dpmm")

    def get_preview_url(self, zpl: str, label_index: int = 0) -> str:
        """Build Labelary API URL for preview.

        Note: This URL can be used directly for GET requests with
        URL-encoded ZPL, but POST is recommended for longer ZPL.

        Args:
            zpl: ZPL code to render
            label_index: Label index (for multi-label formats)

        Returns:
            Labelary API URL
        """
        dimensions = f"{self.label_width}x{self.label_height}"
        return f"{self.BASE_URL}/{self.dpmm}/labels/{dimensions}/{label_index}/"

    def generate_preview(self, zpl: str, label_index: int = 0) -> PreviewResult:
        """Generate a preview image for ZPL code.

        Makes a POST request to Labelary API with the ZPL code
        and returns the rendered PNG image.

        Args:
            zpl: ZPL code to render
            label_index: Label index (for multi-label formats)

        Returns:
            PreviewResult with image data or error
        """
        try:
            import requests  # type: ignore[import-untyped]
        except ImportError:
            return PreviewResult(
                success=False,
                error="requests library not installed (required for preview)",
            )

        url = self.get_preview_url(zpl, label_index)

        try:
            response = requests.post(
                url,
                data=zpl.encode("utf-8"),
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "image/png",
                },
                timeout=30,
            )

            if response.status_code == 200:
                return PreviewResult(
                    success=True,
                    image_data=response.content,
                    content_type=response.headers.get("Content-Type", "image/png"),
                )
            else:
                return PreviewResult(
                    success=False,
                    error=f"Labelary API error: {response.status_code} - {response.text}",
                )

        except requests.exceptions.Timeout:
            return PreviewResult(
                success=False,
                error="Labelary API timeout",
            )
        except requests.exceptions.RequestException as e:
            return PreviewResult(
                success=False,
                error=f"Labelary API request failed: {e}",
            )

    @classmethod
    def mm_to_inches(cls, mm: float) -> float:
        """Convert millimeters to inches.

        Args:
            mm: Value in millimeters

        Returns:
            Value in inches (rounded to 2 decimal places)
        """
        return round(mm / 25.4, 2)


def get_label_preview(
    zpl: str,
    dpi: int = 300,
    width_mm: float = 25.4,
    height_mm: float = 38.0,
) -> PreviewResult:
    """Generate a preview image for ZPL code.

    Convenience function for single preview generation.

    Args:
        zpl: ZPL code to render
        dpi: Printer DPI
        width_mm: Label width in millimeters
        height_mm: Label height in millimeters

    Returns:
        PreviewResult with image data or error
    """
    width_inches = LabelaryPreview.mm_to_inches(width_mm)
    height_inches = LabelaryPreview.mm_to_inches(height_mm)

    client = LabelaryPreview(
        dpi=dpi,
        label_width_inches=width_inches,
        label_height_inches=height_inches,
    )

    return client.generate_preview(zpl)


def get_labelary_url(
    zpl: str,
    dpi: int = 300,
    width_mm: float = 25.4,
    height_mm: float = 38.0,
) -> str:
    """Get Labelary viewer URL for ZPL code.

    Returns a URL to the Labelary web viewer with the ZPL
    code pre-loaded.

    Args:
        zpl: ZPL code to view
        dpi: Printer DPI
        width_mm: Label width in millimeters
        height_mm: Label height in millimeters

    Returns:
        Labelary viewer URL
    """
    width_inches = LabelaryPreview.mm_to_inches(width_mm)
    height_inches = LabelaryPreview.mm_to_inches(height_mm)
    dpmm = LabelaryPreview.DPI_TO_DPMM.get(dpi, "12dpmm")

    # URL encode the ZPL
    encoded_zpl = quote(zpl, safe="")

    return (
        f"http://labelary.com/viewer.html?dpmm={dpmm}&w={width_inches}&h={height_inches}"
        f"&zpl={encoded_zpl}"
    )
