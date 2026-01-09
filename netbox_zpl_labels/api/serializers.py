"""API serializers for NetBox ZPL Labels plugin."""

from dcim.models import Cable
from netbox.api.serializers import NetBoxModelSerializer, WritableNestedSerializer
from rest_framework import serializers

from ..models import LabelTemplate, PrintJob, ZPLPrinter


class NestedCableSerializer(WritableNestedSerializer):
    """Nested serializer for Cable (simplified for plugin use)."""

    url = serializers.HyperlinkedIdentityField(view_name="dcim-api:cable-detail")

    class Meta:
        model = Cable
        fields = ["id", "url", "display", "label"]

#
# Nested Serializers
#


class NestedZPLPrinterSerializer(WritableNestedSerializer):
    """Nested serializer for ZPLPrinter."""

    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:netbox_zpl_labels-api:zplprinter-detail"
    )

    class Meta:
        model = ZPLPrinter
        fields = ["id", "url", "display", "name", "host", "port", "status"]


class NestedLabelTemplateSerializer(WritableNestedSerializer):
    """Nested serializer for LabelTemplate."""

    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:netbox_zpl_labels-api:labeltemplate-detail"
    )

    class Meta:
        model = LabelTemplate
        fields = ["id", "url", "display", "name", "label_size", "is_default"]


class NestedPrintJobSerializer(WritableNestedSerializer):
    """Nested serializer for PrintJob."""

    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:netbox_zpl_labels-api:printjob-detail"
    )

    class Meta:
        model = PrintJob
        fields = ["id", "url", "display", "success", "created"]


#
# Full Serializers
#


class ZPLPrinterSerializer(NetBoxModelSerializer):
    """Full serializer for ZPLPrinter."""

    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:netbox_zpl_labels-api:zplprinter-detail"
    )

    class Meta:
        model = ZPLPrinter
        fields = [
            "id",
            "url",
            "display",
            "name",
            "host",
            "port",
            "dpi",
            "status",
            "location",
            "description",
            "comments",
            "tags",
            "custom_fields",
            "created",
            "last_updated",
        ]
        brief_fields = ["id", "url", "display", "name", "host", "status"]


class LabelTemplateSerializer(NetBoxModelSerializer):
    """Full serializer for LabelTemplate."""

    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:netbox_zpl_labels-api:labeltemplate-detail"
    )

    class Meta:
        model = LabelTemplate
        fields = [
            "id",
            "url",
            "display",
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
            "custom_fields",
            "created",
            "last_updated",
        ]
        brief_fields = ["id", "url", "display", "name", "label_size", "is_default"]


class PrintJobSerializer(NetBoxModelSerializer):
    """Full serializer for PrintJob."""

    url = serializers.HyperlinkedIdentityField(
        view_name="plugins-api:netbox_zpl_labels-api:printjob-detail"
    )
    cable = NestedCableSerializer()
    printer = NestedZPLPrinterSerializer()
    template = NestedLabelTemplateSerializer()

    class Meta:
        model = PrintJob
        fields = [
            "id",
            "url",
            "display",
            "cable",
            "printer",
            "template",
            "quantity",
            "zpl_content",
            "success",
            "error_message",
            "printed_by",
            "comments",
            "created",
            "last_updated",
        ]
        brief_fields = ["id", "url", "display", "cable", "success", "created"]


#
# Action Serializers
#


class GenerateLabelSerializer(serializers.Serializer):
    """Serializer for label generation request."""

    cable_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="List of cable IDs to generate labels for",
    )
    template_id = serializers.IntegerField(
        required=False,
        help_text="Template ID (uses default if not specified)",
    )


class GenerateLabelResponseSerializer(serializers.Serializer):
    """Serializer for label generation response."""

    cable_id = serializers.IntegerField()
    cable_label = serializers.CharField()
    zpl = serializers.CharField()


class PrintLabelSerializer(serializers.Serializer):
    """Serializer for print request."""

    cable_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="List of cable IDs to print labels for",
    )
    printer_id = serializers.IntegerField(
        help_text="Printer ID to send labels to",
    )
    template_id = serializers.IntegerField(
        required=False,
        help_text="Template ID (uses default if not specified)",
    )
    copies = serializers.IntegerField(
        default=1,
        min_value=1,
        max_value=100,
        help_text="Number of copies per label",
    )


class PrintResultSerializer(serializers.Serializer):
    """Serializer for individual print result."""

    cable_id = serializers.IntegerField()
    status = serializers.CharField()
    error = serializers.CharField(required=False, allow_null=True)
    job_id = serializers.IntegerField(required=False, allow_null=True)


class PrintLabelResponseSerializer(serializers.Serializer):
    """Serializer for print response."""

    status = serializers.CharField()
    printed = serializers.IntegerField()
    failed = serializers.IntegerField()
    jobs = PrintResultSerializer(many=True)


class PreviewLabelSerializer(serializers.Serializer):
    """Serializer for preview request."""

    cable_id = serializers.IntegerField(
        help_text="Cable ID to preview label for",
    )
    template_id = serializers.IntegerField(
        required=False,
        help_text="Template ID (uses default if not specified)",
    )


class TestConnectionSerializer(serializers.Serializer):
    """Serializer for connection test response."""

    success = serializers.BooleanField()
    message = serializers.CharField()
