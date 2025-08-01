from rest_framework.generics import ListAPIView
from core.models import Company
from core.models.material import Material
from rest_framework.permissions import AllowAny
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import SearchFilter
from core.serializers import MaterialDropdownSerializer, CompanyDropdownSerializer


class DropdownPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 50

class MaterialDropdownView(ListAPIView):
    queryset = Material.objects.all()
    serializer_class = MaterialDropdownSerializer
    permission_classes = [AllowAny]
    pagination_class = DropdownPagination
    filter_backends = [SearchFilter]
    search_fields = ['name', 'internal_code']
    

class CompanyDropdownView(ListAPIView):
    queryset = Company.objects.all()
    serializer_class = CompanyDropdownSerializer
    permission_classes = [AllowAny]
    pagination_class = DropdownPagination
    filter_backends = [SearchFilter]
    search_fields = ['name']
    
