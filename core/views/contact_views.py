from rest_framework import viewsets, status, filters, pagination
from django.db import transaction
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from core.models import Contact
from core.serializers.contact_serializers import ContactSerializer
from rest_framework.views import exception_handler
from rest_framework.permissions import DjangoModelPermissions
from rest_framework.decorators import action
from safedelete.config import HARD_DELETE

class CustomPagination(pagination.PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            "status": "success",
            "message": "Contacts retrieved successfully",
            "count": self.page.paginator.count,
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
            "results": data
        })


class ContactViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'head', 'options', 'delete']
    """
    API endpoint for managing contacts.

    Filtering options:
      - filterset_fields: company, name, last_name, gender, role, e_mail, phone
      - search_fields: name, last_name, e_mail, phone, description
      - ordering_fields: id, name, last_name, company
    """
    queryset = Contact.objects.all().order_by('-id')
    serializer_class = ContactSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['company', 'name', 'last_name', 'gender', 'role', 'e_mail', 'phone']
    search_fields = ['name', 'last_name', 'e_mail', 'phone', 'description']
    ordering_fields = ['id', 'name', 'last_name', 'company']
    pagination_class = CustomPagination
    permission_classes = [DjangoModelPermissions]

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        if isinstance(response.data, dict) and "results" in response.data:
            response.data["status"] = "success"
            response.data["message"] = "Contacts retrieved successfully"
            return response

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "status": "success",
            "message": "Contact retrieved successfully",
            "result": serializer.data
        }, status=status.HTTP_200_OK)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        from simple_history.utils import bulk_create_with_history
        if isinstance(request.data, list):
            validated_contacts = []
            errors = []

            for i, contact_data in enumerate(request.data):
                serializer = self.get_serializer(data=contact_data)
                if serializer.is_valid():
                    validated_contacts.append(serializer.validated_data)
                else:
                    errors.append({
                        "index": i,
                        "data": contact_data,
                        "errors": serializer.errors
                    })

            if errors:
                return Response({
                    "status": "validation_error",
                    "message": f"Validation failed for {len(errors)} contacts",
                    "errors": errors
                }, status=status.HTTP_400_BAD_REQUEST)

            contact_objects = [Contact(**data) for data in validated_contacts]
            created_contacts = bulk_create_with_history(
                contact_objects,
                Contact,
                default_user=request.user if request.user.is_authenticated else None
            )
            response_data = ContactSerializer(created_contacts, many=True).data

            return Response({
                "status": "success",
                "message": f"Successfully created {len(created_contacts)} contacts",
                "results": response_data
            }, status=status.HTTP_201_CREATED)
        else:
            response = super().create(request, *args, **kwargs)
            response.data = {
                "status": "success",
                "message": "Contact created successfully",
                "result": response.data
            }
            response.status_code = status.HTTP_201_CREATED
            return response

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        response = super().partial_update(request, *args, **kwargs)
        return Response({
            "status": "success",
            "message": "Contact updated successfully",
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
            "message": "Contact deleted successfully"
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
            "message": "Contact recovered successfully"
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
            "message": "Order hard deleted successfully"
        }, status=status.HTTP_200_OK)


