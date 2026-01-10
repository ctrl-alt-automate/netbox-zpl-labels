"""Template extensions for integrating with NetBox views."""

from circuits.models import Circuit
from dcim.models import Cable, Device, Location, Module, PowerFeed, PowerPanel, Rack, Site
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


class RackPrintButton(PluginTemplateExtension):
    """Add a print label button to rack detail pages."""

    models = ["dcim.rack"]

    def buttons(self):
        """Return button HTML for the rack detail page."""
        obj = self.context.get("object")
        if not isinstance(obj, Rack):
            return ""
        return self.render(
            "netbox_zpl_labels/inc/rack_print_button.html",
            extra_context={"rack": obj},
        )

    def right_page(self):
        """Add a label panel to the right side of the rack detail page."""
        obj = self.context.get("object")
        if not isinstance(obj, Rack):
            return ""

        from .models import LabelTemplate, PrintJob

        default_template = LabelTemplate.objects.filter(is_default=True).first()
        rack_ct = ContentType.objects.get_for_model(Rack)
        recent_jobs = (
            PrintJob.objects.filter(content_type=rack_ct, object_id=obj.pk)
            .select_related("printer", "template")
            .order_by("-created")[:5]
        )

        return self.render(
            "netbox_zpl_labels/inc/rack_label_panel.html",
            extra_context={
                "rack": obj,
                "default_template": default_template,
                "recent_jobs": recent_jobs,
            },
        )


class ModulePrintButton(PluginTemplateExtension):
    """Add a print label button to module detail pages."""

    models = ["dcim.module"]

    def buttons(self):
        """Return button HTML for the module detail page."""
        obj = self.context.get("object")
        if not isinstance(obj, Module):
            return ""
        return self.render(
            "netbox_zpl_labels/inc/module_print_button.html",
            extra_context={"module": obj},
        )

    def right_page(self):
        """Add a label panel to the right side of the module detail page."""
        obj = self.context.get("object")
        if not isinstance(obj, Module):
            return ""

        from .models import LabelTemplate, PrintJob

        default_template = LabelTemplate.objects.filter(is_default=True).first()
        module_ct = ContentType.objects.get_for_model(Module)
        recent_jobs = (
            PrintJob.objects.filter(content_type=module_ct, object_id=obj.pk)
            .select_related("printer", "template")
            .order_by("-created")[:5]
        )

        return self.render(
            "netbox_zpl_labels/inc/module_label_panel.html",
            extra_context={
                "module": obj,
                "default_template": default_template,
                "recent_jobs": recent_jobs,
            },
        )


class CircuitPrintButton(PluginTemplateExtension):
    """Add a print label button to circuit detail pages."""

    models = ["circuits.circuit"]

    def buttons(self):
        """Return button HTML for the circuit detail page."""
        obj = self.context.get("object")
        if not isinstance(obj, Circuit):
            return ""
        return self.render(
            "netbox_zpl_labels/inc/circuit_print_button.html",
            extra_context={"circuit": obj},
        )

    def right_page(self):
        """Add a label panel to the right side of the circuit detail page."""
        obj = self.context.get("object")
        if not isinstance(obj, Circuit):
            return ""

        from .models import LabelTemplate, PrintJob

        default_template = LabelTemplate.objects.filter(is_default=True).first()
        circuit_ct = ContentType.objects.get_for_model(Circuit)
        recent_jobs = (
            PrintJob.objects.filter(content_type=circuit_ct, object_id=obj.pk)
            .select_related("printer", "template")
            .order_by("-created")[:5]
        )

        return self.render(
            "netbox_zpl_labels/inc/circuit_label_panel.html",
            extra_context={
                "circuit": obj,
                "default_template": default_template,
                "recent_jobs": recent_jobs,
            },
        )


class PowerFeedPrintButton(PluginTemplateExtension):
    """Add a print label button to power feed detail pages."""

    models = ["dcim.powerfeed"]

    def buttons(self):
        """Return button HTML for the power feed detail page."""
        obj = self.context.get("object")
        if not isinstance(obj, PowerFeed):
            return ""
        return self.render(
            "netbox_zpl_labels/inc/powerfeed_print_button.html",
            extra_context={"powerfeed": obj},
        )

    def right_page(self):
        """Add a label panel to the right side of the power feed detail page."""
        obj = self.context.get("object")
        if not isinstance(obj, PowerFeed):
            return ""

        from .models import LabelTemplate, PrintJob

        default_template = LabelTemplate.objects.filter(is_default=True).first()
        powerfeed_ct = ContentType.objects.get_for_model(PowerFeed)
        recent_jobs = (
            PrintJob.objects.filter(content_type=powerfeed_ct, object_id=obj.pk)
            .select_related("printer", "template")
            .order_by("-created")[:5]
        )

        return self.render(
            "netbox_zpl_labels/inc/powerfeed_label_panel.html",
            extra_context={
                "powerfeed": obj,
                "default_template": default_template,
                "recent_jobs": recent_jobs,
            },
        )


class PowerPanelPrintButton(PluginTemplateExtension):
    """Add a print label button to power panel detail pages."""

    models = ["dcim.powerpanel"]

    def buttons(self):
        """Return button HTML for the power panel detail page."""
        obj = self.context.get("object")
        if not isinstance(obj, PowerPanel):
            return ""
        return self.render(
            "netbox_zpl_labels/inc/powerpanel_print_button.html",
            extra_context={"powerpanel": obj},
        )

    def right_page(self):
        """Add a label panel to the right side of the power panel detail page."""
        obj = self.context.get("object")
        if not isinstance(obj, PowerPanel):
            return ""

        from .models import LabelTemplate, PrintJob

        default_template = LabelTemplate.objects.filter(is_default=True).first()
        powerpanel_ct = ContentType.objects.get_for_model(PowerPanel)
        recent_jobs = (
            PrintJob.objects.filter(content_type=powerpanel_ct, object_id=obj.pk)
            .select_related("printer", "template")
            .order_by("-created")[:5]
        )

        return self.render(
            "netbox_zpl_labels/inc/powerpanel_label_panel.html",
            extra_context={
                "powerpanel": obj,
                "default_template": default_template,
                "recent_jobs": recent_jobs,
            },
        )


class LocationPrintButton(PluginTemplateExtension):
    """Add a print label button to location detail pages."""

    models = ["dcim.location"]

    def buttons(self):
        """Return button HTML for the location detail page."""
        obj = self.context.get("object")
        if not isinstance(obj, Location):
            return ""
        return self.render(
            "netbox_zpl_labels/inc/location_print_button.html",
            extra_context={"location": obj},
        )

    def right_page(self):
        """Add a label panel to the right side of the location detail page."""
        obj = self.context.get("object")
        if not isinstance(obj, Location):
            return ""

        from .models import LabelTemplate, PrintJob

        default_template = LabelTemplate.objects.filter(is_default=True).first()
        location_ct = ContentType.objects.get_for_model(Location)
        recent_jobs = (
            PrintJob.objects.filter(content_type=location_ct, object_id=obj.pk)
            .select_related("printer", "template")
            .order_by("-created")[:5]
        )

        return self.render(
            "netbox_zpl_labels/inc/location_label_panel.html",
            extra_context={
                "location": obj,
                "default_template": default_template,
                "recent_jobs": recent_jobs,
            },
        )


class SitePrintButton(PluginTemplateExtension):
    """Add a print label button to site detail pages."""

    models = ["dcim.site"]

    def buttons(self):
        """Return button HTML for the site detail page."""
        obj = self.context.get("object")
        if not isinstance(obj, Site):
            return ""
        return self.render(
            "netbox_zpl_labels/inc/site_print_button.html",
            extra_context={"site": obj},
        )

    def right_page(self):
        """Add a label panel to the right side of the site detail page."""
        obj = self.context.get("object")
        if not isinstance(obj, Site):
            return ""

        from .models import LabelTemplate, PrintJob

        default_template = LabelTemplate.objects.filter(is_default=True).first()
        site_ct = ContentType.objects.get_for_model(Site)
        recent_jobs = (
            PrintJob.objects.filter(content_type=site_ct, object_id=obj.pk)
            .select_related("printer", "template")
            .order_by("-created")[:5]
        )

        return self.render(
            "netbox_zpl_labels/inc/site_label_panel.html",
            extra_context={
                "site": obj,
                "default_template": default_template,
                "recent_jobs": recent_jobs,
            },
        )


# Register all template extensions
template_extensions = [
    CablePrintButton,
    CableListPrintButton,
    DevicePrintButton,
    DeviceListPrintButton,
    RackPrintButton,
    ModulePrintButton,
    CircuitPrintButton,
    PowerFeedPrintButton,
    PowerPanelPrintButton,
    LocationPrintButton,
    SitePrintButton,
]
