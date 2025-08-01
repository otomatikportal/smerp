from django.urls import path, include
from rest_framework.routers import DefaultRouter
from inventory.views.inventory_location_views import InventoryLocationViewSet
from inventory.views.dropdown_views import InventoryLocationDropdownView


router = DefaultRouter()
router.register(r'inventory-locations', InventoryLocationViewSet, basename='inventory-location')


urlpatterns = [
    path('inventory-locations/dropdown/', InventoryLocationDropdownView.as_view()),
    path('', include(router.urls)),
    
]