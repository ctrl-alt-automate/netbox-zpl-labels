"""Initial migration for NetBox ZPL Labels plugin."""

import django.db.models.deletion
import taggit.managers
import utilities.json
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    """Create initial tables for ZPL Labels plugin."""

    initial = True

    dependencies = [
        ("dcim", "0001_initial"),
        ("extras", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ZPLPrinter",
            fields=[
                (
                    "id",
                    models.BigAutoField(auto_created=True, primary_key=True, serialize=False),
                ),
                ("created", models.DateTimeField(auto_now_add=True, null=True)),
                ("last_updated", models.DateTimeField(auto_now=True, null=True)),
                (
                    "custom_field_data",
                    models.JSONField(
                        blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        help_text="Unique name for this printer",
                        max_length=100,
                        unique=True,
                        verbose_name="name",
                    ),
                ),
                (
                    "host",
                    models.CharField(
                        help_text="IP address or hostname",
                        max_length=255,
                        verbose_name="host",
                    ),
                ),
                (
                    "port",
                    models.PositiveIntegerField(
                        default=9100,
                        help_text="TCP port for ZPL communication (default: 9100)",
                        verbose_name="port",
                    ),
                ),
                (
                    "dpi",
                    models.PositiveIntegerField(
                        choices=[(203, "203 DPI (8 dpmm)"), (300, "300 DPI (12 dpmm)")],
                        default=300,
                        help_text="Printer resolution in DPI",
                        verbose_name="resolution",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("active", "Active"),
                            ("offline", "Offline"),
                            ("maintenance", "Maintenance"),
                        ],
                        default="active",
                        max_length=50,
                        verbose_name="status",
                    ),
                ),
                (
                    "description",
                    models.CharField(blank=True, max_length=200, verbose_name="description"),
                ),
                ("comments", models.TextField(blank=True, verbose_name="comments")),
                (
                    "location",
                    models.ForeignKey(
                        blank=True,
                        help_text="Physical location of the printer",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="zpl_printers",
                        to="dcim.location",
                        verbose_name="location",
                    ),
                ),
                (
                    "tags",
                    taggit.managers.TaggableManager(through="extras.TaggedItem", to="extras.Tag"),
                ),
            ],
            options={
                "verbose_name": "ZPL printer",
                "verbose_name_plural": "ZPL printers",
                "ordering": ["name"],
            },
        ),
        migrations.AddConstraint(
            model_name="zplprinter",
            constraint=models.UniqueConstraint(
                fields=("host", "port"),
                name="netbox_zpl_labels_zplprinter_unique_endpoint",
            ),
        ),
        migrations.CreateModel(
            name="LabelTemplate",
            fields=[
                (
                    "id",
                    models.BigAutoField(auto_created=True, primary_key=True, serialize=False),
                ),
                ("created", models.DateTimeField(auto_now_add=True, null=True)),
                ("last_updated", models.DateTimeField(auto_now=True, null=True)),
                (
                    "custom_field_data",
                    models.JSONField(
                        blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder
                    ),
                ),
                (
                    "name",
                    models.CharField(max_length=100, unique=True, verbose_name="name"),
                ),
                (
                    "description",
                    models.TextField(blank=True, verbose_name="description"),
                ),
                (
                    "label_size",
                    models.CharField(
                        choices=[
                            ("sbp050100", "SBP050100 (8.5mm × 25.4mm)"),
                            ("sbp100143", "SBP100143 (12.7mm × 36.5mm)"),
                            ("sbp100225", "SBP100225 (19.1mm × 57.2mm)"),
                            ("sbp100375", "SBP100375 (25.4mm × 95.3mm)"),
                            ("sbp200375", "SBP200375 (25.4mm × 95.3mm wide)"),
                        ],
                        help_text="TE Raychem SBP label type",
                        max_length=50,
                        verbose_name="label size",
                    ),
                ),
                (
                    "width_mm",
                    models.DecimalField(
                        decimal_places=1,
                        help_text="Printable area width in millimeters",
                        max_digits=5,
                        verbose_name="print width (mm)",
                    ),
                ),
                (
                    "height_mm",
                    models.DecimalField(
                        decimal_places=1,
                        help_text="Printable area height in millimeters",
                        max_digits=5,
                        verbose_name="print height (mm)",
                    ),
                ),
                (
                    "dpi",
                    models.PositiveIntegerField(
                        choices=[(203, "203 DPI (8 dpmm)"), (300, "300 DPI (12 dpmm)")],
                        default=300,
                        verbose_name="target DPI",
                    ),
                ),
                (
                    "zpl_template",
                    models.TextField(
                        help_text=(
                            "ZPL code with {variable} placeholders. "
                            "Available: {cable_id}, {cable_url}, {term_a_device}, "
                            "{term_a_interface}, {term_b_device}, {term_b_interface}, "
                            "{length}, {color}, {type}, {description}, {date}"
                        ),
                        verbose_name="ZPL template",
                    ),
                ),
                (
                    "include_qr_code",
                    models.BooleanField(
                        default=True,
                        help_text="Include QR code linking to NetBox cable page",
                        verbose_name="include QR code",
                    ),
                ),
                (
                    "qr_magnification",
                    models.PositiveIntegerField(
                        default=4,
                        help_text="QR code size (1-10, recommended: 4-5 for cable labels)",
                        verbose_name="QR magnification",
                    ),
                ),
                (
                    "is_default",
                    models.BooleanField(
                        default=False,
                        help_text="Use this template by default",
                        verbose_name="default template",
                    ),
                ),
                ("comments", models.TextField(blank=True, verbose_name="comments")),
                (
                    "tags",
                    taggit.managers.TaggableManager(through="extras.TaggedItem", to="extras.Tag"),
                ),
            ],
            options={
                "verbose_name": "label template",
                "verbose_name_plural": "label templates",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="PrintJob",
            fields=[
                (
                    "id",
                    models.BigAutoField(auto_created=True, primary_key=True, serialize=False),
                ),
                ("created", models.DateTimeField(auto_now_add=True, null=True)),
                ("last_updated", models.DateTimeField(auto_now=True, null=True)),
                (
                    "custom_field_data",
                    models.JSONField(
                        blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder
                    ),
                ),
                (
                    "quantity",
                    models.PositiveIntegerField(
                        default=1,
                        help_text="Number of labels printed",
                        verbose_name="quantity",
                    ),
                ),
                (
                    "zpl_content",
                    models.TextField(
                        help_text="Generated ZPL code sent to printer",
                        verbose_name="ZPL content",
                    ),
                ),
                (
                    "success",
                    models.BooleanField(default=False, verbose_name="success"),
                ),
                (
                    "error_message",
                    models.TextField(blank=True, verbose_name="error message"),
                ),
                ("comments", models.TextField(blank=True, verbose_name="comments")),
                (
                    "cable",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="zpl_print_jobs",
                        to="dcim.cable",
                        verbose_name="cable",
                    ),
                ),
                (
                    "printer",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="print_jobs",
                        to="netbox_zpl_labels.zplprinter",
                        verbose_name="printer",
                    ),
                ),
                (
                    "template",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="print_jobs",
                        to="netbox_zpl_labels.labeltemplate",
                        verbose_name="template",
                    ),
                ),
                (
                    "printed_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="zpl_print_jobs",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="printed by",
                    ),
                ),
                (
                    "tags",
                    taggit.managers.TaggableManager(through="extras.TaggedItem", to="extras.Tag"),
                ),
            ],
            options={
                "verbose_name": "print job",
                "verbose_name_plural": "print jobs",
                "ordering": ["-created"],
            },
        ),
    ]
