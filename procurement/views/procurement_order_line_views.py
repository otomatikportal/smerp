from rest_framework import viewsets, status, filters, pagination
from django.db import transaction
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from procurement.models import ProcurementOrderLine
from procurement.serializers.procurement_order_line_serializers import ProcurementOrderLineSerializer
from rest_framework.views import exception_handler
from rest_framework.permissions import DjangoModelPermissions, IsAuthenticated
from rest_framework.decorators import action
from safedelete.config import HARD_DELETE
from django.conf import settings

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
            "message": "Procurement order lines retrieved successfully",
            "count": self.page.paginator.count,
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
            "results": data
        })

class ProcurementOrderLineViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete']
    """
    API endpoint for managing procurement order lines.

    Filtering options:
      - filterset_fields: po, material, uom
      - search_fields: description
      - ordering_fields: id, po, material
    """
    queryset = ProcurementOrderLine.objects.all().order_by('-id')
    serializer_class = ProcurementOrderLineSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['po', 'material', 'uom']
    search_fields = []
    ordering_fields = ['id', 'po', 'material']
    pagination_class = CustomPagination
    permission_classes = [CustomDjangoModelPermissions]


    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        if isinstance(response.data, dict) and "results" in response.data:
            response.data["status"] = "success"
            response.data["message"] = "Procurement order lines retrieved successfully"
            return response


    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, context={'action': 'retrieve'})
        return Response({
            "status": "success",
            "message": "Procurement order line retrieved successfully",
            "result": serializer.data
        }, status=status.HTTP_200_OK)


    @transaction.atomic
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return Response({
            "status": "success",
            "message": "Procurement order line created successfully",
            "result": response.data
        }, status=status.HTTP_201_CREATED)


    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            "status": "success",
            "message": "Procurement order line updated successfully",
            "result": serializer.data
        }, status=status.HTTP_200_OK)


    @action(detail=True, methods=['post'], url_path='delete', permission_classes=[DjangoModelPermissions])
    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        try:
            instance = ProcurementOrderLine.objects.all_with_deleted().get(pk=kwargs['pk']) # type: ignore
        except ProcurementOrderLine.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Procurement order line not found"
            }, status=status.HTTP_404_NOT_FOUND)
        
        instance.delete()
        return Response({
            "status": "success",
            "message": "Procurement order line soft deleted successfully"
        }, status=status.HTTP_200_OK)


    @action(detail=True, methods=['post'], url_path='recover')
    @transaction.atomic
    def recover(self, request, *args, **kwargs):
        try:
            instance = ProcurementOrderLine.objects.all_with_deleted().get(pk=kwargs['pk']) # type: ignore
        except ProcurementOrderLine.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Procurement order line not found"
            }, status=status.HTTP_404_NOT_FOUND)
        
        if instance.deleted is not None:
            instance.undelete()
            serializer = self.get_serializer(instance)
            return Response({
                "status": "success",
                "message": "Procurement order line recovered successfully",
                "result": serializer.data
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "status": "error",
                "message": "Procurement order line is not deleted"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        
    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete(force_policy=HARD_DELETE)
        return Response({
            "status": "success",
            "message": "Procurement order line hard deleted successfully"
        }, status=status.HTTP_200_OK)


