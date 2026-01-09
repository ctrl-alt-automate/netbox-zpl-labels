"""Template extensions for integrating with NetBox views."""

from dcim.models import Cable
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

        # Get recent print jobs for this cable
        recent_jobs = (
            PrintJob.objects.filter(cable=obj)
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


# Register all template extensions
template_extensions = [CablePrintButton, CableListPrintButton]
