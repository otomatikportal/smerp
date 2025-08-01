from django.urls import path, include
from rest_framework.routers import DefaultRouter
from core.views.material_views import MaterialViewSet
from core.views.company_views import CompanyViewSet
from core.views.contact_views import ContactViewSet
from core.views.dropdown_views import CompanyDropdownView, MaterialDropdownView

router = DefaultRouter()
router.register(r'materials', MaterialViewSet, basename='material')
router.register(r'companies', CompanyViewSet, basename='company')
router.register(r'contacts', ContactViewSet, basename='contact')

urlpatterns = [
    path("companies/dropdown/", CompanyDropdownView.as_view()),
    path("materials/dropdown/", MaterialDropdownView.as_view()),
    path('', include(router.urls)),
]
