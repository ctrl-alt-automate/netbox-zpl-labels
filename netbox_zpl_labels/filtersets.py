"""Filtersets for NetBox ZPL Labels plugin."""

import django_filters
from dcim.models import Location
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from netbox.filtersets import NetBoxModelFilterSet

from .models import (
    LabelSizeChoices,
    LabelTemplate,
    PrinterDPIChoices,
    PrinterStatusChoices,
    PrintJob,
    ZPLPrinter,
)


class ZPLPrinterFilterSet(NetBoxModelFilterSet):
    """Filterset for ZPL printers."""

    status = django_filters.MultipleChoiceFilter(
        choices=PrinterStatusChoices,
        label=_("Status"),
    )
    dpi = django_filters.MultipleChoiceFilter(
        choices=PrinterDPIChoices,
        label=_("Resolution"),
    )
    location_id = django_filters.ModelMultipleChoiceFilter(
        queryset=Location.objects.all(),
        label=_("Location"),
    )
    location = django_filters.ModelMultipleChoiceFilter(
        queryset=Location.objects.all(),
        field_name="location",
        label=_("Location"),
    )

    class Meta:
        model = ZPLPrinter
        fields = ["id", "name", "host", "port", "status", "dpi", "location_id"]

    def search(self, queryset, name, value):
        """Search by name, host, or description."""
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value) | Q(host__icontains=value) | Q(description__icontains=value)
        )


class LabelTemplateFilterSet(NetBoxModelFilterSet):
    """Filterset for label templates."""

    label_size = django_filters.MultipleChoiceFilter(
        choices=LabelSizeChoices,
        label=_("Label Size"),
    )
    dpi = django_filters.MultipleChoiceFilter(
        choices=PrinterDPIChoices,
        label=_("Resolution"),
    )
    include_qr_code = django_filters.BooleanFilter(
        label=_("Include QR Code"),
    )
    is_default = django_filters.BooleanFilter(
        label=_("Default"),
    )

    class Meta:
        model = LabelTemplate
        fields = ["id", "name", "label_size", "dpi", "include_qr_code", "is_default"]

    def search(self, queryset, name, value):
        """Search by name or description."""
        if not value.strip():
            return queryset
        return queryset.filter(Q(name__icontains=value) | Q(description__icontains=value))


class PrintJobFilterSet(NetBoxModelFilterSet):
    """Filterset for print jobs."""

    printer_id = django_filters.ModelMultipleChoiceFilter(
        queryset=ZPLPrinter.objects.all(),
        field_name="printer",
        label=_("Printer"),
    )
    printer = django_filters.ModelMultipleChoiceFilter(
        queryset=ZPLPrinter.objects.all(),
        field_name="printer",
        label=_("Printer"),
    )
    template_id = django_filters.ModelMultipleChoiceFilter(
        queryset=LabelTemplate.objects.all(),
        field_name="template",
        label=_("Template"),
    )
    template = django_filters.ModelMultipleChoiceFilter(
        queryset=LabelTemplate.objects.all(),
        field_name="template",
        label=_("Template"),
    )
    success = django_filters.BooleanFilter(
        label=_("Success"),
    )
    object_id = django_filters.NumberFilter(
        field_name="object_id",
        label=_("Object ID"),
    )
    content_type = django_filters.CharFilter(
        field_name="content_type__model",
        label=_("Object Type"),
    )

    class Meta:
        model = PrintJob
        fields = ["id", "printer_id", "template_id", "success", "object_id", "content_type"]

    def search(self, queryset, name, value):
        """Search by error message."""
        if not value.strip():
            return queryset
        return queryset.filter(Q(error_message__icontains=value))
