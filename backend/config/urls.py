from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/", include("catalog.urls")),
    path("api/orders/", include("orders.urls")),
    path("api/market-visits/", include("market_visits.urls")),
    path("api/", include("batches.urls")),
    path("api/", include("packaging.urls")),
    path("api/", include("dispatch.urls")),
    path("api/", include("loading.urls")),
]
