"""Navigation menu configuration for NetBox ZPL Labels plugin."""
from django.utils.translation import gettext_lazy as _
from netbox.plugins import PluginMenu, PluginMenuButton, PluginMenuItem

# Printer menu item with add button
printer_item = PluginMenuItem(
    link="plugins:netbox_zpl_labels:zplprinter_list",
    link_text=_("Printers"),
    permissions=["netbox_zpl_labels.view_zplprinter"],
    buttons=[
        PluginMenuButton(
            link="plugins:netbox_zpl_labels:zplprinter_add",
            title=_("Add"),
            icon_class="mdi mdi-plus-thick",
            permissions=["netbox_zpl_labels.add_zplprinter"],
        ),
        PluginMenuButton(
            link="plugins:netbox_zpl_labels:zplprinter_import",
            title=_("Import"),
            icon_class="mdi mdi-upload",
            permissions=["netbox_zpl_labels.add_zplprinter"],
        ),
    ],
)

# Template menu item with add button
template_item = PluginMenuItem(
    link="plugins:netbox_zpl_labels:labeltemplate_list",
    link_text=_("Label Templates"),
    permissions=["netbox_zpl_labels.view_labeltemplate"],
    buttons=[
        PluginMenuButton(
            link="plugins:netbox_zpl_labels:labeltemplate_add",
            title=_("Add"),
            icon_class="mdi mdi-plus-thick",
            permissions=["netbox_zpl_labels.add_labeltemplate"],
        ),
    ],
)

# Print history menu item
printjob_item = PluginMenuItem(
    link="plugins:netbox_zpl_labels:printjob_list",
    link_text=_("Print History"),
    permissions=["netbox_zpl_labels.view_printjob"],
)

# Grouped menu for the plugin
menu = PluginMenu(
    label=_("ZPL Labels"),
    groups=(
        (
            _("Configuration"),
            (printer_item, template_item),
        ),
        (
            _("Operations"),
            (printjob_item,),
        ),
    ),
    icon_class="mdi mdi-label-multiple-outline",
)
