"""API views for NetBox ZPL Labels plugin."""

from dcim.models import Cable
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from netbox.api.authentication import TokenAuthentication
from netbox.api.viewsets import NetBoxModelViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..filtersets import LabelTemplateFilterSet, PrintJobFilterSet, ZPLPrinterFilterSet
from ..models import LabelTemplate, PrintJob, ZPLPrinter
from ..zpl import generate_cable_label, get_label_preview
from ..zpl.printer import ZPLPrinterClient, check_printer_connection
from .serializers import (
    GenerateLabelResponseSerializer,
    GenerateLabelSerializer,
    LabelTemplateSerializer,
    PrintJobSerializer,
    PrintLabelResponseSerializer,
    PrintLabelSerializer,
    TestConnectionSerializer,
    ZPLPrinterSerializer,
)


class ZPLPrinterViewSet(NetBoxModelViewSet):
    """API viewset for ZPL printers."""

    queryset = ZPLPrinter.objects.all()
    serializer_class = ZPLPrinterSerializer
    filterset_class = ZPLPrinterFilterSet

    @action(detail=True, methods=["post"])
    def test(self, request, pk=None):
        """Test connection to the printer.

        POST /api/plugins/zpl-labels/printers/{id}/test/
        """
        printer = self.get_object()
        success, error = check_printer_connection(
            host=printer.host,
            port=printer.port,
        )

        serializer = TestConnectionSerializer(
            data={
                "success": success,
                "message": "Connection successful" if success else error,
            }
        )
        serializer.is_valid()

        return Response(
            serializer.data,
            status=status.HTTP_200_OK if success else status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    @action(detail=True, methods=["get"])
    def status(self, request, pk=None):
        """Get real-time printer status.

        GET /api/plugins/zpl-labels/printers/{id}/status/

        Queries the printer directly for status information including
        paper/ribbon status and online state. Also updates the printer's
        last_checked and last_online fields.
        """
        printer = self.get_object()
        client = ZPLPrinterClient(host=printer.host, port=printer.port)

        # Test connection first
        connection_result = client.test_connection()
        online = connection_result.success

        # Update printer status tracking
        printer.update_status(online=online)

        if not online:
            return Response(
                {
                    "printer_id": printer.pk,
                    "printer_name": printer.name,
                    "online": False,
                    "connection_error": connection_result.error,
                    "paper": None,
                    "ribbon": None,
                    "raw_status": None,
                    "last_checked": printer.last_checked.isoformat(),
                },
                status=status.HTTP_200_OK,
            )

        # Get detailed status
        printer_status = client.get_printer_status()

        return Response(
            {
                "printer_id": printer.pk,
                "printer_name": printer.name,
                "online": True,
                "connection_error": None,
                "paper": printer_status.get("paper") if printer_status else None,
                "ribbon": printer_status.get("ribbon") if printer_status else None,
                "raw_status": (
                    printer_status.get("raw_response") if printer_status else None
                ),
                "last_checked": printer.last_checked.isoformat(),
            },
            status=status.HTTP_200_OK,
        )


class LabelTemplateViewSet(NetBoxModelViewSet):
    """API viewset for label templates."""

    queryset = LabelTemplate.objects.all()
    serializer_class = LabelTemplateSerializer
    filterset_class = LabelTemplateFilterSet

    @action(detail=True, methods=["get"])
    def preview(self, request, pk=None):
        """Generate preview image for the template.

        GET /api/plugins/zpl-labels/templates/{id}/preview/

        Returns PNG image.
        """
        template = self.get_object()

        # Sample data for preview
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

        from ..zpl.generator import SafeDict, ZPLGenerator

        generator = ZPLGenerator(dpi=template.dpi)
        sanitized = {k: generator.sanitize_field(str(v)) for k, v in sample_data.items()}
        zpl = template.zpl_template.format_map(SafeDict(sanitized))

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

        return Response(
            {"error": result.error or "Preview generation failed"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class PrintJobViewSet(NetBoxModelViewSet):
    """API viewset for print jobs."""

    queryset = PrintJob.objects.select_related("cable", "printer", "template", "printed_by")
    serializer_class = PrintJobSerializer
    filterset_class = PrintJobFilterSet

    # Disable create/update - print jobs are created via /labels/print/
    http_method_names = ["get", "delete", "head", "options"]


class LabelGenerateView(APIView):
    """Generate ZPL code for cable labels.

    POST /api/plugins/zpl-labels/labels/generate/
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = GenerateLabelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cable_ids = serializer.validated_data["cable_ids"]
        template_id = serializer.validated_data.get("template_id")

        # Get template
        if template_id:
            template = get_object_or_404(LabelTemplate, pk=template_id)
        else:
            template = LabelTemplate.objects.filter(is_default=True).first()
            if not template:
                return Response(
                    {"error": "No default template configured"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Get base URL
        base_url = request.build_absolute_uri("/").rstrip("/")

        # Generate labels
        labels = []
        for cable_id in cable_ids:
            try:
                cable = Cable.objects.get(pk=cable_id)
                zpl = generate_cable_label(
                    cable=cable,
                    template=template,
                    quantity=1,
                    base_url=base_url,
                )
                labels.append(
                    {
                        "cable_id": cable.pk,
                        "cable_label": cable.label or f"CBL-{cable.pk}",
                        "zpl": zpl,
                    }
                )
            except Cable.DoesNotExist:
                continue

        response_serializer = GenerateLabelResponseSerializer(labels, many=True)
        return Response({"labels": response_serializer.data})


class LabelPrintView(APIView):
    """Print labels for cables.

    POST /api/plugins/zpl-labels/labels/print/
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PrintLabelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cable_ids = serializer.validated_data["cable_ids"]
        printer_id = serializer.validated_data["printer_id"]
        template_id = serializer.validated_data.get("template_id")
        copies = serializer.validated_data.get("copies", 1)

        # Get printer
        printer = get_object_or_404(ZPLPrinter, pk=printer_id)

        if printer.status != "active":
            return Response(
                {"error": f"Printer '{printer.name}' is not active"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get template
        if template_id:
            template = get_object_or_404(LabelTemplate, pk=template_id)
        else:
            template = LabelTemplate.objects.filter(is_default=True).first()
            if not template:
                return Response(
                    {"error": "No default template configured"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Get base URL
        base_url = request.build_absolute_uri("/").rstrip("/")

        # First pass: Generate all ZPL and collect valid cables
        cables_data = []  # List of (cable, zpl) tuples
        jobs = []
        failed = 0

        for cable_id in cable_ids:
            try:
                cable = Cable.objects.get(pk=cable_id)
            except Cable.DoesNotExist:
                jobs.append(
                    {
                        "cable_id": cable_id,
                        "status": "error",
                        "error": "Cable not found",
                        "job_id": None,
                    }
                )
                failed += 1
                continue

            # Generate ZPL
            zpl = generate_cable_label(
                cable=cable,
                template=template,
                quantity=copies,
                base_url=base_url,
            )
            cables_data.append((cable, zpl))

        # Second pass: Send all labels in a single connection (batch printing)
        printed = 0
        if cables_data:
            zpl_contents = [zpl for _, zpl in cables_data]
            client = ZPLPrinterClient(host=printer.host, port=printer.port)

            try:
                results = client.send_zpl_batch(zpl_contents)
            except Exception as e:
                # Connection failed entirely - mark all as failed
                for cable, zpl in cables_data:
                    job = PrintJob.objects.create(
                        cable=cable,
                        printer=printer,
                        template=template,
                        quantity=copies,
                        zpl_content=zpl,
                        success=False,
                        error_message=str(e),
                        printed_by=request.user if request.user.is_authenticated else None,
                    )
                    failed += 1
                    jobs.append(
                        {
                            "cable_id": cable.pk,
                            "status": "failed",
                            "error": str(e),
                            "job_id": job.pk,
                        }
                    )
            else:
                # Create print job records and build response
                for (cable, zpl), result in zip(cables_data, results, strict=True):
                    job = PrintJob.objects.create(
                        cable=cable,
                        printer=printer,
                        template=template,
                        quantity=copies,
                        zpl_content=zpl,
                        success=result.success,
                        error_message=result.error or "",
                        printed_by=request.user if request.user.is_authenticated else None,
                    )

                    if result.success:
                        printed += 1
                        jobs.append(
                            {
                                "cable_id": cable.pk,
                                "status": "printed",
                                "error": None,
                                "job_id": job.pk,
                            }
                        )
                    else:
                        failed += 1
                        jobs.append(
                            {
                                "cable_id": cable.pk,
                                "status": "failed",
                                "error": result.error,
                                "job_id": job.pk,
                            }
                        )

        response_data = {
            "status": "success" if failed == 0 else "partial" if printed > 0 else "failed",
            "printed": printed,
            "failed": failed,
            "jobs": jobs,
        }

        response_serializer = PrintLabelResponseSerializer(data=response_data)
        response_serializer.is_valid()

        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK if printed > 0 else status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class LabelPreviewView(APIView):
    """Generate preview image for a cable label.

    GET /api/plugins/zpl-labels/labels/preview/?cable_id=X&template_id=Y
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cable_id = request.query_params.get("cable_id")
        template_id = request.query_params.get("template_id")

        if not cable_id:
            return Response(
                {"error": "cable_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cable = get_object_or_404(Cable, pk=cable_id)

        # Get template
        if template_id:
            template = get_object_or_404(LabelTemplate, pk=template_id)
        else:
            template = LabelTemplate.objects.filter(is_default=True).first()
            if not template:
                return Response(
                    {"error": "No default template configured"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Generate ZPL
        base_url = request.build_absolute_uri("/").rstrip("/")
        zpl = generate_cable_label(
            cable=cable,
            template=template,
            quantity=1,
            base_url=base_url,
        )

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

        return Response(
            {"error": result.error or "Preview generation failed"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
