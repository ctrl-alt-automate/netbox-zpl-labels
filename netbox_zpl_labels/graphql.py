"""GraphQL types for NetBox ZPL Labels plugin.

Provides GraphQL queries for ZPL printers, label templates, and print jobs.
"""

from __future__ import annotations

try:
    import strawberry

    STRAWBERRY_AVAILABLE = True
except ImportError:
    STRAWBERRY_AVAILABLE = False
    strawberry = None  # type: ignore[assignment]

# Default pagination limits
DEFAULT_LIMIT = 100
MAX_LIMIT = 1000

# Only define GraphQL types if strawberry is available
if STRAWBERRY_AVAILABLE:
    from .models import LabelTemplate, PrintJob, ZPLPrinter

    @strawberry.type
    class ZPLPrinterType:
        """GraphQL type for ZPLPrinter."""

        id: int
        name: str
        host: str
        port: int
        status: str
        description: str

    @strawberry.type
    class LabelTemplateType:
        """GraphQL type for LabelTemplate."""

        id: int
        name: str
        description: str
        width_mm: float
        height_mm: float
        dpi: int
        is_default: bool

    @strawberry.type
    class PrintJobType:
        """GraphQL type for PrintJob."""

        id: int
        quantity: int
        success: bool
        error_message: str

    @strawberry.type
    class Query:
        """GraphQL queries for ZPL Labels plugin."""

        @strawberry.field
        def zpl_printer(self, id: int) -> ZPLPrinterType | None:
            """Get a single ZPL printer by ID."""
            printer = ZPLPrinter.objects.filter(pk=id).first()
            if printer:
                return ZPLPrinterType(
                    id=printer.pk,
                    name=printer.name,
                    host=printer.host,
                    port=printer.port,
                    status=printer.status,
                    description=printer.description or "",
                )
            return None

        @strawberry.field
        def zpl_printer_list(
            self,
            limit: int = DEFAULT_LIMIT,
            offset: int = 0,
        ) -> list[ZPLPrinterType]:
            """List ZPL printers with pagination."""
            limit = min(limit, MAX_LIMIT)
            qs = ZPLPrinter.objects.all()[offset : offset + limit]
            return [
                ZPLPrinterType(
                    id=p.pk,
                    name=p.name,
                    host=p.host,
                    port=p.port,
                    status=p.status,
                    description=p.description or "",
                )
                for p in qs
            ]

        @strawberry.field
        def label_template(self, id: int) -> LabelTemplateType | None:
            """Get a single label template by ID."""
            template = LabelTemplate.objects.filter(pk=id).first()
            if template:
                return LabelTemplateType(
                    id=template.pk,
                    name=template.name,
                    description=template.description or "",
                    width_mm=float(template.width_mm),
                    height_mm=float(template.height_mm),
                    dpi=template.dpi,
                    is_default=template.is_default,
                )
            return None

        @strawberry.field
        def label_template_list(
            self,
            limit: int = DEFAULT_LIMIT,
            offset: int = 0,
        ) -> list[LabelTemplateType]:
            """List label templates with pagination."""
            limit = min(limit, MAX_LIMIT)
            qs = LabelTemplate.objects.all()[offset : offset + limit]
            return [
                LabelTemplateType(
                    id=t.pk,
                    name=t.name,
                    description=t.description or "",
                    width_mm=float(t.width_mm),
                    height_mm=float(t.height_mm),
                    dpi=t.dpi,
                    is_default=t.is_default,
                )
                for t in qs
            ]

        @strawberry.field
        def print_job(self, id: int) -> PrintJobType | None:
            """Get a single print job by ID."""
            job = PrintJob.objects.filter(pk=id).first()
            if job:
                return PrintJobType(
                    id=job.pk,
                    quantity=job.quantity,
                    success=job.success,
                    error_message=job.error_message or "",
                )
            return None

        @strawberry.field
        def print_job_list(
            self,
            limit: int = DEFAULT_LIMIT,
            offset: int = 0,
        ) -> list[PrintJobType]:
            """List print jobs with pagination."""
            limit = min(limit, MAX_LIMIT)
            qs = PrintJob.objects.all()[offset : offset + limit]
            return [
                PrintJobType(
                    id=j.pk,
                    quantity=j.quantity,
                    success=j.success,
                    error_message=j.error_message or "",
                )
                for j in qs
            ]

    # Export schema for NetBox plugin system
    schema = [Query]
else:
    # Strawberry not available - no GraphQL support
    schema = []
