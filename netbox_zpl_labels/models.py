"""Data models for NetBox ZPL Labels plugin."""

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from netbox.models import NetBoxModel
from utilities.choices import ChoiceSet


# Supported object types for label printing
LABELABLE_MODELS = [
    "dcim.cable",
    "dcim.device",
    "dcim.rack",
    "dcim.module",
    "dcim.location",
    "dcim.site",
    "circuits.circuit",
    "dcim.powerfeed",
    "dcim.powerpanel",
]


class PrinterStatusChoices(ChoiceSet):
    """Choices for printer operational status."""

    key = "ZPLPrinter.status"

    STATUS_ACTIVE = "active"
    STATUS_OFFLINE = "offline"
    STATUS_MAINTENANCE = "maintenance"

    CHOICES = [
        (STATUS_ACTIVE, _("Active"), "green"),
        (STATUS_OFFLINE, _("Offline"), "red"),
        (STATUS_MAINTENANCE, _("Maintenance"), "orange"),
    ]


class PrinterDPIChoices(ChoiceSet):
    """Choices for printer resolution."""

    key = "ZPLPrinter.dpi"

    DPI_203 = 203
    DPI_300 = 300

    CHOICES = [
        (DPI_203, _("203 DPI (8 dpmm)"), "blue"),
        (DPI_300, _("300 DPI (12 dpmm)"), "green"),
    ]


class LabelSizeChoices(ChoiceSet):
    """Choices for TE Raychem SBP label sizes."""

    key = "LabelTemplate.label_size"

    SBP050100 = "sbp050100"
    SBP100143 = "sbp100143"
    SBP100225 = "sbp100225"
    SBP100375 = "sbp100375"
    SBP200375 = "sbp200375"

    CHOICES = [
        (SBP050100, _("SBP050100 (8.5mm × 25.4mm)"), "gray"),
        (SBP100143, _("SBP100143 (12.7mm × 36.5mm)"), "blue"),
        (SBP100225, _("SBP100225 (19.1mm × 57.2mm)"), "cyan"),
        (SBP100375, _("SBP100375 (25.4mm × 95.3mm)"), "purple"),
        (SBP200375, _("SBP200375 (25.4mm × 95.3mm wide)"), "purple"),
    ]


# Label dimensions lookup (print_width_mm, print_height_mm, total_height_mm)
LABEL_DIMENSIONS = {
    LabelSizeChoices.SBP050100: (8.5, 12.0, 25.4),
    LabelSizeChoices.SBP100143: (12.7, 18.0, 36.5),
    LabelSizeChoices.SBP100225: (19.1, 25.0, 57.2),
    LabelSizeChoices.SBP100375: (25.4, 38.0, 95.3),
    LabelSizeChoices.SBP200375: (25.4, 38.0, 95.3),
}


class ZPLPrinter(NetBoxModel):
    """Model representing a Zebra ZPL thermal printer.

    Stores configuration for direct TCP/IP printing to Zebra
    printers via port 9100.
    """

    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("name"),
        help_text=_("Unique name for this printer"),
    )
    host = models.CharField(
        max_length=255,
        verbose_name=_("host"),
        help_text=_("IP address or hostname"),
    )
    port = models.PositiveIntegerField(
        default=9100,
        verbose_name=_("port"),
        help_text=_("TCP port for ZPL communication (default: 9100)"),
        validators=[MinValueValidator(1), MaxValueValidator(65535)],
    )
    dpi = models.PositiveIntegerField(
        choices=PrinterDPIChoices,
        default=PrinterDPIChoices.DPI_300,
        verbose_name=_("resolution"),
        help_text=_("Printer resolution in DPI"),
    )
    status = models.CharField(
        max_length=50,
        choices=PrinterStatusChoices,
        default=PrinterStatusChoices.STATUS_ACTIVE,
        verbose_name=_("status"),
    )
    location = models.ForeignKey(
        to="dcim.Location",
        on_delete=models.SET_NULL,
        related_name="zpl_printers",
        blank=True,
        null=True,
        verbose_name=_("location"),
        help_text=_("Physical location of the printer"),
    )
    description = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("description"),
    )
    last_checked = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("last checked"),
        help_text=_("Last time the printer status was checked"),
    )
    last_online = models.BooleanField(
        default=None,
        blank=True,
        null=True,
        verbose_name=_("last online status"),
        help_text=_("Online status from last check"),
    )
    comments = models.TextField(
        blank=True,
        verbose_name=_("comments"),
    )

    class Meta:
        ordering = ["name"]
        verbose_name = _("ZPL printer")
        verbose_name_plural = _("ZPL printers")
        constraints = [
            models.UniqueConstraint(
                fields=["host", "port"],
                name="%(app_label)s_%(class)s_unique_endpoint",
            )
        ]

    def __str__(self) -> str:
        return str(self.name)

    def clean(self) -> None:
        """Validate printer configuration."""
        super().clean()

        # Validate host is not empty or whitespace-only
        if self.host and not self.host.strip():
            raise ValidationError({"host": _("Host cannot be empty or whitespace only.")})

        # Strip whitespace from host
        if self.host:
            self.host = self.host.strip()

    def get_absolute_url(self) -> str:
        return str(reverse("plugins:netbox_zpl_labels:zplprinter", args=[self.pk]))

    def get_status_color(self) -> str:
        return str(PrinterStatusChoices.colors.get(self.status, "gray"))

    def clone(self) -> dict:
        """Return a dictionary of attributes for cloning this printer.

        Used by NetBox's clone view to pre-populate the form.
        """
        return {
            "port": self.port,
            "dpi": self.dpi,
            "status": self.status,
            "location": self.location,
            # Note: name and host are not cloned to force unique values
        }

    @property
    def dots_per_mm(self) -> float:
        """Return dots per millimeter for this printer's DPI."""
        return float(self.dpi) / 25.4

    def update_status(self, online: bool) -> None:
        """Update the printer's last checked status.

        Args:
            online: Whether the printer was online during the check
        """
        from django.utils import timezone

        self.last_checked = timezone.now()
        self.last_online = online
        self.save(update_fields=["last_checked", "last_online"])


class LabelTemplate(NetBoxModel):
    """Model representing a ZPL label template.

    Templates define the layout and ZPL code structure for cable labels.
    Support placeholders like {cable_id}, {cable_url}, {term_a_device}, etc.
    """

    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("name"),
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("description"),
    )
    label_size = models.CharField(
        max_length=50,
        choices=LabelSizeChoices,
        verbose_name=_("label size"),
        help_text=_("TE Raychem SBP label type"),
    )
    width_mm = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        verbose_name=_("print width (mm)"),
        help_text=_("Printable area width in millimeters"),
    )
    height_mm = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        verbose_name=_("print height (mm)"),
        help_text=_("Printable area height in millimeters"),
    )
    dpi = models.PositiveIntegerField(
        choices=PrinterDPIChoices,
        default=PrinterDPIChoices.DPI_300,
        verbose_name=_("target DPI"),
    )
    zpl_template = models.TextField(
        verbose_name=_("ZPL template"),
        help_text=_(
            "ZPL code with {variable} placeholders. "
            "Available: {cable_id}, {cable_url}, {term_a_device}, "
            "{term_a_interface}, {term_b_device}, {term_b_interface}, "
            "{length}, {color}, {type}, {description}, {date}"
        ),
    )
    include_qr_code = models.BooleanField(
        default=True,
        verbose_name=_("include QR code"),
        help_text=_("Include QR code linking to NetBox cable page"),
    )
    qr_magnification = models.PositiveIntegerField(
        default=4,
        verbose_name=_("QR magnification"),
        help_text=_("QR code size (1-10, recommended: 4-5 for cable labels)"),
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )
    is_default = models.BooleanField(
        default=False,
        verbose_name=_("default template"),
        help_text=_("Use this template by default"),
    )
    comments = models.TextField(
        blank=True,
        verbose_name=_("comments"),
    )

    class Meta:
        ordering = ["name"]
        verbose_name = _("label template")
        verbose_name_plural = _("label templates")

    def __str__(self) -> str:
        return str(self.name)

    def get_absolute_url(self) -> str:
        return str(reverse("plugins:netbox_zpl_labels:labeltemplate", args=[self.pk]))

    def clean(self) -> None:
        """Validate template configuration."""
        from .zpl.generator import validate_zpl_template

        super().clean()

        # Validate ZPL template structure
        if self.zpl_template:
            zpl = self.zpl_template.strip()
            if not zpl.startswith("^XA"):
                raise ValidationError(
                    {"zpl_template": _("ZPL template must start with ^XA (format start).")}
                )
            if not zpl.endswith("^XZ"):
                raise ValidationError(
                    {"zpl_template": _("ZPL template must end with ^XZ (format end).")}
                )

            # Check for dangerous ZPL commands
            is_safe, dangerous_commands = validate_zpl_template(zpl)
            if not is_safe:
                raise ValidationError(
                    {
                        "zpl_template": _(
                            "Template contains dangerous ZPL commands that are not "
                            "allowed: %(commands)s"
                        )
                        % {"commands": ", ".join(dangerous_commands)}
                    }
                )

        # Validate dimensions are positive
        if self.width_mm is not None and self.width_mm <= 0:
            raise ValidationError({"width_mm": _("Width must be greater than 0.")})
        if self.height_mm is not None and self.height_mm <= 0:
            raise ValidationError({"height_mm": _("Height must be greater than 0.")})

    def save(self, *args, **kwargs):
        """Ensure only one default template exists."""
        if self.is_default:
            LabelTemplate.objects.filter(is_default=True).exclude(pk=self.pk).update(
                is_default=False
            )
        super().save(*args, **kwargs)

    def clone(self) -> dict:
        """Return a dictionary of attributes for cloning this template.

        Used by NetBox's clone view to pre-populate the form.
        """
        return {
            "label_size": self.label_size,
            "width_mm": self.width_mm,
            "height_mm": self.height_mm,
            "dpi": self.dpi,
            "zpl_template": self.zpl_template,
            "include_qr_code": self.include_qr_code,
            "qr_magnification": self.qr_magnification,
            # Note: name, is_default, and description are not cloned
            # to force the user to provide unique values
        }

    @property
    def width_dots(self) -> int:
        """Return width in printer dots."""
        return int(float(self.width_mm) * self.dpi / 25.4)

    @property
    def height_dots(self) -> int:
        """Return height in printer dots."""
        return int(float(self.height_mm) * self.dpi / 25.4)


class PrintJob(NetBoxModel):
    """Model tracking print job history.

    Records all label print operations for auditing and troubleshooting.
    Supports printing labels for various DCIM objects via GenericForeignKey.
    """

    # Generic relation to support multiple object types
    content_type = models.ForeignKey(
        to=ContentType,
        on_delete=models.CASCADE,
        verbose_name=_("object type"),
        help_text=_("Type of object this label was printed for"),
    )
    object_id = models.PositiveIntegerField(
        verbose_name=_("object ID"),
    )
    labeled_object = GenericForeignKey("content_type", "object_id")

    printer = models.ForeignKey(
        to=ZPLPrinter,
        on_delete=models.SET_NULL,
        null=True,
        related_name="print_jobs",
        verbose_name=_("printer"),
    )
    template = models.ForeignKey(
        to=LabelTemplate,
        on_delete=models.SET_NULL,
        null=True,
        related_name="print_jobs",
        verbose_name=_("template"),
    )
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name=_("quantity"),
        help_text=_("Number of labels printed"),
        validators=[MinValueValidator(1), MaxValueValidator(100)],
    )
    zpl_content = models.TextField(
        verbose_name=_("ZPL content"),
        help_text=_("Generated ZPL code sent to printer"),
    )
    success = models.BooleanField(
        default=False,
        verbose_name=_("success"),
    )
    error_message = models.TextField(
        blank=True,
        verbose_name=_("error message"),
    )
    printed_by = models.ForeignKey(
        to="users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="zpl_print_jobs",
        verbose_name=_("printed by"),
    )
    comments = models.TextField(
        blank=True,
        verbose_name=_("comments"),
    )

    class Meta:
        ordering = ["-created"]
        verbose_name = _("print job")
        verbose_name_plural = _("print jobs")
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]

    def __str__(self) -> str:
        status = _("OK") if self.success else _("FAILED")
        obj_str = str(self.labeled_object) if self.labeled_object else f"#{self.object_id}"
        return f"Print #{self.pk} - {obj_str} [{status}]"

    def get_absolute_url(self) -> str:
        return str(reverse("plugins:netbox_zpl_labels:printjob", args=[self.pk]))

    @property
    def cable(self):
        """Backwards compatibility: return labeled_object if it's a Cable."""
        if self.content_type and self.content_type.model == "cable":
            return self.labeled_object
        return None

    @property
    def object_type_name(self) -> str:
        """Return human-readable name of the object type."""
        if self.content_type:
            return self.content_type.model_class()._meta.verbose_name.title()
        return ""
