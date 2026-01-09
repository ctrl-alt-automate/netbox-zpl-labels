"""Template extensions for integrating with NetBox views."""

import logging

from dcim.models import Cable
from netbox.plugins import PluginTemplateExtension

logger = logging.getLogger("netbox.plugins.netbox_zpl_labels")


class CablePrintButton(PluginTemplateExtension):
    """Add a print label button to cable detail pages."""

    models = ["dcim.cable"]

    def buttons(self):
        """Return button HTML for the cable detail page."""
        obj = self.context.get("object")
        obj_type = type(obj).__name__ if obj else "None"
        logger.warning(
            f"[ZPL DEBUG] CablePrintButton.buttons() called - "
            f"object type: {obj_type}, "
            f"is Cable: {isinstance(obj, Cable)}, "
            f"context keys: {list(self.context.keys())}"
        )
        # Only show button for Cable objects
        if not isinstance(obj, Cable):
            logger.warning(f"[ZPL DEBUG] buttons() returning empty - not a Cable")
            return ""
        logger.warning(f"[ZPL DEBUG] buttons() returning button HTML for Cable")
        return self.render(
            "netbox_zpl_labels/inc/cable_print_button.html",
            extra_context={
                "cable": obj,
            },
        )

    def right_page(self):
        """Add a label panel to the right side of the cable detail page."""
        obj = self.context.get("object")
        obj_type = type(obj).__name__ if obj else "None"
        logger.warning(
            f"[ZPL DEBUG] CablePrintButton.right_page() called - "
            f"object type: {obj_type}, "
            f"is Cable: {isinstance(obj, Cable)}"
        )
        # Only show panel for Cable objects
        if not isinstance(obj, Cable):
            logger.warning(f"[ZPL DEBUG] right_page() returning empty - not a Cable")
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

        logger.warning(f"[ZPL DEBUG] right_page() returning panel HTML for Cable")
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
        view = self.context.get("view")
        view_name = type(view).__name__ if view else "None"
        model_from_qs = None
        model_from_view = None

        if view and hasattr(view, "queryset"):
            model_from_qs = getattr(view.queryset, "model", None)
        if view and hasattr(view, "model"):
            model_from_view = view.model

        logger.warning(
            f"[ZPL DEBUG] CableListPrintButton.list_buttons() called - "
            f"view: {view_name}, "
            f"model from queryset: {model_from_qs}, "
            f"model from view: {model_from_view}, "
            f"context keys: {list(self.context.keys())}"
        )

        # Check if we're on a Cable list view
        if view and hasattr(view, "queryset"):
            model = getattr(view.queryset, "model", None)
            if model is not Cable:
                logger.warning(f"[ZPL DEBUG] list_buttons() returning empty - queryset model is not Cable")
                return ""
        elif view and hasattr(view, "model"):
            if view.model is not Cable:
                logger.warning(f"[ZPL DEBUG] list_buttons() returning empty - view model is not Cable")
                return ""
        else:
            logger.warning(f"[ZPL DEBUG] list_buttons() returning empty - can't determine model")
            return ""

        logger.warning(f"[ZPL DEBUG] list_buttons() returning button HTML for Cable list")
        return self.render("netbox_zpl_labels/inc/cable_list_button.html")


# Register all template extensions
template_extensions = [CablePrintButton, CableListPrintButton]
