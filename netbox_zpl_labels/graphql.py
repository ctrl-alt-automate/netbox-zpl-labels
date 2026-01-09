"""GraphQL types for NetBox ZPL Labels plugin."""

import strawberry
import strawberry_django

from .models import LabelTemplate, PrintJob, ZPLPrinter

# Default pagination limits
DEFAULT_LIMIT = 100
MAX_LIMIT = 1000


@strawberry_django.type(ZPLPrinter, fields="__all__")
class ZPLPrinterType:
    """GraphQL type for ZPLPrinter."""

    pass


@strawberry_django.type(LabelTemplate, fields="__all__")
class LabelTemplateType:
    """GraphQL type for LabelTemplate."""

    pass


@strawberry_django.type(PrintJob, fields="__all__")
class PrintJobType:
    """GraphQL type for PrintJob."""

    pass


@strawberry.type
class Query:
    """GraphQL queries for ZPL Labels plugin."""

    @strawberry.field
    def zpl_printer(self, id: int) -> ZPLPrinterType | None:
        """Get a single ZPL printer by ID."""
        return ZPLPrinter.objects.filter(pk=id).first()

    @strawberry.field
    def zpl_printer_list(
        self,
        limit: int = DEFAULT_LIMIT,
        offset: int = 0,
    ) -> list[ZPLPrinterType]:
        """List ZPL printers with pagination."""
        limit = min(limit, MAX_LIMIT)
        qs = ZPLPrinter.objects.all()[offset : offset + limit]
        return list(qs)

    @strawberry.field
    def label_template(self, id: int) -> LabelTemplateType | None:
        """Get a single label template by ID."""
        return LabelTemplate.objects.filter(pk=id).first()

    @strawberry.field
    def label_template_list(
        self,
        limit: int = DEFAULT_LIMIT,
        offset: int = 0,
    ) -> list[LabelTemplateType]:
        """List label templates with pagination."""
        limit = min(limit, MAX_LIMIT)
        qs = LabelTemplate.objects.all()[offset : offset + limit]
        return list(qs)

    @strawberry.field
    def print_job(self, id: int) -> PrintJobType | None:
        """Get a single print job by ID."""
        return PrintJob.objects.filter(pk=id).first()

    @strawberry.field
    def print_job_list(
        self,
        limit: int = DEFAULT_LIMIT,
        offset: int = 0,
    ) -> list[PrintJobType]:
        """List print jobs with pagination."""
        limit = min(limit, MAX_LIMIT)
        qs = PrintJob.objects.select_related("cable", "printer", "template", "printed_by")[
            offset : offset + limit
        ]
        return list(qs)


schema = [Query]
