from rest_framework import viewsets, status, filters, pagination
from django.db import transaction
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.views import exception_handler
from rest_framework.permissions import DjangoModelPermissions
from rest_framework.decorators import action
from inventory.models import InventoryLocation
from inventory.serializers.inventory_location_serializers import InventoryLocationSerializer
from safedelete.config import HARD_DELETE
from django.utils.translation import gettext_lazy as _
from simple_history.utils import bulk_create_with_history

class CustomDjangoModelPermissions(DjangoModelPermissions):
    perms_map = {
        'GET': ['%(app_label)s.view_%(model_name)s'],
        'OPTIONS': [],
        'HEAD': [],
        'POST': ['%(app_label)s.add_%(model_name)s'],
        'PUT': ['%(app_label)s.change_%(model_name)s'],
        'PATCH': ['%(app_label)s.change_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }


class CustomPagination(pagination.PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            "status": "success",
            "message": "Inventory locations retrieved successfully",
            "count": self.page.paginator.count,
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
            "results": data
        })


class InventoryLocationViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'head', 'options', 'delete']
    """
    API endpoint for managing inventory locations.

    Filtering options:
      - filterset_fields: facility, area, section, shelf, bin, type
      - search_fields: name
      - ordering_fields: id, name, facility, area, section, shelf, bin, type
    """
    queryset = InventoryLocation.objects.all().order_by('-id')
    serializer_class = InventoryLocationSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['facility', 'area', 'section', 'shelf', 'bin', 'type']
    search_fields = ['name']
    ordering_fields = ['id', 'name', 'facility', 'area', 'section', 'shelf', 'bin', 'type']
    pagination_class = CustomPagination
    permission_classes = [CustomDjangoModelPermissions]
    

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        if isinstance(response.data, dict) and "results" in response.data:
            response.data["status"] = "success"
            response.data["message"] = "Inventory Locations retrieved successfully"
            return response


    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, context={**self.get_serializer_context(), 'action': 'retrieve'})
        return Response({
            "status": "success",
            "message": "Inventory location retrieved successfully",
            "result": serializer.data
        }, status=status.HTTP_200_OK)


    @transaction.atomic
    def create(self, request, *args, **kwargs):
        data = request.data
        is_many = isinstance(data, list)
        data_list = data if is_many else [data]
        unique_fields = ['facility', 'area', 'section', 'shelf', 'bin']

        to_bulk_create = []
        created_count = 0
        recovered_count = 0
        skipped_count = 0
        error_count = 0

        for item in data_list:
            # Build filter kwargs
            filter_kwargs = {field: item.get(field) for field in unique_fields}
            if any(v is None for v in filter_kwargs.values()):
                error_count += 1
                continue

            existing = InventoryLocation.all_objects.filter(**filter_kwargs).first()

            if existing and not existing.deleted:
                # Active → skip
                skipped_count += 1
            elif existing and existing.deleted:
                # Soft-deleted → recover
                existing.undelete()
                for key, val in item.items():
                    if hasattr(existing, key):
                        setattr(existing, key, val)
                if not existing.name:
                    existing.name = InventoryLocation.generate_name(
                        facility=existing.facility,
                        area=existing.area,
                        section=existing.section,
                        shelf=existing.shelf,
                        bin=existing.bin
                    )
                existing._change_reason = "Recovered and updated via bulk API"
                existing.save()
                recovered_count += 1
            else:
                # New object
                serializer = self.get_serializer(data=item)
                try:
                    serializer.is_valid(raise_exception=True)
                    validated_data = serializer.validated_data

                    if not validated_data.get('name'):
                        validated_data['name'] = InventoryLocation.generate_name(
                            facility=validated_data.get('facility'),
                            area=validated_data.get('area'),
                            section=validated_data.get('section'),
                            shelf=validated_data.get('shelf'),
                            bin=validated_data.get('bin')
                        )

                    obj = InventoryLocation(**validated_data)
                    obj._change_reason = "Created via bulk API"
                    to_bulk_create.append(obj)
                    created_count += 1
                except Exception:
                    error_count += 1

        # Bulk create new objects
        if to_bulk_create:
            bulk_create_with_history(
                to_bulk_create,
                InventoryLocation,
                batch_size=100,
                default_user=request.user,
                default_change_reason="Created via bulk API"
            )

        # === Final Response Logic ===
        total_processed = len(data_list)
        any_success = created_count > 0 or recovered_count > 0 or skipped_count > 0
        has_errors = error_count > 0
        has_creations = created_count > 0

        if has_errors and not any_success:
            status_code = status.HTTP_400_BAD_REQUEST
            response_status = "error"
            message = _("Hiçbir envanter konumu oluşturulamadı. Girdi verilerinde hatalar var.")
        else:
            parts = []
            if created_count:
                parts.append(_("%(count)d tane oluşturuldu") % {'count': created_count})
            if recovered_count:
                parts.append(_("%(count)d tane kurtarıldı") % {'count': recovered_count})
            if skipped_count:
                parts.append(_("%(count)d tane zaten var, atlandı") % {'count': skipped_count})
            if error_count:
                parts.append(_("%(count)d tane hatalı veri" ) % {'count': error_count})

            message = _("; ".join(parts)) + "."
            response_status = "success"
            status_code = status.HTTP_201_CREATED if created_count > 0 else status.HTTP_200_OK

        return Response({
            "status": response_status,
            "message": message,
            "summary": {
                "total": total_processed,
                "created": created_count,
                "recovered": recovered_count,
                "skipped": skipped_count,
                "errors": error_count,
            }
        }, status=status_code)


    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        response = super().partial_update(request, *args, **kwargs)
        return Response({
            "status": "success",
            "message": "Inventory location updated successfully",
            "result": response.data
        }, status=status.HTTP_200_OK)


    @action(detail=True, methods=['post'], url_path='delete')
    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        try:
            instance = InventoryLocation.objects.all_with_deleted().get(pk=kwargs['pk'])  # type: ignore
        except InventoryLocation.DoesNotExist:
            return Response({
                "status": "error",
                "message": _("Envanter lokasyonu bulunamadı")
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if there are any StockRecord objects using this location
        if hasattr(instance, 'stockrecord_set') and instance.stockrecord_set.exists():
            return Response({
                "status": "error",
                "message": _("Bu lokasyonda stok kayıtları bulunduğu için silinemez. Önce stok kayıtlarını başka bir lokasyona taşıyın.")
            }, status=status.HTTP_400_BAD_REQUEST)
        
        instance.delete()
        return Response({
            "status": "success",
            "message": _("Envanter lokasyonu başarıyla silindi")
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='recover')
    @transaction.atomic
    def recover(self, request, *args, **kwargs):
        try:
            instance = InventoryLocation.objects.all_with_deleted().get(pk=kwargs['pk'])  # type: ignore
        except InventoryLocation.DoesNotExist:
            return Response({
                "status": "error",
                "message": _("Envanter lokasyonu bulunamadı")
            }, status=status.HTTP_404_NOT_FOUND)
        
        if instance.deleted is not None:
            instance.undelete()
            serializer = self.get_serializer(instance)
            return Response({
                "status": "success",
                "message": _("Envanter lokasyonu başarıyla geri yüklendi"),
                "result": serializer.data
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "status": "error",
                "message": _("Envanter lokasyonu zaten silinmemiş")
            }, status=status.HTTP_400_BAD_REQUEST)

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # Use safedelete's HARD_DELETE policy for permanent deletion
        if hasattr(instance, 'delete'):
            instance.delete(force_policy=HARD_DELETE)
        else:
            instance.delete()
        return Response({
            "status": "success",
            "message": "Inventory location hard deleted successfully"
        }, status=status.HTTP_200_OK)

