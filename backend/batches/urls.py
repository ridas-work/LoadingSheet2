from django.urls import path

from .views import BatchDetailView, BatchListCreateView, BatchProductListView

urlpatterns = [
    path("batch-products/", BatchProductListView.as_view(), name="batch-product-list"),
    path("batches/", BatchListCreateView.as_view(), name="batch-list-create"),
    path("batches/<int:pk>/", BatchDetailView.as_view(), name="batch-detail"),
]
