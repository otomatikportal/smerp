from django.db import transaction
from django.utils.translation import gettext_lazy as _
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response
from inventory.models import StockRecord
from procurement.models import ProcurementOrderLine
from rest_framework.permissions import BasePermission
from inventory.serializers.inventory_interaction_serializers import IncomingItemsDetailSerializer, IncomingItemsListSerializer, SimpleInventoryTransactionSerializer
from django.shortcuts import get_object_or_404
from rest_framework import status, filters, pagination, serializers
from rest_framework.views import exception_handler
from inventory.serializers.stock_record_serializers import StockRecordSerializer


class HasStockRecordTransactPermission(BasePermission):
    def has_permission(self, request, view):
        return request.user.has_perm('stockrecord.transact_stockrecord')

class CustomPagination(pagination.PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            "status": "success",
            "message": _("Inventory action results retrieved successfully"),
            "count": self.page.paginator.count,
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
            "results": data
        })

class InventoryIncomingViewset(ViewSet):
    http_method_names = ['get', 'put']
    serializer_class = IncomingItemsListSerializer  # Default serializer
    
    def get_queryset(self):
        action = self.action
        base_queryset = ProcurementOrderLine.objects.select_related('material', 'po__vendor')
        if action == 'incoming':
            # For incoming list view
            return base_queryset.filter(
                po__status__in=["ordered", "billed", "paid"]
            )
        
        elif action == 'incoming_detail':
            # For incoming detail view
            return base_queryset.filter(
                po__status__in=["ordered", "billed", "paid"]
            )
        
        # Default fallback
        return base_queryset.none()
    
    def get_serializer_class(self):
        if self.action == 'incoming_detail':
            return IncomingItemsDetailSerializer
        return self.serializer_class
    
    @permission_classes([HasStockRecordTransactPermission])
    @action(detail=False, methods=['get'], url_path='incoming')
    def incoming(self, request):
        # Use get_queryset() and get_serializer_class() for consistency
        queryset = self.get_queryset()
        
        # Pagination
        paginator = CustomPagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        serializer = self.get_serializer_class()(paginated_queryset, many=True)
        
        return paginator.get_paginated_response(serializer.data)
    
    @permission_classes([HasStockRecordTransactPermission])
    @action(detail=True, methods=['get'], url_path='incoming-detail')
    def incoming_detail(self, request, pk=None):
        queryset = self.get_queryset()
        instance = get_object_or_404(queryset, pk=pk)
        serializer = self.get_serializer_class()(instance)
        
        return Response({
            "status": "success",
            "message": _("Item successfully retrieved"),
            "data": serializer.data
        })
        
    @transaction.atomic
    @permission_classes([HasStockRecordTransactPermission])
    @action(detail=False, methods=['put'], url_path='enter-inventory')
    def enter_ordered_material(self, request):
        
        serializer = SimpleInventoryTransactionSerializer(data=request.data)
        
        if serializer.is_valid():
            data = serializer.validated_data
            
            # Handle procurement order line update
            if 'source_id' in data:                        #type: ignore
                po_line = data['source_id']  #type: ignore
                po_line.quantity_received += data['quantity']  #type: ignore
                po_line.save()
            
            # Try to get existing stock record
            stock_record = None
            created = False
            
            try:
                stock_record = StockRecord.objects.get(
                    location=data['location'], #type: ignore
                    material=data['material'], #type: ignore
                    uom=data['uom'] #type: ignore
                )
                # If found, increment the quantity
                stock_record.quantity += data['quantity'] #type: ignore
                created = False
                
            except StockRecord.DoesNotExist:
                # If not found, create new stock record
                stock_record = StockRecord(
                    location=data['location'], #type: ignore
                    material=data['material'], #type: ignore
                    uom=data['uom'], #type: ignore
                    quantity=data['quantity'] #type: ignore
                )
                created = True
            
            # Handle change_reason for Django Simple History
            change_reason = data.get('change_reason') #type: ignore
            
            # Set change reason and save in one operation
            if change_reason:
                stock_record._change_reason = change_reason #type: ignore
                
            stock_record.save()
            
            # Return the stock record object using StockRecordSerializer
            stock_record_serializer = StockRecordSerializer(stock_record)
            return Response(stock_record_serializer.data, status=status.HTTP_200_OK)
        
        else:
            raise serializers.ValidationError(serializer.errors)
        
        
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