"""Forms for NetBox ZPL Labels plugin."""

from dcim.models import Location
from django import forms
from django.utils.translation import gettext_lazy as _
from netbox.forms import (
    NetBoxModelBulkEditForm,
    NetBoxModelFilterSetForm,
    NetBoxModelForm,
    NetBoxModelImportForm,
)
from utilities.forms.fields import (
    DynamicModelChoiceField,
    DynamicModelMultipleChoiceField,
    TagFilterField,
)
from utilities.forms.rendering import FieldSet

from .models import (
    LabelSizeChoices,
    LabelTemplate,
    PrinterDPIChoices,
    PrinterStatusChoices,
    PrintJob,
    ZPLPrinter,
)

#
# ZPLPrinter Forms
#


class ZPLPrinterForm(NetBoxModelForm):
    """Form for creating/editing ZPL printers."""

    location = DynamicModelChoiceField(
        queryset=Location.objects.all(),
        required=False,
        label=_("Location"),
    )

    fieldsets = (
        FieldSet("name", "description", name=_("Printer")),
        FieldSet("host", "port", "dpi", "status", name=_("Connection")),
        FieldSet("location", name=_("Assignment")),
        FieldSet("tags", name=_("Tags")),
    )

    class Meta:
        model = ZPLPrinter
        fields = [
            "name",
            "description",
            "host",
            "port",
            "dpi",
            "status",
            "location",
            "comments",
            "tags",
        ]


class ZPLPrinterFilterForm(NetBoxModelFilterSetForm):
    """Filter form for ZPL printer list."""

    model = ZPLPrinter

    status = forms.MultipleChoiceField(
        choices=PrinterStatusChoices,
        required=False,
        label=_("Status"),
    )
    dpi = forms.MultipleChoiceField(
        choices=PrinterDPIChoices,
        required=False,
        label=_("Resolution"),
    )
    location_id = DynamicModelMultipleChoiceField(
        queryset=Location.objects.all(),
        required=False,
        label=_("Location"),
    )
    tag = TagFilterField(model)


class ZPLPrinterBulkEditForm(NetBoxModelBulkEditForm):
    """Bulk edit form for ZPL printers."""

    model = ZPLPrinter

    status = forms.ChoiceField(
        choices=[("", "---------")] + list(PrinterStatusChoices),
        required=False,
        label=_("Status"),
    )
    dpi = forms.ChoiceField(
        choices=[("", "---------")] + list(PrinterDPIChoices),
        required=False,
        label=_("Resolution"),
    )
    location = DynamicModelChoiceField(
        queryset=Location.objects.all(),
        required=False,
        label=_("Location"),
    )
    description = forms.CharField(
        max_length=200,
        required=False,
        label=_("Description"),
    )

    fieldsets = (FieldSet("status", "dpi", "location", "description"),)
    nullable_fields = ["location", "description"]


class ZPLPrinterImportForm(NetBoxModelImportForm):
    """Import form for ZPL printers."""

    class Meta:
        model = ZPLPrinter
        fields = ["name", "host", "port", "dpi", "status", "description"]


#
# LabelTemplate Forms
#


class LabelTemplateForm(NetBoxModelForm):
    """Form for creating/editing label templates."""

    zpl_template = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "rows": 20,
                "class": "font-monospace",
                "style": "font-size: 0.85rem;",
                "placeholder": "^XA\n^FO20,20^A0N,28,24^FD{cable_id}^FS\n^XZ",
            }
        ),
        label=_("ZPL Template"),
        help_text=_(
            "ZPL code with {variable} placeholders. Available variables: "
            "{cable_id}, {cable_url}, {term_a_device}, {term_a_interface}, "
            "{term_b_device}, {term_b_interface}, {length}, {color}, "
            "{type}, {description}, {date}"
        ),
    )

    fieldsets = (
        FieldSet("name", "description", "is_default", name=_("Template")),
        FieldSet("label_size", "width_mm", "height_mm", "dpi", name=_("Dimensions")),
        FieldSet("include_qr_code", "qr_magnification", "zpl_template", name=_("Content")),
        FieldSet("tags", name=_("Tags")),
    )

    class Meta:
        model = LabelTemplate
        fields = [
            "name",
            "description",
            "label_size",
            "width_mm",
            "height_mm",
            "dpi",
            "zpl_template",
            "include_qr_code",
            "qr_magnification",
            "is_default",
            "comments",
            "tags",
        ]


class LabelTemplateFilterForm(NetBoxModelFilterSetForm):
    """Filter form for label template list."""

    model = LabelTemplate

    label_size = forms.MultipleChoiceField(
        choices=LabelSizeChoices,
        required=False,
        label=_("Label Size"),
    )
    dpi = forms.MultipleChoiceField(
        choices=PrinterDPIChoices,
        required=False,
        label=_("Resolution"),
    )
    include_qr_code = forms.NullBooleanField(
        required=False,
        label=_("Include QR Code"),
        widget=forms.Select(
            choices=[
                ("", "---------"),
                ("true", _("Yes")),
                ("false", _("No")),
            ]
        ),
    )
    is_default = forms.NullBooleanField(
        required=False,
        label=_("Default"),
        widget=forms.Select(
            choices=[
                ("", "---------"),
                ("true", _("Yes")),
                ("false", _("No")),
            ]
        ),
    )
    tag = TagFilterField(model)


class LabelTemplateBulkEditForm(NetBoxModelBulkEditForm):
    """Bulk edit form for label templates."""

    model = LabelTemplate

    dpi = forms.ChoiceField(
        choices=[("", "---------")] + list(PrinterDPIChoices),
        required=False,
        label=_("Resolution"),
    )
    include_qr_code = forms.NullBooleanField(
        required=False,
        label=_("Include QR Code"),
    )
    qr_magnification = forms.IntegerField(
        min_value=1,
        max_value=10,
        required=False,
        label=_("QR Magnification"),
    )

    fieldsets = (FieldSet("dpi", "include_qr_code", "qr_magnification"),)
    nullable_fields: list[str] = []


class LabelTemplateImportForm(NetBoxModelImportForm):
    """Import form for label templates (CSV/JSON import)."""

    class Meta:
        model = LabelTemplate
        fields = [
            "name",
            "description",
            "label_size",
            "width_mm",
            "height_mm",
            "dpi",
            "zpl_template",
            "include_qr_code",
            "qr_magnification",
            "is_default",
        ]


#
# PrintJob Forms
#


class PrintJobFilterForm(NetBoxModelFilterSetForm):
    """Filter form for print job list."""

    model = PrintJob

    printer_id = DynamicModelMultipleChoiceField(
        queryset=ZPLPrinter.objects.all(),
        required=False,
        label=_("Printer"),
    )
    template_id = DynamicModelMultipleChoiceField(
        queryset=LabelTemplate.objects.all(),
        required=False,
        label=_("Template"),
    )
    success = forms.NullBooleanField(
        required=False,
        label=_("Success"),
        widget=forms.Select(
            choices=[
                ("", "---------"),
                ("true", _("Yes")),
                ("false", _("No")),
            ]
        ),
    )


#
# Cable Label Printing Forms
#


class PrintLabelForm(forms.Form):
    """Form for printing a single cable label."""

    printer = DynamicModelChoiceField(
        queryset=ZPLPrinter.objects.filter(status="active"),
        label=_("Printer"),
        help_text=_("Select the printer to use"),
    )
    template = DynamicModelChoiceField(
        queryset=LabelTemplate.objects.all(),
        label=_("Label Template"),
        help_text=_("Select the label template"),
    )
    quantity = forms.IntegerField(
        min_value=1,
        max_value=100,
        initial=1,
        label=_("Quantity"),
        help_text=_("Number of labels to print (1-100)"),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default template
        default_template = LabelTemplate.objects.filter(is_default=True).first()
        if default_template:
            self.fields["template"].initial = default_template


class BulkPrintLabelForm(forms.Form):
    """Form for bulk printing cable labels."""

    pk = forms.MultipleChoiceField(
        widget=forms.MultipleHiddenInput,
        required=True,
    )
    printer = DynamicModelChoiceField(
        queryset=ZPLPrinter.objects.filter(status="active"),
        label=_("Printer"),
        help_text=_("Select the printer to use"),
    )
    template = DynamicModelChoiceField(
        queryset=LabelTemplate.objects.all(),
        label=_("Label Template"),
        help_text=_("Select the label template"),
    )
    quantity_per_cable = forms.IntegerField(
        min_value=1,
        max_value=10,
        initial=1,
        label=_("Labels per Cable"),
        help_text=_("Number of labels to print for each cable"),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default template
        default_template = LabelTemplate.objects.filter(is_default=True).first()
        if default_template:
            self.fields["template"].initial = default_template


class PreviewLabelForm(forms.Form):
    """Form for previewing a label without printing."""

    template = DynamicModelChoiceField(
        queryset=LabelTemplate.objects.all(),
        label=_("Label Template"),
        required=True,
    )
