from django.urls import path, include
from rest_framework.routers import DefaultRouter
from bom.views.bom_line_views import BomLineViewSet
from bom.views.bom_views import BomViewSet

router = DefaultRouter()
router.register(r'boms', BomViewSet, basename='bom')
router.register(r'bom-lines', BomLineViewSet, basename='bom-line')


urlpatterns = [
    path('', include(router.urls)),
]