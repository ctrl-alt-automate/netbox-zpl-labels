"""API URL routing for NetBox ZPL Labels plugin."""
from django.urls import path
from netbox.api.routers import NetBoxRouter

from . import views

router = NetBoxRouter()
router.APIRootView = views.ZPLPrinterViewSet

# Register viewsets
router.register("printers", views.ZPLPrinterViewSet)
router.register("templates", views.LabelTemplateViewSet)
router.register("jobs", views.PrintJobViewSet)

# Custom URL patterns for label operations
urlpatterns = [
    path("labels/generate/", views.LabelGenerateView.as_view(), name="label-generate"),
    path("labels/print/", views.LabelPrintView.as_view(), name="label-print"),
    path("labels/preview/", views.LabelPreviewView.as_view(), name="label-preview"),
]

urlpatterns += router.urls
