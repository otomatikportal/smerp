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
    http_method_names = ['get', 'post', 'patch', 'head', 'options', 'delete']
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
        try:
            response = super().list(request, *args, **kwargs)
            if isinstance(response.data, dict) and "results" in response.data:
                response.data["status"] = "success"
                response.data["message"] = "Procurement order lines retrieved successfully"
                return response
            return Response({
                "status": "success",
                "message": "Procurement order lines retrieved successfully",
                "results": response.data
            }, status=status.HTTP_200_OK)
        except Exception as exc:
            return self.handle_exception(exc)

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, context={'action': 'retrieve'})
            return Response({
                "status": "success",
                "message": "Procurement order line retrieved successfully",
                "result": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as exc:
            return self.handle_exception(exc)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        try:
            response = super().create(request, *args, **kwargs)
            return Response({
                "status": "success",
                "message": "Procurement order line created successfully",
                "result": response.data
            }, status=status.HTTP_201_CREATED)
        except Exception as exc:
            return self.handle_exception(exc)

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({
                "status": "success",
                "message": "Procurement order line updated successfully",
                "result": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as exc:
            return self.handle_exception(exc)

    @action(detail=True, methods=['post'], url_path='delete', permission_classes=[DjangoModelPermissions])
    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer()
            # Soft delete (SafeDeleteModel)
            serializer.delete(instance)
            return Response({
                "status": "success",
                "message": "Procurement order line soft deleted successfully"
            }, status=status.HTTP_200_OK)
        except Exception as exc:
            return self.handle_exception(exc)

    def update(self, request, *args, **kwargs):
        return Response({
            "status": "error",
            "message": "PUT method is not allowed for this resource. Use PATCH instead."
        }, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            instance.delete(force_policy=HARD_DELETE)
            return Response({
                "status": "success",
                "message": "Procurement order line hard deleted successfully"
            }, status=status.HTTP_200_OK)
        except Exception as exc:
            return self.handle_exception(exc)

    @action(detail=True, methods=['post'], url_path='recover')
    @transaction.atomic
    def recover(self, request, *args, **kwargs):
        instance = self.get_object()
        if hasattr(instance, 'undelete'):
            instance.undelete()
        else:
            instance.save()
        return Response({
            "status": "success",
            "message": "Procurement order line recovered successfully"
        }, status=status.HTTP_200_OK)

    def handle_exception(self, exc):
        response = exception_handler(exc, self.get_exception_handler_context())
        if response is not None:
            response.data = {
                "status": "error",
                "message": str(exc),
                "details": response.data
            }
            return response
        return Response({
            "status": "error",
            "message": "Internal server error",
            "details": str(exc)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
