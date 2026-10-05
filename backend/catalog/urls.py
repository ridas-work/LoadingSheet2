from django.urls import path

from .views import CustomerListView, OuterBoxListView, ProductListView

urlpatterns = [
    path("customers/", CustomerListView.as_view(), name="customer-list"),
    path("products/", ProductListView.as_view(), name="product-list"),
    path("outer-boxes/", OuterBoxListView.as_view(), name="outer-box-list"),
]
