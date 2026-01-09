"""Label preview generation using Labelary API or BinaryKits.Zpl.

This module provides preview image generation for ZPL labels
using either:
- Labelary API (http://labelary.com) - online service
- BinaryKits.Zpl (self-hosted Docker) - local service
"""

from __future__ import annotations

import base64
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


class BinaryKitsPreview:
    """Client for BinaryKits.Zpl preview API.

    BinaryKits.Zpl is an open-source ZPL renderer that can be
    self-hosted using Docker. This eliminates the need for
    external API calls to Labelary.

    Docker: yipingruan/binarykits-zpl
    """

    # DPI to dpmm conversion
    DPI_TO_DPMM = {
        152: 6,
        203: 8,
        300: 12,
        600: 24,
    }

    def __init__(
        self,
        base_url: str = "http://localhost:4040",
        dpi: int = 300,
        label_width_mm: float = 50.0,
        label_height_mm: float = 30.0,
    ):
        """Initialize the BinaryKits preview client.

        Args:
            base_url: URL to BinaryKits.Zpl API (e.g., http://localhost:4040)
            dpi: Printer DPI (152, 203, 300, or 600)
            label_width_mm: Label width in millimeters
            label_height_mm: Label height in millimeters
        """
        self.base_url = base_url.rstrip("/")
        self.dpi = dpi
        self.label_width_mm = label_width_mm
        self.label_height_mm = label_height_mm

    @property
    def dpmm(self) -> int:
        """Get dpmm value for current DPI."""
        return self.DPI_TO_DPMM.get(self.dpi, 12)

    def generate_preview(self, zpl: str) -> PreviewResult:
        """Generate a preview image for ZPL code.

        Makes a POST request to BinaryKits.Zpl API with the ZPL code
        and returns the rendered PNG image.

        Args:
            zpl: ZPL code to render

        Returns:
            PreviewResult with image data or error
        """
        try:
            import requests
        except ImportError:
            return PreviewResult(
                success=False,
                error="requests library not installed (required for preview)",
            )

        url = f"{self.base_url}/api/v1/viewer"
        payload = {
            "zplData": zpl,
            "printDensityDpmm": self.dpmm,
            "labelWidth": self.label_width_mm,
            "labelHeight": self.label_height_mm,
        }

        try:
            response = requests.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30,
            )

            if response.status_code == 200:
                data = response.json()
                labels = data.get("labels", [])
                if labels and labels[0].get("imageBase64"):
                    image_data = base64.b64decode(labels[0]["imageBase64"])
                    return PreviewResult(
                        success=True,
                        image_data=image_data,
                        content_type="image/png",
                    )
                else:
                    return PreviewResult(
                        success=False,
                        error="BinaryKits API returned no image data",
                    )
            else:
                return PreviewResult(
                    success=False,
                    error=f"BinaryKits API error: {response.status_code} - {response.text}",
                )

        except requests.exceptions.Timeout:
            return PreviewResult(
                success=False,
                error="BinaryKits API timeout",
            )
        except requests.exceptions.RequestException as e:
            return PreviewResult(
                success=False,
                error=f"BinaryKits API request failed: {e}",
            )
        except (ValueError, KeyError) as e:
            return PreviewResult(
                success=False,
                error=f"BinaryKits API response parse error: {e}",
            )


def get_label_preview(
    zpl: str,
    dpi: int = 300,
    width_mm: float = 25.4,
    height_mm: float = 38.0,
) -> PreviewResult:
    """Generate a preview image for ZPL code.

    Uses plugin settings to determine which backend to use:
    - 'labelary': Labelary online API (default)
    - 'binarykits': BinaryKits.Zpl self-hosted Docker

    Args:
        zpl: ZPL code to render
        dpi: Printer DPI
        width_mm: Label width in millimeters
        height_mm: Label height in millimeters

    Returns:
        PreviewResult with image data or error
    """
    # Get plugin settings
    from netbox.plugins import get_plugin_config

    # get_plugin_config requires plugin name AND parameter name
    preview_backend = get_plugin_config("netbox_zpl_labels", "preview_backend")
    preview_url = get_plugin_config("netbox_zpl_labels", "preview_url")

    if preview_backend == "binarykits":
        # Use BinaryKits.Zpl (self-hosted Docker)
        base_url = preview_url or "http://localhost:4040"
        client = BinaryKitsPreview(
            base_url=base_url,
            dpi=dpi,
            label_width_mm=width_mm,
            label_height_mm=height_mm,
        )
        return client.generate_preview(zpl)
    else:
        # Use Labelary (online API) - default
        width_inches = LabelaryPreview.mm_to_inches(width_mm)
        height_inches = LabelaryPreview.mm_to_inches(height_mm)

        labelary_client = LabelaryPreview(
            dpi=dpi,
            label_width_inches=width_inches,
            label_height_inches=height_inches,
        )
        return labelary_client.generate_preview(zpl)


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
