"""Template extensions for integrating with NetBox views."""

from dcim.models import Cable, Device
from django.contrib.contenttypes.models import ContentType
from netbox.plugins import PluginTemplateExtension


class CablePrintButton(PluginTemplateExtension):
    """Add a print label button to cable detail pages."""

    models = ["dcim.cable"]

    def buttons(self):
        """Return button HTML for the cable detail page."""
        obj = self.context.get("object")
        if not isinstance(obj, Cable):
            return ""
        return self.render(
            "netbox_zpl_labels/inc/cable_print_button.html",
            extra_context={
                "cable": obj,
            },
        )

    def right_page(self):
        """Add a label panel to the right side of the cable detail page."""
        obj = self.context.get("object")
        if not isinstance(obj, Cable):
            return ""

        # Import here to avoid circular imports
        from .models import LabelTemplate, PrintJob

        # Get default template
        default_template = LabelTemplate.objects.filter(is_default=True).first()

        # Get recent print jobs for this cable using generic relation
        cable_ct = ContentType.objects.get_for_model(Cable)
        recent_jobs = (
            PrintJob.objects.filter(content_type=cable_ct, object_id=obj.pk)
            .select_related("printer", "template")
            .order_by("-created")[:5]
        )

        return self.render(
            "netbox_zpl_labels/inc/cable_label_panel.html",
            extra_context={
                "cable": obj,
                "default_template": default_template,
                "recent_jobs": recent_jobs,
            },
        )


class CableListPrintButton(PluginTemplateExtension):
    """Add bulk print button to cable list page."""

    models = ["dcim.cable"]

    def list_buttons(self):
        """Add button to cable list page actions."""
        return self.render("netbox_zpl_labels/inc/cable_list_button.html")


class DevicePrintButton(PluginTemplateExtension):
    """Add a print label button to device detail pages."""

    models = ["dcim.device"]

    def buttons(self):
        """Return button HTML for the device detail page."""
        obj = self.context.get("object")
        if not isinstance(obj, Device):
            return ""
        return self.render(
            "netbox_zpl_labels/inc/device_print_button.html",
            extra_context={
                "device": obj,
            },
        )

    def right_page(self):
        """Add a label panel to the right side of the device detail page."""
        obj = self.context.get("object")
        if not isinstance(obj, Device):
            return ""

        # Import here to avoid circular imports
        from .models import LabelTemplate, PrintJob

        # Get default template
        default_template = LabelTemplate.objects.filter(is_default=True).first()

        # Get recent print jobs for this device using generic relation
        device_ct = ContentType.objects.get_for_model(Device)
        recent_jobs = (
            PrintJob.objects.filter(content_type=device_ct, object_id=obj.pk)
            .select_related("printer", "template")
            .order_by("-created")[:5]
        )

        return self.render(
            "netbox_zpl_labels/inc/device_label_panel.html",
            extra_context={
                "device": obj,
                "default_template": default_template,
                "recent_jobs": recent_jobs,
            },
        )


class DeviceListPrintButton(PluginTemplateExtension):
    """Add bulk print button to device list page."""

    models = ["dcim.device"]

    def list_buttons(self):
        """Add button to device list page actions."""
        return self.render("netbox_zpl_labels/inc/device_list_button.html")


# Register all template extensions
template_extensions = [
    CablePrintButton,
    CableListPrintButton,
    DevicePrintButton,
    DeviceListPrintButton,
]
