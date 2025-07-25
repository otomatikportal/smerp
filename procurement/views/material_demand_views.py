from rest_framework import viewsets, status, filters, pagination
from django.db import transaction
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from procurement.models import MaterialDemand
from procurement.serializers.material_demand_serializers import MaterialDemandSerializer
from rest_framework.views import exception_handler
from rest_framework.permissions import DjangoModelPermissions
from rest_framework.decorators import action

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
            "message": "Material demands retrieved successfully",
            "count": self.page.paginator.count,
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
            "results": data
        })


class MaterialDemandViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'head', 'options', 'delete']
    """
    API endpoint for managing material demands.

    Filtering options:
      - filterset_fields: material, status, deadline
      - search_fields: description, demand_no
      - ordering_fields: id, demand_no, deadline, status
    """
    queryset = MaterialDemand.objects.all().order_by('-id')
    serializer_class = MaterialDemandSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['material', 'status', 'deadline']
    search_fields = ['description', 'demand_no']
    ordering_fields = ['id', 'demand_no', 'deadline', 'status']
    pagination_class = CustomPagination
    permission_classes = [CustomDjangoModelPermissions]

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        if isinstance(response.data, dict) and "results" in response.data:
            response.data["status"] = "success"
            response.data["message"] = "Material demands retrieved successfully"
            return response
        return Response({
            "status": "success",
            "message": "Material demands retrieved successfully",
            "results": response.data
        }, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, context={'action': 'retrieve'})
        return Response({
            "status": "success",
            "message": "Material demand retrieved successfully",
            "result": serializer.data
        }, status=status.HTTP_200_OK)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return Response({
            "status": "success",
            "message": "Material demand created successfully",
            "result": response.data
        }, status=status.HTTP_201_CREATED)

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        response = super().partial_update(request, *args, **kwargs)
        return Response({
            "status": "success",
            "message": "Material demand updated successfully",
            "result": response.data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='delete')
    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer()
        serializer.delete(instance)
        return Response({
            "status": "success",
            "message": "Material demand deleted successfully"
        }, status=status.HTTP_200_OK)

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete(force_policy=HARD_DELETE)
        return Response({
            "status": "success",
            "message": "Material demand hard deleted successfully"
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='recover')
    @transaction.atomic
    def recover(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.deleted is not None:
            instance.undelete()
        serializer = self.get_serializer(instance)
        return Response({
            "status": "success",
            "message": "Material demand recovered successfully",
            "result": serializer.data
        }, status=status.HTTP_200_OK)




