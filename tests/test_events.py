"""Tests for events module (without Django model dependencies).

These tests verify the event helper functions work correctly
using mock objects instead of actual Django models.
"""

from unittest.mock import MagicMock


class TestEventTypeConstants:
    """Tests for event type constants."""

    def test_event_type_values(self):
        """Test that event type constants have expected values."""
        from netbox_zpl_labels.events import (
            EVENT_PRINT_JOB_FAILURE,
            EVENT_PRINT_JOB_SUCCESS,
        )

        assert EVENT_PRINT_JOB_SUCCESS == "print_job_success"
        assert EVENT_PRINT_JOB_FAILURE == "print_job_failure"

    def test_custom_event_types_list(self):
        """Test that custom event types list is properly formatted."""
        from netbox_zpl_labels.events import CUSTOM_EVENT_TYPES

        assert len(CUSTOM_EVENT_TYPES) == 2

        # Each entry should be (type_name, label)
        for event_type, label in CUSTOM_EVENT_TYPES:
            assert isinstance(event_type, str)
            assert isinstance(label, str)
            assert len(event_type) > 0
            assert len(label) > 0


class TestGetPrintJobEventType:
    """Tests for get_print_job_event_type function."""

    def test_success_returns_success_event(self):
        """Test successful job returns success event type."""
        from netbox_zpl_labels.events import (
            EVENT_PRINT_JOB_SUCCESS,
            get_print_job_event_type,
        )

        job = MagicMock()
        job.success = True

        assert get_print_job_event_type(job) == EVENT_PRINT_JOB_SUCCESS

    def test_failure_returns_failure_event(self):
        """Test failed job returns failure event type."""
        from netbox_zpl_labels.events import (
            EVENT_PRINT_JOB_FAILURE,
            get_print_job_event_type,
        )

        job = MagicMock()
        job.success = False

        assert get_print_job_event_type(job) == EVENT_PRINT_JOB_FAILURE


class TestCreatePrintJobEventData:
    """Tests for create_print_job_event_data function."""

    def test_returns_dict_with_all_fields(self):
        """Test that event data contains all required fields."""
        from datetime import datetime

        from netbox_zpl_labels.events import create_print_job_event_data

        # Create mock objects
        cable = MagicMock()
        cable.__str__ = MagicMock(return_value="CBL-001")

        printer = MagicMock()
        printer.__str__ = MagicMock(return_value="Printer-01")

        template = MagicMock()
        template.__str__ = MagicMock(return_value="Standard Label")

        user = MagicMock()
        user.username = "testuser"

        job = MagicMock()
        job.pk = 42
        job.cable_id = 1
        job.cable = cable
        job.printer_id = 2
        job.printer = printer
        job.template_id = 3
        job.template = template
        job.quantity = 5
        job.success = True
        job.error_message = ""
        job.printed_by = user
        job.created = datetime(2024, 1, 15, 10, 30)

        data = create_print_job_event_data(job)

        # Check all required fields are present
        assert "print_job_id" in data
        assert "cable_id" in data
        assert "cable" in data
        assert "printer_id" in data
        assert "printer" in data
        assert "template_id" in data
        assert "template" in data
        assert "quantity" in data
        assert "success" in data
        assert "error_message" in data
        assert "printed_by" in data
        assert "created" in data

        # Check values
        assert data["print_job_id"] == 42
        assert data["cable"] == "CBL-001"
        assert data["printer"] == "Printer-01"
        assert data["template"] == "Standard Label"
        assert data["quantity"] == 5
        assert data["success"] is True
        assert data["printed_by"] == "testuser"

    def test_handles_null_relations(self):
        """Test that null relations are handled gracefully."""
        from netbox_zpl_labels.events import create_print_job_event_data

        job = MagicMock()
        job.pk = 1
        job.cable_id = None
        job.cable = None
        job.printer_id = None
        job.printer = None
        job.template_id = None
        job.template = None
        job.quantity = 1
        job.success = False
        job.error_message = "Connection failed"
        job.printed_by = None
        job.created = None

        data = create_print_job_event_data(job)

        assert data["cable"] is None
        assert data["printer"] is None
        assert data["template"] is None
        assert data["printed_by"] is None
        assert data["created"] is None
        assert data["error_message"] == "Connection failed"

    def test_empty_error_message_becomes_none(self):
        """Test that empty error_message becomes None."""
        from netbox_zpl_labels.events import create_print_job_event_data

        job = MagicMock()
        job.pk = 1
        job.cable_id = 1
        job.cable = MagicMock(__str__=MagicMock(return_value="CBL"))
        job.printer_id = 1
        job.printer = MagicMock(__str__=MagicMock(return_value="P"))
        job.template_id = 1
        job.template = MagicMock(__str__=MagicMock(return_value="T"))
        job.quantity = 1
        job.success = True
        job.error_message = ""  # Empty string
        job.printed_by = None
        job.created = None

        data = create_print_job_event_data(job)

        # Empty error_message should become None for cleaner JSON
        assert data["error_message"] is None

    def test_created_is_iso_formatted(self):
        """Test that created datetime is ISO formatted."""
        from datetime import datetime

        from netbox_zpl_labels.events import create_print_job_event_data

        job = MagicMock()
        job.pk = 1
        job.cable_id = 1
        job.cable = MagicMock(__str__=MagicMock(return_value="CBL"))
        job.printer_id = 1
        job.printer = MagicMock(__str__=MagicMock(return_value="P"))
        job.template_id = 1
        job.template = MagicMock(__str__=MagicMock(return_value="T"))
        job.quantity = 1
        job.success = True
        job.error_message = ""
        job.printed_by = None
        job.created = datetime(2024, 6, 15, 14, 30, 45)

        data = create_print_job_event_data(job)

        # Should be ISO format
        assert "2024-06-15" in data["created"]
        assert "14:30:45" in data["created"]
