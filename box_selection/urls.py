from django.urls import path

from . import views

app_name = "box_selection"

urlpatterns = [
    path("products/", views.ProductListView.as_view(), name="product-list"),
    path("products/add/", views.ProductCreateView.as_view(), name="product-add"),
    path(
        "products/<int:pk>/",
        views.ProductDetailView.as_view(),
        name="product-detail",
    ),
    path(
        "products/<int:pk>/edit/",
        views.ProductUpdateView.as_view(),
        name="product-edit",
    ),
    path(
        "products/<int:pk>/delete/",
        views.ProductDeleteView.as_view(),
        name="product-delete",
    ),
    path("boxes/", views.BoxListView.as_view(), name="box-list"),
    path("boxes/add/", views.BoxCreateView.as_view(), name="box-add"),
    path("boxes/<int:pk>/", views.BoxDetailView.as_view(), name="box-detail"),
    path("boxes/<int:pk>/edit/", views.BoxUpdateView.as_view(), name="box-edit"),
    path(
        "boxes/<int:pk>/delete/",
        views.BoxDeleteView.as_view(),
        name="box-delete",
    ),
    path("orders/", views.OrderListView.as_view(), name="order-list"),
    path(
        "analytics/",
        views.WarehouseAnalyticsView.as_view(),
        name="warehouse-analytics",
    ),
    path("orders/add/", views.OrderCreateView.as_view(), name="order-add"),
    path(
        "orders/<int:pk>/",
        views.OrderDetailView.as_view(),
        name="order-detail",
    ),
    path(
        "orders/<int:pk>/delete/",
        views.OrderDeleteView.as_view(),
        name="order-delete",
    ),
    path(
        "orders/<int:pk>/recommend/",
        views.OrderRecommendationView.as_view(),
        name="order-recommend",
    ),
    path(
        "orders/<int:pk>/place/",
        views.OrderPlacementView.as_view(),
        name="order-place",
    ),
]
