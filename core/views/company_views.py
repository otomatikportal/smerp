from rest_framework import viewsets, status, filters, pagination
from django.db import transaction
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from core.models import Company
from core.serializers.company_serializers import CompanySerializer
from rest_framework.permissions import DjangoModelPermissions
from rest_framework.decorators import action
from safedelete.config import HARD_DELETE
from simple_history.utils import bulk_create_with_history

class CustomPagination(pagination.PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            "status": "success",
            "message": "Companies retrieved successfully",
            "count": self.page.paginator.count,
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
            "results": data
        })


class CompanyViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing companies.

    Filtering options:
      - filterset_fields: name, legal_name, e_mail, website, phone
      - search_fields: name, legal_name, e_mail, website, phone, description
      - ordering_fields: id, name, legal_name
    """
    http_method_names = ['get', 'post', 'patch', 'delete']
    queryset = Company.objects.all().order_by('-id')
    serializer_class = CompanySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['name', 'legal_name', 'e_mail', 'website', 'phone']
    search_fields = ['name', 'legal_name', 'e_mail', 'website', 'phone', 'description']
    ordering_fields = ['id', 'name', 'legal_name']
    pagination_class = CustomPagination
    permission_classes = [DjangoModelPermissions]

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "status": "success",
            "message": "Company retrieved successfully",
            "result": serializer.data
        }, status=status.HTTP_200_OK)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        
        if isinstance(request.data, list):
            
            validated_companies = []
            errors = []
            
            for i, company_data in enumerate(request.data):
                serializer = self.get_serializer(data=company_data)
                if serializer.is_valid():
                    validated_companies.append(serializer.validated_data)
                else:
                    errors.append({
                        "index": i,
                        "data": company_data,
                        "errors": serializer.errors
                    })
            
            if errors:
                return Response({
                    "status": "validation_error",
                    "message": f"Validation failed for {len(errors)} companies",
                    "errors": errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            company_objects = [Company(**data) for data in validated_companies]
            created_companies = bulk_create_with_history(
                company_objects,
                Company,
                default_user=request.user if request.user.is_authenticated else None
            )
                       
            response_data = CompanySerializer(created_companies, many=True).data
            
            return Response({
                "status": "success",
                "message": f"Successfully created {len(created_companies)} companies",
                "results": response_data
            }, status=status.HTTP_201_CREATED)
        
        else:        
            
            response = super().create(request, *args, **kwargs)
            response.data = {
                "status": "success",
                "message": "Company created successfully",
                "result": response.data
            }
            response.status_code = status.HTTP_201_CREATED
            return response

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        response = super().partial_update(request, *args, **kwargs)
        response.data = {
            "status": "success",
            "message": "Company updated successfully",
            "result": response.data
        }
        return response

    @action(detail=True, methods=['post'], url_path='delete')
    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer()
        serializer.delete(instance)
        return Response({
            "status": "success",
            "message": "Company deleted successfully"
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
            "message": "Company recovered successfully"
        }, status=status.HTTP_200_OK)

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete(force_policy=HARD_DELETE)
        return Response({
            "status": "success",
            "message": "Company hard deleted successfully"
        }, status=status.HTTP_200_OK)
