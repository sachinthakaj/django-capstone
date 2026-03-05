from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProviderViewSet, ServiceViewSet


router = DefaultRouter()
router.register(r"providers", ProviderViewSet, basename="provider")
router.register(r"services", ServiceViewSet, basename="service")


urlpatterns = [
    path("", include(router.urls)),
]
