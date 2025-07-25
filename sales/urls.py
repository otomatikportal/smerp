from rest_framework.routers import DefaultRouter
from sales.views.variable_cost_views import VariableCostViewSet 
from django.urls import path, include

router = DefaultRouter()
router.register(r'variable-costs', VariableCostViewSet, basename='variable-cost')


urlpatterns = [
    path('', include(router.urls)),
]
