"""NetBox ZPL Labels Plugin.

A NetBox plugin for generating and printing ZPL labels for cables
documented in NetBox. Targets Zebra thermal transfer printers
(ZD421/ZD621 series) with self-laminating cable labels.
"""

from django.utils.translation import gettext_lazy as _
from netbox.plugins import PluginConfig


class NetBoxZPLLabelsConfig(PluginConfig):
    """Plugin configuration for NetBox ZPL Labels."""

    name = "netbox_zpl_labels"
    verbose_name = _("ZPL Cable Labels")
    description = _("Generate and print ZPL labels for cables")
    version = "0.1.0"
    author = "Elvis Smeers"
    author_email = "elvis@smeers.nl"
    base_url = "zpl-labels"

    # NetBox version compatibility (NetBox 4.5+ only)
    min_version = "4.5.0"

    # Default plugin settings
    default_settings = {
        "default_dpi": 300,
        "labelary_enabled": True,
        "labelary_dpmm": "12dpmm",
        "default_print_speed": 4,
        "socket_timeout": 5,
    }

    # Required settings (none required)
    required_settings: list[str] = []

    # GraphQL schema
    graphql_schema = "netbox_zpl_labels.graphql.schema"

    def ready(self):
        """Called when the plugin is loaded.

        Registers signal handlers with Django.
        """
        super().ready()
        # Register signal handlers for events
        from .events import _register_signals

        _register_signals()


config = NetBoxZPLLabelsConfig
