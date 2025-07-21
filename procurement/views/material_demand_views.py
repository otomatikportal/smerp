from rest_framework import viewsets, status, filters, pagination
from django.db import transaction
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from procurement.models import MaterialDemand
from procurement.serializers.material_demand_serializers import MaterialDemandSerializer
from rest_framework.views import exception_handler
from rest_framework.permissions import DjangoModelPermissions
from rest_framework.decorators import action


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
    permission_classes = [DjangoModelPermissions]

    def list(self, request, *args, **kwargs):
        try:
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
        except Exception as exc:
            return self.handle_exception(exc)

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, context={'action': 'retrieve'})
            return Response({
                "status": "success",
                "message": "Material demand retrieved successfully",
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
                "message": "Material demand created successfully",
                "result": response.data
            }, status=status.HTTP_201_CREATED)
        except Exception as exc:
            return self.handle_exception(exc)

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        try:
            response = super().partial_update(request, *args, **kwargs)
            return Response({
                "status": "success",
                "message": "Material demand updated successfully",
                "result": response.data
            }, status=status.HTTP_200_OK)
        except Exception as exc:
            return self.handle_exception(exc)

    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer()
            serializer.delete(instance)
            return Response({
                "status": "success",
                "message": "Material demand deleted successfully"
            }, status=status.HTTP_200_OK)
        except Exception as exc:
            return self.handle_exception(exc)

    def update(self, request, *args, **kwargs):
        return Response({
            "status": "error",
            "message": "PUT method is not allowed for this resource. Use PATCH instead."
        }, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def destroy(self, request, *args, **kwargs):
        return Response({
            "status": "error",
            "message": "DELETE method is not allowed for this resource. Use the custom 'delete' action instead."
        }, status=status.HTTP_405_METHOD_NOT_ALLOWED)

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
            "message": "Material demand recovered successfully"
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


