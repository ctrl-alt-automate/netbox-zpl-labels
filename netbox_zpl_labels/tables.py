"""Tables for NetBox ZPL Labels plugin."""

import django_tables2 as tables
from django.utils.translation import gettext_lazy as _
from netbox.tables import ChoiceFieldColumn, NetBoxTable, TagColumn, columns

from .models import LabelTemplate, PrintJob, ZPLPrinter


class ZPLPrinterTable(NetBoxTable):
    """Table for displaying ZPL printers."""

    name = tables.Column(
        linkify=True,
        verbose_name=_("Name"),
    )
    host = tables.Column(
        verbose_name=_("Host"),
    )
    port = tables.Column(
        verbose_name=_("Port"),
    )
    dpi = ChoiceFieldColumn(
        verbose_name=_("Resolution"),
    )
    status = ChoiceFieldColumn(
        verbose_name=_("Status"),
    )
    location = tables.Column(
        linkify=True,
        verbose_name=_("Location"),
    )
    tags = TagColumn()
    actions = columns.ActionsColumn(
        actions=("edit", "delete"),
    )

    class Meta(NetBoxTable.Meta):
        model = ZPLPrinter
        fields = (
            "pk",
            "id",
            "name",
            "host",
            "port",
            "dpi",
            "status",
            "location",
            "description",
            "tags",
            "created",
            "last_updated",
            "actions",
        )
        default_columns = ("name", "host", "port", "dpi", "status", "location")


class LabelTemplateTable(NetBoxTable):
    """Table for displaying label templates."""

    name = tables.Column(
        linkify=True,
        verbose_name=_("Name"),
    )
    label_size = ChoiceFieldColumn(
        verbose_name=_("Label Size"),
    )
    width_mm = tables.Column(
        verbose_name=_("Width (mm)"),
    )
    height_mm = tables.Column(
        verbose_name=_("Height (mm)"),
    )
    dpi = ChoiceFieldColumn(
        verbose_name=_("DPI"),
    )
    include_qr_code = tables.BooleanColumn(
        verbose_name=_("QR Code"),
    )
    is_default = tables.BooleanColumn(
        verbose_name=_("Default"),
    )
    tags = TagColumn()
    actions = columns.ActionsColumn(
        actions=("edit", "delete"),
    )

    class Meta(NetBoxTable.Meta):
        model = LabelTemplate
        fields = (
            "pk",
            "id",
            "name",
            "label_size",
            "width_mm",
            "height_mm",
            "dpi",
            "include_qr_code",
            "qr_magnification",
            "is_default",
            "tags",
            "created",
            "last_updated",
            "actions",
        )
        default_columns = (
            "name",
            "label_size",
            "dpi",
            "include_qr_code",
            "is_default",
        )


class PrintJobTable(NetBoxTable):
    """Table for displaying print job history."""

    id = tables.Column(
        linkify=True,
        verbose_name=_("ID"),
    )
    labeled_object = tables.Column(
        verbose_name=_("Object"),
        accessor="labeled_object",
        linkify=lambda record: record.labeled_object.get_absolute_url() if record.labeled_object else None,
    )
    object_type = tables.Column(
        verbose_name=_("Type"),
        accessor="object_type_name",
    )
    printer = tables.Column(
        linkify=True,
        verbose_name=_("Printer"),
    )
    template = tables.Column(
        linkify=True,
        verbose_name=_("Template"),
    )
    quantity = tables.Column(
        verbose_name=_("Qty"),
    )
    success = tables.BooleanColumn(
        verbose_name=_("Success"),
    )
    printed_by = tables.Column(
        linkify=True,
        verbose_name=_("Printed By"),
    )
    created = tables.DateTimeColumn(
        verbose_name=_("Printed At"),
    )

    class Meta(NetBoxTable.Meta):
        model = PrintJob
        fields = (
            "pk",
            "id",
            "labeled_object",
            "object_type",
            "printer",
            "template",
            "quantity",
            "success",
            "error_message",
            "printed_by",
            "created",
        )
        default_columns = (
            "id",
            "labeled_object",
            "object_type",
            "printer",
            "template",
            "success",
            "created",
        )


class CableLabelTable(NetBoxTable):
    """Simplified table for cable selection in bulk print."""

    pk = columns.ToggleColumn()
    label = tables.Column(
        accessor="label",
        verbose_name=_("Cable Label"),
    )
    a_terminations = tables.Column(
        accessor="a_terminations",
        verbose_name=_("Termination A"),
        orderable=False,
    )
    b_terminations = tables.Column(
        accessor="b_terminations",
        verbose_name=_("Termination B"),
        orderable=False,
    )
    type = tables.Column(
        verbose_name=_("Type"),
    )
    length = tables.Column(
        verbose_name=_("Length"),
    )

    class Meta(NetBoxTable.Meta):
        model = None  # Will be set dynamically
        fields = (
            "pk",
            "label",
            "a_terminations",
            "b_terminations",
            "type",
            "length",
        )
        default_columns = fields
