"""Views for NetBox ZPL Labels plugin."""

from dcim.models import Cable
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.generic import View
from netbox.views import generic
from utilities.views import GetReturnURLMixin, ViewTab, register_model_view

from .filtersets import LabelTemplateFilterSet, PrintJobFilterSet, ZPLPrinterFilterSet
from .forms import (
    BulkPrintLabelForm,
    LabelTemplateBulkEditForm,
    LabelTemplateFilterForm,
    LabelTemplateForm,
    LabelTemplateImportForm,
    PreviewLabelForm,
    PrintJobFilterForm,
    PrintLabelForm,
    ZPLPrinterBulkEditForm,
    ZPLPrinterFilterForm,
    ZPLPrinterForm,
    ZPLPrinterImportForm,
)
from .models import LabelTemplate, PrintJob, ZPLPrinter
from .tables import LabelTemplateTable, PrintJobTable, ZPLPrinterTable
from .zpl import generate_cable_label, get_label_preview, send_to_printer

#
# ZPLPrinter Views
#


class ZPLPrinterListView(generic.ObjectListView):
    """List view for ZPL printers."""

    queryset = ZPLPrinter.objects.all()
    table = ZPLPrinterTable
    filterset = ZPLPrinterFilterSet
    filterset_form = ZPLPrinterFilterForm


class ZPLPrinterView(generic.ObjectView):
    """Detail view for a single ZPL printer."""

    queryset = ZPLPrinter.objects.all()

    def get_extra_context(self, request, instance):
        """Add recent print jobs to context."""
        recent_jobs = (
            PrintJob.objects.filter(printer=instance)
            .select_related("cable", "template", "printed_by")
            .order_by("-created")[:10]
        )

        return {
            "recent_jobs": recent_jobs,
        }


class ZPLPrinterEditView(generic.ObjectEditView):
    """Create/edit view for ZPL printers."""

    queryset = ZPLPrinter.objects.all()
    form = ZPLPrinterForm


class ZPLPrinterDeleteView(generic.ObjectDeleteView):
    """Delete view for ZPL printers."""

    queryset = ZPLPrinter.objects.all()


class ZPLPrinterBulkImportView(generic.BulkImportView):
    """Bulk import view for ZPL printers."""

    queryset = ZPLPrinter.objects.all()
    model_form = ZPLPrinterImportForm


class ZPLPrinterBulkEditView(generic.BulkEditView):
    """Bulk edit view for ZPL printers."""

    queryset = ZPLPrinter.objects.all()
    filterset = ZPLPrinterFilterSet
    table = ZPLPrinterTable
    form = ZPLPrinterBulkEditForm


class ZPLPrinterBulkDeleteView(generic.BulkDeleteView):
    """Bulk delete view for ZPL printers."""

    queryset = ZPLPrinter.objects.all()
    filterset = ZPLPrinterFilterSet
    table = ZPLPrinterTable


class ZPLPrinterTestConnectionView(View):
    """Test connection to a printer."""

    def get(self, request, pk):
        printer = get_object_or_404(ZPLPrinter, pk=pk)

        from .zpl.printer import check_printer_connection

        success, error = check_printer_connection(
            host=printer.host,
            port=printer.port,
        )

        if success:
            messages.success(
                request,
                _("Successfully connected to {printer}").format(printer=printer.name),
            )
        else:
            messages.error(
                request,
                _("Connection to {printer} failed: {error}").format(
                    printer=printer.name, error=error
                ),
            )

        return redirect(printer.get_absolute_url())


class ZPLPrinterStatusHTMXView(View):
    """HTMX partial view for real-time printer status."""

    def get(self, request, pk):
        from .zpl.printer import ZPLPrinterClient

        printer = get_object_or_404(ZPLPrinter, pk=pk)
        client = ZPLPrinterClient(host=printer.host, port=printer.port)

        # Test connection
        connection_result = client.test_connection()
        online = connection_result.success

        # Update printer status tracking
        printer.update_status(online=online)

        context = {
            "online": online,
            "error": connection_result.error if not online else None,
            "paper": None,
            "ribbon": None,
            "last_checked": (
                printer.last_checked.strftime("%H:%M:%S") if printer.last_checked else None
            ),
        }

        # Get detailed status if online
        if online:
            status = client.get_printer_status()
            if status:
                context["paper"] = status.get("paper")
                context["ribbon"] = status.get("ribbon")

        return render(request, "netbox_zpl_labels/htmx/printer_status.html", context)


#
# LabelTemplate Views
#


class LabelTemplateListView(generic.ObjectListView):
    """List view for label templates."""

    queryset = LabelTemplate.objects.all()
    table = LabelTemplateTable
    filterset = LabelTemplateFilterSet
    filterset_form = LabelTemplateFilterForm


class LabelTemplateView(generic.ObjectView):
    """Detail view for a label template."""

    queryset = LabelTemplate.objects.all()

    def get_extra_context(self, request, instance):
        """Add template preview and ZPL code to context."""
        return {
            "zpl_code": instance.zpl_template,
        }


class LabelTemplateEditView(generic.ObjectEditView):
    """Create/edit view for label templates."""

    queryset = LabelTemplate.objects.all()
    form = LabelTemplateForm


class LabelTemplateDeleteView(generic.ObjectDeleteView):
    """Delete view for label templates."""

    queryset = LabelTemplate.objects.all()


class LabelTemplateBulkImportView(generic.BulkImportView):
    """Bulk import view for label templates (CSV/JSON)."""

    queryset = LabelTemplate.objects.all()
    model_form = LabelTemplateImportForm


class LabelTemplateBulkEditView(generic.BulkEditView):
    """Bulk edit view for label templates."""

    queryset = LabelTemplate.objects.all()
    filterset = LabelTemplateFilterSet
    table = LabelTemplateTable
    form = LabelTemplateBulkEditForm


class LabelTemplateBulkDeleteView(generic.BulkDeleteView):
    """Bulk delete view for label templates."""

    queryset = LabelTemplate.objects.all()
    filterset = LabelTemplateFilterSet
    table = LabelTemplateTable


class LabelTemplatePreviewView(View):
    """Generate preview image for a template."""

    def get(self, request, pk):
        template = get_object_or_404(LabelTemplate, pk=pk)

        # Create sample data for preview
        sample_data = {
            "cable_id": "CBL-001",
            "cable_url": "https://netbox.local/dcim/cables/1/",
            "term_a_device": "switch-01",
            "term_a_interface": "Gi1/0/1",
            "term_b_device": "server-01",
            "term_b_interface": "eth0",
            "length": "3m",
            "color": "blue",
            "type": "CAT6A",
            "description": "Sample cable",
            "date": "2024-01-15",
        }

        # Format template with sample data
        from .zpl.generator import SafeDict, ZPLGenerator

        generator = ZPLGenerator(dpi=template.dpi)
        sanitized = {k: generator.sanitize_field(str(v)) for k, v in sample_data.items()}
        zpl = template.zpl_template.format_map(SafeDict(sanitized))

        # Generate preview
        result = get_label_preview(
            zpl=zpl,
            dpi=template.dpi,
            width_mm=float(template.width_mm),
            height_mm=float(template.height_mm),
        )

        if result.success and result.image_data:
            return HttpResponse(
                result.image_data,
                content_type=result.content_type,
            )
        else:
            return JsonResponse(
                {"error": result.error or "Preview generation failed"},
                status=500,
            )


#
# PrintJob Views
#


class PrintJobListView(generic.ObjectListView):
    """List view for print job history."""

    queryset = PrintJob.objects.select_related("cable", "printer", "template", "printed_by")
    table = PrintJobTable
    filterset = PrintJobFilterSet
    filterset_form = PrintJobFilterForm
    actions = {
        "export": {"view"},
    }


class PrintJobView(generic.ObjectView):
    """Detail view for a print job."""

    queryset = PrintJob.objects.select_related("cable", "printer", "template", "printed_by")


class PrintJobDeleteView(generic.ObjectDeleteView):
    """Delete view for print jobs."""

    queryset = PrintJob.objects.all()


class PrintJobBulkDeleteView(generic.BulkDeleteView):
    """Bulk delete view for print jobs."""

    queryset = PrintJob.objects.all()
    filterset = PrintJobFilterSet
    table = PrintJobTable


#
# Cable Label Printing Views
#


@register_model_view(Cable, name="print_label", path="print-label")
class CablePrintLabelView(generic.ObjectView):
    """View for printing a label for a specific cable."""

    queryset = Cable.objects.all()
    template_name = "netbox_zpl_labels/cable_print_label.html"
    tab = ViewTab(
        label=_("Print Label"),
        permission="netbox_zpl_labels.add_printjob",
        weight=500,
    )

    def get_extra_context(self, request, instance):
        """Provide form and available printers/templates."""
        form = PrintLabelForm()
        preview_form = PreviewLabelForm()

        return {
            "form": form,
            "preview_form": preview_form,
            "printers": ZPLPrinter.objects.filter(status="active"),
            "templates": LabelTemplate.objects.all(),
            "active_tab": "print-label",
        }

    def post(self, request, pk):
        """Handle label print request."""
        cable = get_object_or_404(Cable, pk=pk)
        form = PrintLabelForm(request.POST)

        if form.is_valid():
            printer = form.cleaned_data["printer"]
            template = form.cleaned_data["template"]
            quantity = form.cleaned_data["quantity"]

            # Generate ZPL
            base_url = request.build_absolute_uri("/").rstrip("/")
            zpl_content = generate_cable_label(
                cable=cable,
                template=template,
                quantity=quantity,
                base_url=base_url,
            )

            # Send to printer
            success, error = send_to_printer(
                host=printer.host,
                port=printer.port,
                zpl_content=zpl_content,
            )

            # Log print job
            PrintJob.objects.create(
                cable=cable,
                printer=printer,
                template=template,
                quantity=quantity,
                zpl_content=zpl_content,
                success=success,
                error_message=error or "",
                printed_by=request.user if request.user.is_authenticated else None,
            )

            if success:
                messages.success(
                    request,
                    _("Label printed successfully to {printer}").format(printer=printer.name),
                )
            else:
                messages.error(
                    request,
                    _("Print failed: {error}").format(error=error),
                )

            return redirect(cable.get_absolute_url())

        # Form invalid, re-render
        return render(
            request,
            self.template_name,
            {
                "object": cable,
                "form": form,
                "preview_form": PreviewLabelForm(),
                "printers": ZPLPrinter.objects.filter(status="active"),
                "templates": LabelTemplate.objects.all(),
                "active_tab": "print-label",
            },
        )


class CableLabelPreviewView(View):
    """Generate preview for a cable label."""

    def get(self, request, pk):
        cable = get_object_or_404(Cable, pk=pk)
        template_id = request.GET.get("template")

        if not template_id:
            return JsonResponse({"error": "Template ID required"}, status=400)

        template = get_object_or_404(LabelTemplate, pk=template_id)

        # Generate ZPL
        base_url = request.build_absolute_uri("/").rstrip("/")
        zpl_content = generate_cable_label(
            cable=cable,
            template=template,
            quantity=1,
            base_url=base_url,
        )

        # Generate preview
        result = get_label_preview(
            zpl=zpl_content,
            dpi=template.dpi,
            width_mm=float(template.width_mm),
            height_mm=float(template.height_mm),
        )

        if result.success and result.image_data:
            return HttpResponse(
                result.image_data,
                content_type=result.content_type,
            )
        else:
            return JsonResponse(
                {"error": result.error or "Preview generation failed"},
                status=500,
            )


class CableLabelDownloadView(View):
    """Download ZPL code for a cable label."""

    def get(self, request, pk):
        cable = get_object_or_404(Cable, pk=pk)
        template_id = request.GET.get("template")

        if not template_id:
            # Use default template
            template = LabelTemplate.objects.filter(is_default=True).first()
            if not template:
                template = LabelTemplate.objects.first()
        else:
            template = get_object_or_404(LabelTemplate, pk=template_id)

        if not template:
            return JsonResponse({"error": "No template available"}, status=400)

        # Generate ZPL
        base_url = request.build_absolute_uri("/").rstrip("/")
        zpl_content = generate_cable_label(
            cable=cable,
            template=template,
            quantity=1,
            base_url=base_url,
        )

        # Return as downloadable file
        response = HttpResponse(zpl_content, content_type="text/plain")
        filename = f"cable_{cable.pk}_{cable.label or 'label'}.zpl"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


class CableBulkPrintLabelsView(GetReturnURLMixin, View):
    """Bulk print labels for multiple cables."""

    template_name = "netbox_zpl_labels/cable_bulk_print.html"

    def get(self, request):
        """Display form for bulk printing."""
        pk_list = request.GET.getlist("pk")

        if not pk_list:
            messages.warning(request, _("No cables selected."))
            return redirect("dcim:cable_list")

        cables = Cable.objects.filter(pk__in=pk_list)

        if not cables:
            messages.warning(request, _("No cables found."))
            return redirect("dcim:cable_list")

        form = BulkPrintLabelForm(initial={"pk": pk_list})

        return render(
            request,
            self.template_name,
            {
                "cables": cables,
                "form": form,
                "printers": ZPLPrinter.objects.filter(status="active"),
                "templates": LabelTemplate.objects.all(),
                "return_url": self.get_return_url(request),
            },
        )

    def post(self, request):
        """Process bulk print request."""
        pk_list = request.POST.getlist("pk")
        cables = Cable.objects.filter(pk__in=pk_list)
        form = BulkPrintLabelForm(request.POST)

        if form.is_valid():
            printer = form.cleaned_data["printer"]
            template = form.cleaned_data["template"]
            quantity_per_cable = form.cleaned_data["quantity_per_cable"]

            base_url = request.build_absolute_uri("/").rstrip("/")
            success_count = 0
            error_count = 0

            for cable in cables:
                zpl_content = generate_cable_label(
                    cable=cable,
                    template=template,
                    quantity=quantity_per_cable,
                    base_url=base_url,
                )

                success, error = send_to_printer(
                    host=printer.host,
                    port=printer.port,
                    zpl_content=zpl_content,
                )

                PrintJob.objects.create(
                    cable=cable,
                    printer=printer,
                    template=template,
                    quantity=quantity_per_cable,
                    zpl_content=zpl_content,
                    success=success,
                    error_message=error or "",
                    printed_by=request.user if request.user.is_authenticated else None,
                )

                if success:
                    success_count += 1
                else:
                    error_count += 1

            if success_count:
                messages.success(
                    request,
                    _("Printed {count} labels successfully.").format(count=success_count),
                )
            if error_count:
                messages.error(
                    request,
                    _("Failed to print {count} labels.").format(count=error_count),
                )

            return redirect(self.get_return_url(request))

        return render(
            request,
            self.template_name,
            {
                "cables": cables,
                "form": form,
                "printers": ZPLPrinter.objects.filter(status="active"),
                "templates": LabelTemplate.objects.all(),
                "return_url": self.get_return_url(request),
            },
        )
