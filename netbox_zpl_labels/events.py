"""Event types and handlers for NetBox ZPL Labels plugin.

Provides custom event types for print job operations that can trigger
webhooks and be logged in the event log.
"""

from __future__ import annotations

from typing import Any

# Custom event type names for webhook filtering
EVENT_PRINT_JOB_SUCCESS = "print_job_success"
EVENT_PRINT_JOB_FAILURE = "print_job_failure"

# All custom event types
CUSTOM_EVENT_TYPES = [
    (EVENT_PRINT_JOB_SUCCESS, "Print Job Success"),
    (EVENT_PRINT_JOB_FAILURE, "Print Job Failure"),
]


def get_print_job_event_type(print_job: Any) -> str:
    """Return the appropriate event type for a print job.

    Args:
        print_job: PrintJob instance (or any object with success attribute)

    Returns:
        Event type string
    """
    return EVENT_PRINT_JOB_SUCCESS if print_job.success else EVENT_PRINT_JOB_FAILURE


def create_print_job_event_data(print_job: Any) -> dict:
    """Create event data dictionary for a print job.

    Args:
        print_job: PrintJob instance (or any object with required attributes)

    Returns:
        Dictionary suitable for webhook payloads and event logging.
    """
    return {
        "print_job_id": print_job.pk,
        "cable_id": print_job.cable_id,
        "cable": str(print_job.cable) if print_job.cable else None,
        "printer_id": print_job.printer_id,
        "printer": str(print_job.printer) if print_job.printer else None,
        "template_id": print_job.template_id,
        "template": str(print_job.template) if print_job.template else None,
        "quantity": print_job.quantity,
        "success": print_job.success,
        "error_message": print_job.error_message or None,
        "printed_by": print_job.printed_by.username if print_job.printed_by else None,
        "created": print_job.created.isoformat() if print_job.created else None,
    }


def _register_signals():
    """Register signal handlers. Called from PluginConfig.ready()."""
    from django.db.models.signals import post_save
    from django.dispatch import receiver

    from .models import PrintJob

    @receiver(post_save, sender=PrintJob)
    def handle_print_job_created(sender, instance, created, **kwargs):
        """Signal handler for PrintJob creation.

        Emits custom events when a print job is created. This allows
        webhooks to be triggered based on print success or failure.

        Note: NetBox automatically handles the object create/update webhooks.
        This handler is for emitting custom event types.
        """
        if not created:
            return

        # Log the event for debugging/monitoring
        # The actual webhook triggering is handled by NetBox's webhook system
        # based on the model's ObjectChange entries
        event_type = get_print_job_event_type(instance)  # noqa: F841

        # Future enhancement: Use NetBox's event system to emit custom events
        # from extras.events import emit_event
        # emit_event(event_type, instance, create_print_job_event_data(instance))

        # For now, the signal provides a hook point for custom integrations
        pass
