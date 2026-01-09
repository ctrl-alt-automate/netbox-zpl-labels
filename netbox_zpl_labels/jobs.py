"""Background jobs for NetBox ZPL Labels plugin.

Provides async job support for large batch printing operations
using NetBox's built-in job scheduling system.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Threshold for triggering background job instead of synchronous processing
BATCH_THRESHOLD = 10


def print_labels_batch(
    cable_ids: list[int],
    printer_id: int,
    template_id: int,
    copies: int = 1,
    user_id: int | None = None,
    base_url: str = "",
) -> dict:
    """Background job for batch printing labels.

    This function is designed to be run as a background job for large
    batch printing operations. It processes labels sequentially and
    creates PrintJob records for each.

    Args:
        cable_ids: List of cable PKs to print labels for
        printer_id: PK of the printer to use
        template_id: PK of the template to use
        copies: Number of copies per cable
        user_id: PK of the user initiating the job (optional)
        base_url: Base URL for generating cable URLs

    Returns:
        Dictionary with results summary
    """
    # Import here to avoid circular imports and to work in job context
    from dcim.models import Cable
    from django.contrib.auth import get_user_model

    from .models import LabelTemplate, PrintJob, ZPLPrinter
    from .zpl import generate_cable_label
    from .zpl.printer import ZPLPrinterClient

    User = get_user_model()

    # Load related objects
    printer = ZPLPrinter.objects.filter(pk=printer_id).first()
    template = LabelTemplate.objects.filter(pk=template_id).first()
    user = User.objects.filter(pk=user_id).first() if user_id else None

    if not printer:
        return {"status": "error", "error": "Printer not found", "printed": 0, "failed": 0}

    if not template:
        return {"status": "error", "error": "Template not found", "printed": 0, "failed": 0}

    if printer.status != "active":
        return {
            "status": "error",
            "error": f"Printer '{printer.name}' is not active",
            "printed": 0,
            "failed": 0,
        }

    # Process cables
    cables = Cable.objects.filter(pk__in=cable_ids)
    printed = 0
    failed = 0
    job_ids = []

    # Generate all ZPL first
    cables_data = []
    for cable in cables:
        zpl = generate_cable_label(
            cable=cable,
            template=template,
            quantity=copies,
            base_url=base_url,
        )
        cables_data.append((cable, zpl))

    # Send all in batch
    if cables_data:
        zpl_contents = [zpl for _, zpl in cables_data]
        client = ZPLPrinterClient(host=printer.host, port=printer.port)

        try:
            results = client.send_zpl_batch(zpl_contents)
        except Exception as e:
            # Connection failed - mark all as failed
            for cable, zpl in cables_data:
                job = PrintJob.objects.create(
                    cable=cable,
                    printer=printer,
                    template=template,
                    quantity=copies,
                    zpl_content=zpl,
                    success=False,
                    error_message=str(e),
                    printed_by=user,
                )
                failed += 1
                job_ids.append(job.pk)

            logger.error("Batch print connection failed: %s", e)
        else:
            # Process results
            for (cable, zpl), result in zip(cables_data, results, strict=True):
                job = PrintJob.objects.create(
                    cable=cable,
                    printer=printer,
                    template=template,
                    quantity=copies,
                    zpl_content=zpl,
                    success=result.success,
                    error_message=result.error or "",
                    printed_by=user,
                )
                job_ids.append(job.pk)

                if result.success:
                    printed += 1
                else:
                    failed += 1

    # Add missing cables as failures
    missing = len(cable_ids) - len(cables)
    failed += missing

    logger.info(
        "Batch print job completed: printed=%d, failed=%d, printer=%s",
        printed,
        failed,
        printer.name,
    )

    return {
        "status": "success" if failed == 0 else "partial" if printed > 0 else "failed",
        "printed": printed,
        "failed": failed,
        "job_ids": job_ids,
    }


def should_use_background_job(count: int) -> bool:
    """Determine if a batch should be processed as a background job.

    Args:
        count: Number of items in the batch

    Returns:
        True if background job should be used
    """
    return count >= BATCH_THRESHOLD
