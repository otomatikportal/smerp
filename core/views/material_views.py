from rest_framework import viewsets, status, filters, pagination
from django.db import transaction
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from core.models import Material
from core.serializers.material_serializers import MaterialSerializer
from rest_framework.decorators import action
from rest_framework.permissions import DjangoModelPermissions
from safedelete.config import HARD_DELETE
from simple_history.utils import bulk_create_with_history

class CustomPagination(pagination.PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            "status": "success",
            "message": "Materials retrieved successfully",
            "count": self.page.paginator.count,
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
            "results": data
        })


class MaterialViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'head', 'options', 'delete']
    """
    API endpoint for managing materials.

    Filtering options:
      - filterset_fields: category, internal_code, name
      - search_fields: name, internal_code, description
      - ordering_fields: id, name, category, internal_code
    """
    queryset = Material.objects.all().order_by('-id')
    serializer_class = MaterialSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'internal_code', 'name']
    search_fields = ['name', 'internal_code', 'description']
    ordering_fields = ['id', 'name', 'category', 'internal_code']
    pagination_class = CustomPagination
    permission_classes = [DjangoModelPermissions]

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        if isinstance(response.data, dict) and "results" in response.data:
            response.data["status"] = "success"
            response.data["message"] = "Materials retrieved successfully"
            return response


    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "status": "success",
            "message": "Material retrieved successfully",
            "result": serializer.data
        }, status=status.HTTP_200_OK)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        
        if isinstance(request.data, list):
            
            validated_materials = []
            errors = []
            
            for i, material_data in enumerate(request.data):
                serializer = self.get_serializer(data=material_data)
                if serializer.is_valid():
                    validated_materials.append(serializer.validated_data)
                else:
                    errors.append({
                        "index": i,
                        "data": material_data,
                        "errors": serializer.errors
                    })
            
            if errors:
                return Response({
                    "status": "validation_error",
                    "message": f"Validation failed for {len(errors)} materials",
                    "errors": errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            material_objects = [Material(**data) for data in validated_materials]
            created_materials = bulk_create_with_history(
                material_objects,
                Material,
                default_user=request.user if request.user.is_authenticated else None
            )
            
            for material in created_materials:
                material.generate_internal_code()

            Material.objects.bulk_update(created_materials, ['internal_code'])            
            response_data = MaterialSerializer(created_materials, many=True).data
            
            return Response({
                "status": "success",
                "message": f"Successfully created {len(created_materials)} materials",
                "results": response_data
            }, status=status.HTTP_201_CREATED)
        else:
            # Single create (original behavior with signals)
            response = super().create(request, *args, **kwargs)
            return Response({
                "status": "success",
                "message": "Material created successfully",
                "result": response.data
            }, status=status.HTTP_201_CREATED)

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        response = super().partial_update(request, *args, **kwargs)
        return Response({
            "status": "success",
            "message": "Material updated successfully",
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
            "message": "Material deleted successfully"
        }, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        return Response({
            "status": "error",
            "message": "PUT method is not allowed for this resource. Use PATCH instead."
        }, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete(force_policy=HARD_DELETE)
        return Response({
            "status": "success",
            "message": "Material hard deleted successfully"
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
            "message": "Material recovered successfully",
            "results": serializer.data
        }, status=status.HTTP_200_OK)


