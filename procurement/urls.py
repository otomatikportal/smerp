from rest_framework.routers import DefaultRouter
from procurement.views.material_demand_views import MaterialDemandViewSet
from procurement.views.procurement_order_line_views import ProcurementOrderLineViewSet
from django.urls import path, include

router = DefaultRouter()
router.register(r'material-demands', MaterialDemandViewSet, basename='material-demand')
router.register(r'procurement-order-lines', ProcurementOrderLineViewSet, basename='procurement-order-lne')

urlpatterns = [
    path('', include(router.urls)),
]
