from rest_framework import viewsets, status, filters, pagination
from django.db import transaction
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from core.models import Company
from core.serializers.company_serializers import CompanySerializer
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
    queryset = Company.objects.all().order_by('-id')
    serializer_class = CompanySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['name', 'legal_name', 'e_mail', 'website', 'phone']
    search_fields = ['name', 'legal_name', 'e_mail', 'website', 'phone', 'description']
    ordering_fields = ['id', 'name', 'legal_name']
    pagination_class = CustomPagination
    permission_classes = [DjangoModelPermissions]

    def list(self, request, *args, **kwargs):
        try:
            response = super().list(request, *args, **kwargs)
            if isinstance(response.data, dict) and "results" in response.data:
                response.data["status"] = "success"
                response.data["message"] = "Companies retrieved successfully"
                return response
            return Response({
                "status": "success",
                "message": "Companies retrieved successfully",
                "results": response.data
            }, status=status.HTTP_200_OK)
        except Exception as exc:
            return self.handle_exception(exc)

    def retrieve(self, request, *args, **kwargs):
        print('executed')
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, context={'action': 'retrieve'})
            return Response({
                "status": "success",
                "message": "Company retrieved successfully",
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
                "message": "Company created successfully",
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
                "message": "Company updated successfully",
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
                "message": "Company deleted successfully"
            }, status=status.HTTP_200_OK)
        except Exception as exc:
            return self.handle_exception(exc)
        
    @action(detail=True, methods=['post'], url_path='recover')
    @transaction.atomic
    def recover(self, request, *args, **kwargs):
        instance = self.get_object()
        # Example for a custom is_deleted flag:
        # instance.is_deleted = False
        # instance.save()
        # If using safedelete or similar, use undelete method:
        if hasattr(instance, 'undelete'):
            instance.undelete()
        else:
            # fallback: just save (no-op if not soft deleted)
            instance.save()
        return Response({
            "status": "success",
            "message": "Company recovered successfully"
        }, status=status.HTTP_200_OK)

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
