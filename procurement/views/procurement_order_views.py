from django.http import JsonResponse
from rest_framework import viewsets, status, filters, pagination
from django.db import transaction
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from procurement.models import ProcurementOrder
from procurement.serializers.procurement_order_serializers import ProcurementOrderSerializer
from rest_framework.views import exception_handler
from rest_framework.permissions import DjangoModelPermissions
from rest_framework.decorators import action
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

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
            "message": "Orders retrieved successfully",
            "count": self.page.paginator.count,
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
            "results": data
        })

class ProcurementOrderViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'head', 'options', 'delete']
    queryset = ProcurementOrder.objects.all().order_by('-id')
    serializer_class = ProcurementOrderSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['vendor', 'status', 'po_number', 'currency']
    search_fields = ['po_number', 'description', 'vendor__name']
    ordering_fields = ['id', 'po_number', 'vendor', 'status']
    pagination_class = CustomPagination
    permission_classes = [CustomDjangoModelPermissions]

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        if isinstance(response.data, dict) and "results" in response.data:
            response.data["status"] = "success"
            response.data["message"] = "Orders retrieved successfully"
            return response

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, context={'action': 'retrieve'})
        return Response({
            "status": "success",
            "message": "Order retrieved successfully",
            "result": serializer.data
        }, status=status.HTTP_200_OK)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return Response({
            "status": "success",
            "message": "Order created successfully",
            "result": response.data
        }, status=status.HTTP_201_CREATED)

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            "status": "success",
            "message": "Order updated successfully",
            "result": serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='delete', permission_classes=[DjangoModelPermissions])
    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        try:
            instance = ProcurementOrder.objects.all_with_deleted().get(pk=kwargs['pk']) #type: ignore
        except ProcurementOrder.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Order not found"
            }, status=status.HTTP_404_NOT_FOUND)
        
        instance.delete()
        return Response({
            "status": "success",
            "message": "Order soft deleted successfully"
        }, status=status.HTTP_200_OK)
        
    @action(detail=True, methods=['post'], url_path='recover')
    @transaction.atomic
    def recover(self, request, *args, **kwargs):
        try:
            instance = ProcurementOrder.objects.all_with_deleted().get(pk=kwargs['pk']) #type: ignore
        except ProcurementOrder.DoesNotExist:
            return Response({
                "status": "error",
                "message": "Order not found"
            }, status=status.HTTP_404_NOT_FOUND)
        
        if instance.deleted is not None:
            instance.undelete()
            serializer = self.get_serializer(instance)
            return Response({
                "status": "success",
                "message": "Order recovered successfully",
                "result": serializer.data
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "status": "error",
                "message": "Order is not deleted"
            }, status=status.HTTP_400_BAD_REQUEST)

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        from safedelete.config import HARD_DELETE
        instance.delete(force_policy=HARD_DELETE)
        return Response({
            "status": "success",
            "message": "Order hard deleted successfully"
        }, status=status.HTTP_200_OK)
        
    @action(detail=True, methods=['patch'], url_path='set-status')
    @transaction.atomic
    def change_status(self, request, *args, **kwargs):
        instance = self.get_object()
        new_status = request.data.get('status')
        
        if not new_status:
            return Response({
                "status": "error",
                "message": _("Durum alanı gereklidir")
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check permissions based on status
        permission_map = {
            'submitted': 'submit_procurementorder',
            'approved': 'approve_procurementorder',
            'rejected': 'approve_procurementorder',
            'ordered': 'order_procurementorder',
            'billed': 'bill_procurementorder',
            'paid': 'bill_procurementorder',
            'cancelled': 'cancel_procurementorder',
        }
        
        required_permission = permission_map.get(new_status)
        if required_permission and not request.user.has_perm(f'procurement.{required_permission}'):
            return Response({
                "status": "error",
                "message": _("Bu durum değişikliği için yetkiniz bulunmamaktadır.")
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            # Use model method for status change
            kwargs_for_status = {}
            if new_status == 'billed' and 'invoice_date' in request.data:
                kwargs_for_status['invoice_date'] = request.data['invoice_date']
            
            instance.change_status(new_status, user=request.user, **kwargs_for_status)
            
            serializer = self.get_serializer(instance)
            return Response({
                "status": "success",
                "message": _("Sipariş durumu %(status)s olarak başarıyla değiştirildi") % {'status': new_status},
                "result": serializer.data
            }, status=status.HTTP_200_OK)
            
        except ValidationError as e:
            return Response({
                "status": "error",
                "message": _("Doğrulama başarısız"),
                "errors": e.message_dict if hasattr(e, 'message_dict') else str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'], url_path='allowed-transitions')
    def allowed_transitions(self, request, *args, **kwargs):
        instance = self.get_object()
        transitions = instance.get_allowed_transitions(user=request.user)
        return Response({
            "status": "success",
            "current_status": instance.status,
            "allowed_transitions": transitions
        })