from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import PackagingMaterialViewSet

router = DefaultRouter()
router.register(
    "packaging-materials",
    PackagingMaterialViewSet,
    basename="packaging-material",
)

urlpatterns = [
    path("", include(router.urls)),
]
