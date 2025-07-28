from rest_framework import viewsets, status, filters, pagination
from django.db import transaction
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.views import exception_handler
from rest_framework.permissions import DjangoModelPermissions
from rest_framework.decorators import action
from inventory.models import StockRecord
from inventory.serializers.stock_record_serializers import StockRecordSerializer
from safedelete.config import HARD_DELETE
from django.utils.translation import gettext_lazy as _

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
            "message": "Stock records retrieved successfully",
            "count": self.page.paginator.count,
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
            "results": data
        })

class StockRecordViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'head', 'options', 'delete']
    queryset = StockRecord.objects.all().order_by('-id')
    serializer_class = StockRecordSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['material', 'uom', 'location']
    search_fields = ['material__name', 'material__description', 'material__internal_code']
    ordering_fields = ['id', 'material', 'uom', 'quantity', 'location']
    pagination_class = CustomPagination
    permission_classes = [CustomDjangoModelPermissions]

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        if isinstance(response.data, dict) and "results" in response.data:
            response.data["status"] = "success"
            response.data["message"] = "Stock Records retrieved successfully"
            return response

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, context={**self.get_serializer_context(), 'action': 'retrieve'})
        return Response({
            "status": "success",
            "message": "Stock record retrieved successfully",
            "result": serializer.data
        }, status=status.HTTP_200_OK)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        if hasattr(instance, '_change_reason') and not getattr(instance, '_change_reason', None):
            instance._change_reason = "Created via API"
            instance.save()
        return Response({
            "status": "success",
            "message": "Stock record created successfully",
            "result": serializer.data
        }, status=status.HTTP_201_CREATED)

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        response = super().partial_update(request, *args, **kwargs)
        return Response({
            "status": "success",
            "message": "Stock record updated successfully",
            "result": response.data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='delete')
    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        try:
            instance = StockRecord.objects.all_with_deleted().get(pk=kwargs['pk'])  # type: ignore
        except StockRecord.DoesNotExist:
            return Response({
                "status": "error",
                "message": _("Stok kaydı bulunamadı")
            }, status=status.HTTP_404_NOT_FOUND)
        
        instance.delete()
        return Response({
            "status": "success",
            "message": _("Stok kaydı başarıyla silindi")
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='recover')
    @transaction.atomic
    def recover(self, request, *args, **kwargs):
        try:
            instance = StockRecord.objects.all_with_deleted().get(pk=kwargs['pk'])  # type: ignore
        except StockRecord.DoesNotExist:
            return Response({
                "status": "error",
                "message": _("Stok kaydı bulunamadı")
            }, status=status.HTTP_404_NOT_FOUND)
        
        if instance.deleted is not None:
            instance.undelete()
            serializer = self.get_serializer(instance)
            return Response({
                "status": "success",
                "message": _("Stok kaydı başarıyla geri yüklendi"),
                "result": serializer.data
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "status": "error",
                "message": _("Stok kaydı zaten silinmemiş")
            }, status=status.HTTP_400_BAD_REQUEST)
            

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if hasattr(instance, 'delete'):
            instance.delete(force_policy=HARD_DELETE)
        else:
            instance.delete()
        return Response({
            "status": "success",
            "message": "Stock record hard deleted successfully"
        }, status=status.HTTP_200_OK)


