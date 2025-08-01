from django.db import transaction
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.generics import get_object_or_404
from django.utils.translation import gettext_lazy as _
from inventory.serializers import (
    EnterFromPOLineSerializer,
    ExitFromSOLineSerializer,
    AdjustmentSerializer,
    TransferSerializer,
)
from inventory.models.stock_movement import StockMovement
from procurement.models import ProcurementOrderLine
from sales.models import SalesOrderLine
from drf_yasg.utils import swagger_auto_schema

class EnterFromPOLineAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(request_body=EnterFromPOLineSerializer)
    @transaction.atomic
    def post(self, request, id):
        po_line = get_object_or_404(ProcurementOrderLine, pk=id)
        
        if po_line.po.status not in ['ordered', 'paid', 'billed']:
            raise ValidationError(_('Satın alma depoya aktarılabilir statüde değil'))
        
        data = request.data.copy()
        data['uom'] = po_line.uom
        data['created_by'] = request.user.pk
        serializer = EnterFromPOLineSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        StockMovement.enter_from_po_line(
            po_line=po_line,
            **serializer.validated_data  # type: ignore
        )
        return Response({
            "status": "success",
            "message": _("Stok girişi başarıyla kaydedildi. Kalan gelecek: %(qty)s") % {"qty": po_line.quantity_left},
        }, status=status.HTTP_201_CREATED)


class ExitFromSOLineAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(request_body=ExitFromSOLineSerializer)
    def post(self, request, id):
        so_line = get_object_or_404(SalesOrderLine, pk=id)
        
        if so_line.so.status not in ['approved', 'billed', 'paid']:
            raise ValidationError(_('Satış kalemi çıkmak için geçerli statüde değil'))
        
        data = request.data.copy()
        data['uom'] = so_line.uom
        data['created_by'] = request.user.pk
        serializer = ExitFromSOLineSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        StockMovement.exit_from_so_line(
            reason = "Satış çıkışı",
            so_line=so_line,
            **serializer.validated_data #type: ignore
        )
        return Response({
            "status": "success",
            "message": _("Stok çıkışı başarıyla kaydedildi. Kalan çıkacak: %(qty)s") % {"qty": so_line.quantity_left}
        }, status=status.HTTP_201_CREATED)


class AdjustmentAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(request_body=AdjustmentSerializer)
    def post(self, request):
        data = request.data.copy()
        data['created_by'] = request.user.pk
        serializer = AdjustmentSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        print(serializer.validated_data)
        StockMovement.adjustment(
            **serializer.validated_data #type: ignore
        )
        return Response({
            "status": "success",
            "message": _("Stok düzeltme işlemi başarıyla kaydedildi.")
        }, status=status.HTTP_201_CREATED)


class TransferAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(request_body=TransferSerializer)
    def post(self, request):
        data = request.data.copy()
        data['created_by'] = request.user.pk
        serializer = TransferSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        StockMovement.transfer(
            **serializer.validated_data #type: ignore
        )
        return Response({
            "status": "success",
            "message": _("Stok transferi başarıyla kaydedildi."),
        }, status=status.HTTP_201_CREATED)
