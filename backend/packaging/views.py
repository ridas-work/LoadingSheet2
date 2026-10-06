from django.db.models import Q
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError

from accounts.permissions import IsBatchClerkOrAdmin

from .models import PackagingMaterial
from .serializers import PackagingMaterialSerializer


class PackagingMaterialViewSet(viewsets.ModelViewSet):
    serializer_class = PackagingMaterialSerializer
    permission_classes = [IsBatchClerkOrAdmin]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        qs = PackagingMaterial.objects.filter(is_active=True)
        search = (self.request.query_params.get("search") or "").strip()
        if search:
            qs = qs.filter(
                Q(name__icontains=search)
                | Q(code__icontains=search)
                | Q(material_type__icontains=search)
            )
        return qs

    def perform_create(self, serializer):
        if "uip_qty" in self.request.data:
            raise ValidationError({"uip_qty": "UIP is read-only in this phase."})
        serializer.save()

    def perform_update(self, serializer):
        if "uip_qty" in self.request.data:
            raise ValidationError({"uip_qty": "UIP is read-only in this phase."})
        serializer.save()
