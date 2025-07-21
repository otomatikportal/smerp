from rest_framework.routers import DefaultRouter
from procurement.views.material_demand_views import MaterialDemandViewSet
from django.urls import path, include

router = DefaultRouter()
router.register(r'material-demands', MaterialDemandViewSet, basename='material-demand')

urlpatterns = [
    path('', include(router.urls)),
]
