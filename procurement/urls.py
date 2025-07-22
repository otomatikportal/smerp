from rest_framework.routers import DefaultRouter
from procurement.views.material_demand_views import MaterialDemandViewSet
from procurement.views.procurement_order_line_views import ProcurementOrderLineViewSet
from procurement.views.procurement_order_views import ProcurementOrderViewSet
from django.urls import path, include

router = DefaultRouter()
router.register(r'material-demands', MaterialDemandViewSet, basename='material-demand')
router.register(r'procurement-order-lines', ProcurementOrderLineViewSet, basename='procurement-order-line')
router.register(r'procurement-orders', ProcurementOrderViewSet, basename='procurement-order')

urlpatterns = [
    path('', include(router.urls)),
]
