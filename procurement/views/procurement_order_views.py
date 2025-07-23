from rest_framework import viewsets, status, filters, pagination
from django.db import transaction
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from procurement.models import ProcurementOrder
from procurement.serializers.procurement_order_serializers import ProcurementOrderSerializer
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
        import traceback
        try:
            response = super().list(request, *args, **kwargs)
            if isinstance(response.data, dict) and "results" in response.data:
                response.data["status"] = "success"
                response.data["message"] = "Orders retrieved successfully"
                return response
            return Response({
                "status": "success",
                "message": "Orders retrieved successfully",
                "results": response.data
            }, status=status.HTTP_200_OK)
        except Exception as exc:
            print("Exception in ProcurementOrderViewSet.list:", exc)
            traceback.print_exc()
            return self.handle_exception(exc)

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, context={'action': 'retrieve'})
            return Response({
                "status": "success",
                "message": "Order retrieved successfully",
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
                "message": "Order created successfully",
                "result": response.data
            }, status=status.HTTP_201_CREATED)
        except Exception as exc:
            return self.handle_exception(exc)

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({
                "status": "success",
                "message": "Order updated successfully",
                "result": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as exc:
            return self.handle_exception(exc)

    @action(detail=True, methods=['post'], url_path='delete', permission_classes=[DjangoModelPermissions])
    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            instance.delete()
            return Response({
                "status": "success",
                "message": "Order soft deleted successfully"
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
            "message": "Order recovered successfully"
        }, status=status.HTTP_200_OK)

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            from safedelete.config import HARD_DELETE
            instance.delete(force_policy=HARD_DELETE)
            return Response({
                "status": "success",
                "message": "Order hard deleted successfully"
            }, status=status.HTTP_200_OK)
        except Exception as exc:
            return self.handle_exception(exc)
        
    @action(detail=True, methods=['patch'], url_path='set-status-draft', permission_classes=[DjangoModelPermissions])
    @transaction.atomic
    def set_status_draft(self, request, *args, **kwargs):
        return self._set_status_action(request, 'set_status_draft', 'submit_procurementorder', 'Order drafted successfully')

    @action(detail=True, methods=['patch'], url_path='set-status-submitted', permission_classes=[DjangoModelPermissions])
    @transaction.atomic
    def set_status_submitted(self, request, *args, **kwargs):
        return self._set_status_action(request, 'set_status_submitted', 'submit_procurementorder', 'Order submitted successfully')

    @action(detail=True, methods=['patch'], url_path='set-status-approved', permission_classes=[DjangoModelPermissions])
    @transaction.atomic
    def set_status_approved(self, request, *args, **kwargs):
        return self._set_status_action(request, 'set_status_approved', 'approve_procurementorder', 'Order approved successfully')

    @action(detail=True, methods=['patch'], url_path='set-status-rejected', permission_classes=[DjangoModelPermissions])
    @transaction.atomic
    def set_status_rejected(self, request, *args, **kwargs):
        return self._set_status_action(request, 'set_status_rejected', 'reject_procurementorder', 'Order rejected successfully')

    @action(detail=True, methods=['patch'], url_path='set-status-ordered', permission_classes=[DjangoModelPermissions])
    @transaction.atomic
    def set_status_ordered(self, request, *args, **kwargs):
        return self._set_status_action(request, 'set_status_ordered', 'submit_procurementorder', 'Order set to ordered successfully')

    @action(detail=True, methods=['patch'], url_path='set-status-billed', permission_classes=[DjangoModelPermissions])
    @transaction.atomic
    def set_status_billed(self, request, *args, **kwargs):
        return self._set_status_action(request, 'set_status_billed', 'bill_procurementorder', 'Order billed successfully')

    @action(detail=True, methods=['patch'], url_path='set-status-paid', permission_classes=[DjangoModelPermissions])
    @transaction.atomic
    def set_status_paid(self, request, *args, **kwargs):
        return self._set_status_action(request, 'set_status_paid', 'bill_procurementorder', 'Order paid successfully')

    @action(detail=True, methods=['patch'], url_path='set-status-cancelled', permission_classes=[DjangoModelPermissions])
    @transaction.atomic
    def set_status_cancelled(self, request, *args, **kwargs):
        return self._set_status_action(request, 'set_status_cancelled', 'cancel_procurementorder', 'Order cancelled successfully')

    @transaction.atomic
    def _set_status_action(self, request, action_flag, permission_codename, success_message):
        try:
            instance = self.get_object()
            self.check_object_permissions(request, instance)
            if not request.user.has_perm(f'procurement.{permission_codename}'):
                return Response({
                    "status": "error",
                    "message": "Permission denied for this status change."
                }, status=status.HTTP_403_FORBIDDEN)
            serializer = self.get_serializer(instance, data=request.data, partial=True, context={'action': action_flag})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({
                "status": "success",
                "message": success_message,
                "result": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as exc:
            return self.handle_exception(exc)

    def update(self, request, *args, **kwargs):
        return Response({
            "status": "error",
            "message": "PUT method is not allowed for this resource. Use PATCH instead."
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
