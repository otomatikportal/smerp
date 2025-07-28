from rest_framework import viewsets, status, filters, pagination
from django.db import transaction
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.views import exception_handler
from rest_framework.permissions import DjangoModelPermissions
from rest_framework.decorators import action
from bom.models import BomLine
from bom.serializers.bom_line_serializers import BomLineSerializer
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
            "message": "BOM lines retrieved successfully",
            "count": self.page.paginator.count,
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
            "results": data
        })

class BomLineViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete']
    queryset = BomLine.objects.all().order_by('-id')
    serializer_class = BomLineSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['bom', 'component', 'uom']
    search_fields = ['component__name', 'component__description', 'component__internal_code']
    ordering_fields = ['id', 'component', 'quantity', 'uom']
    pagination_class = CustomPagination
    permission_classes = [CustomDjangoModelPermissions]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action in ['recover', 'delete']:
            return BomLine.objects.all_with_deleted()
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True, context={**self.get_serializer_context(), 'action': 'list'})
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True, context={**self.get_serializer_context(), 'action': 'list'})
        return Response({
            "status": "success",
            "message": "BOM lines retrieved successfully",
            "results": serializer.data
        }, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, context={**self.get_serializer_context(), 'action': 'retrieve'})
        return Response({
            "status": "success",
            "message": "BOM line retrieved successfully",
            "result": serializer.data
        }, status=status.HTTP_200_OK)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            "status": "success",
            "message": "BOM line created successfully",
            "result": serializer.data
        }, status=status.HTTP_201_CREATED)

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            "status": "success",
            "message": "BOM line updated successfully",
            "result": serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='delete')
    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({
            "status": "success",
            "message": "BOM line deleted successfully"
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
            "message": "BOM line recovered successfully",
            "result": serializer.data
        }, status=status.HTTP_200_OK)

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if hasattr(instance, 'delete'):
            instance.delete(force_policy=HARD_DELETE)
        else:
            instance.delete()
        return Response({
            "status": "success",
            "message": "BOM line hard deleted successfully"
        }, status=status.HTTP_200_OK)
