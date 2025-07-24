from django.urls import path, include
from rest_framework.routers import DefaultRouter
from inventory.views.inventory_location_views import InventoryLocationViewSet
from inventory.views.stock_record_views import StockRecordViewSet
from inventory.views.inventory_interaction_views import InventoryIncomingViewset


router = DefaultRouter()
router.register(r'inventory-locations', InventoryLocationViewSet, basename='inventory-location')
router.register(r'stock-records', StockRecordViewSet, basename='stock-record')
router.register(r'inventory-incoming', InventoryIncomingViewset, basename='inventory-incoming')

urlpatterns = [
    path('', include(router.urls)),
]