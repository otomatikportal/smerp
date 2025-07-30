from rest_framework import viewsets, status, filters, pagination
from django.db import transaction
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import DjangoModelPermissions
from rest_framework.decorators import action
from safedelete.config import HARD_DELETE
from sales.models import VariableCost
from sales.serializers.variable_cost_serializers import VariableCostSerializer

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
            "message": "Variable Cost records retrieved successfully",
            "count": self.page.paginator.count,
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
            "results": data
        })
        
class VariableCostViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'delete']
    queryset = VariableCost.objects.all().order_by('-id')
    serializer_class = VariableCostSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['material__name', 'material__description', 'material__internal_code']
    ordering_fields = ['cost', 'id']
    pagination_class = CustomPagination
    permission_classes = [CustomDjangoModelPermissions]

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        if isinstance(response.data, dict) and "results" in response.data:
            response.data["status"] = "success"
            response.data["message"] = "Variable cost records retrieved successfully"
            return response

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, context={**self.get_serializer_context(), 'action': 'retrieve'})
        return Response({
            "status": "success",
            "message": "Variable cost record retrieved successfully",
            "result": serializer.data
        }, status=status.HTTP_200_OK)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        if isinstance(request.data, list):
            created_costs = []
            errors = []
            
            for i, cost_data in enumerate(request.data):
                serializer = self.get_serializer(data=cost_data)
                if serializer.is_valid():
                    validated_data = serializer.validated_data
                    validated_data['user'] = request.user
                    instance = serializer.save(**validated_data)
                    created_costs.append(self.get_serializer(instance).data)
                else:
                    errors.append({
                        "index": i,
                        "data": cost_data,
                        "errors": serializer.errors
                    })
            
            if errors:
                return Response({
                    "status": "validation_error",
                    "message": f"Validation failed for {len(errors)} variable costs",
                    "errors": errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({
                "status": "success",
                "message": f"Successfully created {len(created_costs)} variable cost records",
                "results": created_costs
            }, status=status.HTTP_201_CREATED)
        else:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
            validated_data['user'] = request.user
            instance = serializer.save(**validated_data)
            
            return Response({
                "status": "success",
                "message": "Variable cost record created successfully",
                "result": self.get_serializer(instance).data
            }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='delete')
    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        try:
            instance = VariableCost.objects.all_with_deleted().get(pk=kwargs['pk']) #type: ignore
        except VariableCost.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Variable cost record not found"
            }, status=status.HTTP_404_NOT_FOUND)
        
        instance.delete()
        return Response({
            "status": "success",
            "message": "Variable cost record deleted successfully"
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='recover')
    @transaction.atomic
    def recover(self, request, *args, **kwargs):
        try:
            instance = VariableCost.objects.all_with_deleted().get(pk=kwargs['pk']) #type: ignore
        except VariableCost.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Variable cost record not found"
            }, status=status.HTTP_404_NOT_FOUND)
        
        if instance.deleted is not None:
            instance.undelete()
            serializer = self.get_serializer(instance)
            return Response({
                "status": "success",
                "message": "Variable cost record recovered successfully",
                "result": serializer.data
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "status": "error",
                "message": "Variable cost record is not deleted"
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
            "message": "Variable cost record hard deleted successfully"
        }, status=status.HTTP_200_OK)

        

