"""Add status tracking fields to ZPLPrinter.

Migration for adding last_checked and last_online fields to track
real-time printer status monitoring.
"""

from django.db import migrations, models


class Migration(migrations.Migration):
    """Add status tracking fields to ZPLPrinter."""

    dependencies = [
        ("netbox_zpl_labels", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="zplprinter",
            name="last_checked",
            field=models.DateTimeField(
                blank=True,
                help_text="Last time the printer status was checked",
                null=True,
                verbose_name="last checked",
            ),
        ),
        migrations.AddField(
            model_name="zplprinter",
            name="last_online",
            field=models.BooleanField(
                blank=True,
                default=None,
                help_text="Online status from last check",
                null=True,
                verbose_name="last online status",
            ),
        ),
    ]
