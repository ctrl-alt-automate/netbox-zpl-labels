"""Migration to convert PrintJob from cable FK to GenericForeignKey.

This migration:
1. Adds content_type and object_id fields
2. Migrates existing cable data to the new fields
3. Removes the old cable FK
"""

import django.db.models.deletion
from django.db import migrations, models


def migrate_cable_to_generic(apps, schema_editor):
    """Migrate existing cable FK data to generic relation."""
    PrintJob = apps.get_model("netbox_zpl_labels", "PrintJob")
    ContentType = apps.get_model("contenttypes", "ContentType")

    # Get Cable content type
    cable_ct = ContentType.objects.get(app_label="dcim", model="cable")

    # Update all existing PrintJobs
    for job in PrintJob.objects.filter(cable__isnull=False):
        job.content_type = cable_ct
        job.object_id = job.cable_id
        job.save(update_fields=["content_type", "object_id"])


def reverse_generic_to_cable(apps, schema_editor):
    """Reverse migration: restore cable FK from generic relation."""
    PrintJob = apps.get_model("netbox_zpl_labels", "PrintJob")
    ContentType = apps.get_model("contenttypes", "ContentType")

    cable_ct = ContentType.objects.get(app_label="dcim", model="cable")

    for job in PrintJob.objects.filter(content_type=cable_ct):
        job.cable_id = job.object_id
        job.save(update_fields=["cable_id"])


class Migration(migrations.Migration):

    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("netbox_zpl_labels", "0001_initial"),
    ]

    operations = [
        # Step 1: Add new fields (nullable initially)
        migrations.AddField(
            model_name="printjob",
            name="content_type",
            field=models.ForeignKey(
                help_text="Type of object this label was printed for",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="contenttypes.contenttype",
                verbose_name="object type",
            ),
        ),
        migrations.AddField(
            model_name="printjob",
            name="object_id",
            field=models.PositiveIntegerField(
                null=True,
                verbose_name="object ID",
            ),
        ),
        # Step 2: Migrate data
        migrations.RunPython(
            migrate_cable_to_generic,
            reverse_generic_to_cable,
        ),
        # Step 3: Make fields non-nullable
        migrations.AlterField(
            model_name="printjob",
            name="content_type",
            field=models.ForeignKey(
                help_text="Type of object this label was printed for",
                on_delete=django.db.models.deletion.CASCADE,
                to="contenttypes.contenttype",
                verbose_name="object type",
            ),
        ),
        migrations.AlterField(
            model_name="printjob",
            name="object_id",
            field=models.PositiveIntegerField(
                verbose_name="object ID",
            ),
        ),
        # Step 4: Add index for performance
        migrations.AddIndex(
            model_name="printjob",
            index=models.Index(
                fields=["content_type", "object_id"],
                name="netbox_zpl__content_4a1234_idx",
            ),
        ),
        # Step 5: Remove old cable FK
        migrations.RemoveField(
            model_name="printjob",
            name="cable",
        ),
    ]
