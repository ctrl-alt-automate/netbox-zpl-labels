"""Search indexes for NetBox ZPL Labels plugin."""

from netbox.search import SearchIndex, register_search

from .models import LabelTemplate, ZPLPrinter


@register_search
class ZPLPrinterIndex(SearchIndex):
    """Search index for ZPL printers."""

    model = ZPLPrinter
    fields = (
        ("name", 100),
        ("host", 60),
        ("description", 500),
        ("comments", 1000),
    )


@register_search
class LabelTemplateIndex(SearchIndex):
    """Search index for label templates."""

    model = LabelTemplate
    fields = (
        ("name", 100),
        ("description", 500),
        ("comments", 1000),
    )
