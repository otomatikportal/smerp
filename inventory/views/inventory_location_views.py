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
        try:
            queryset = self.filter_queryset(self.get_queryset())
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True, context={**self.get_serializer_context(), 'action': 'list'})
                return self.get_paginated_response(serializer.data)
            serializer = self.get_serializer(queryset, many=True, context={**self.get_serializer_context(), 'action': 'list'})
            return Response({
                "status": "success",
                "message": "Inventory locations retrieved successfully",
                "results": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as exc:
            return self.handle_exception(exc)


    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, context={**self.get_serializer_context(), 'action': 'retrieve'})
            return Response({
                "status": "success",
                "message": "Inventory location retrieved successfully",
                "result": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as exc:
            return self.handle_exception(exc)


    @transaction.atomic
    def create(self, request, *args, **kwargs):
        try:
            # Extract relevant fields from request data
            data = request.data
            unique_fields = ['facility', 'area', 'section', 'shelf', 'bin', 'type', 'name']
            filter_kwargs = {field: data.get(field) for field in unique_fields if data.get(field) is not None}

            # Find a soft-deleted instance using safedelete's deleted field
            existing = InventoryLocation.all_objects.filter(**filter_kwargs).filter(deleted__isnull=False).first()
            if existing:
                existing.undelete()
                # Apply partial update with request data
                serializer = self.get_serializer(existing, data=data)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                return Response({
                    "status": "success",
                    "message": "Inventory location recovered and updated successfully",
                    "result": serializer.data
                }, status=status.HTTP_200_OK)

            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            instance = serializer.save()
            instance._change_reason = "Created via API"
            instance.save()
            
            return Response({
                "status": "success",
                "message": "Inventory location created successfully",
                "result": serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as exc:
            return self.handle_exception(exc)


    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        try:
            response = super().partial_update(request, *args, **kwargs)
            return Response({
                "status": "success",
                "message": "Inventory location updated successfully",
                "result": response.data
            }, status=status.HTTP_200_OK)
        except Exception as exc:
            return self.handle_exception(exc)


    @action(detail=True, methods=['post'], url_path='delete')
    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            instance.delete()
            return Response({
                "status": "success",
                "message": "Inventory location deleted successfully"
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
            "message": "Inventory location recovered successfully"
        }, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        return Response({
            "status": "error",
            "message": "PUT method is not allowed for this resource. Use PATCH instead."
        }, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            # Use safedelete's HARD_DELETE policy for permanent deletion
            if hasattr(instance, 'delete'):
                instance.delete(force_policy=HARD_DELETE)
            else:
                instance.delete()
            return Response({
                "status": "success",
                "message": "Inventory location hard deleted successfully"
            }, status=status.HTTP_200_OK)
        except Exception as exc:
            return self.handle_exception(exc)

    def handle_exception(self, exc):
        response = exception_handler(exc, self.get_exception_handler_context())
        if response is not None:
            response.data = {
                "status": "error",
                "message": str(exc),
                "details": response.data
            }
            return response
        # Fallback 500 error
        return Response({
            "status": "error",
            "message": "Internal server error",
            "details": str(exc)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)