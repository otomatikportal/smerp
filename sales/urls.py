from rest_framework.routers import DefaultRouter
from sales.views.variable_cost_views import VariableCostViewSet 
from sales.views.sales_order_views import SalesOrderViewSet
from django.urls import path, include

router = DefaultRouter()
router.register(r'variable-costs', VariableCostViewSet, basename='variable-cost')
router.register(r'sales-orders', SalesOrderViewSet, basename='sales-order')


urlpatterns = [
    path('', include(router.urls)),
]
