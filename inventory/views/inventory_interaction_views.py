from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response




class InventoryActionAPI(APIView):
    
    
    @action(detail=True, methods=['get'], url_path='incoming')
    def get(self, request, pk=None):
        return Response({})