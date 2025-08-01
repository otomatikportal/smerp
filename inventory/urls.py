from django.urls import path, include
from rest_framework.routers import DefaultRouter
from inventory.views.inventory_location_views import InventoryLocationViewSet
from inventory.views.dropdown_views import InventoryLocationDropdownView
from inventory.views.inventory_action_views import (
    EnterFromPOLineAPIView,
    ExitFromSOLineAPIView,
    AdjustmentAPIView,
    TransferAPIView,
)
from inventory.views.inventory_get_views import (
    InventoryBalanceListAPIView,
    InventoryBalanceDetailAPIView
)


router = DefaultRouter()
router.register(r'inventory-locations', InventoryLocationViewSet, basename='inventory-location')


urlpatterns = [
    path('action/<int:id>/exit-from-so-line/', ExitFromSOLineAPIView.as_view(), name='exit-from-so-line'),
    path('action/<int:id>/enter-from-po-line/', EnterFromPOLineAPIView.as_view(), name='enter-from-po-line'),
    path('action/adjustment/', AdjustmentAPIView.as_view(), name='adjustment'),
    path('action/transfer/', TransferAPIView.as_view(), name='transfer'),
    path('inventory-locations/dropdown/', InventoryLocationDropdownView.as_view()),
    path('inventory-balances/', InventoryBalanceListAPIView.as_view(), name='inventory-balance-list'),
    path('inventory-balances/<int:pk>/', InventoryBalanceDetailAPIView.as_view(), name='inventory-balance-detail'),
    path('', include(router.urls)),
]