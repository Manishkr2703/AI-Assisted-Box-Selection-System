from django.contrib import admin

from .models import Box, BoxRecommendation, Order, OrderItem, Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "sku",
        "category",
        "price",
        "length_cm",
        "width_cm",
        "height_cm",
        "weight_kg",
        "allow_rotation",
    )
    search_fields = ("name", "sku")


@admin.register(Box)
class BoxAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "inner_length_cm",
        "inner_width_cm",
        "inner_height_cm",
        "max_weight_kg",
        "tare_weight_kg",
        "cost",
    )


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = (
        "product",
        "product_name",
        "sku",
        "length_cm",
        "width_cm",
        "height_cm",
        "weight_kg",
        "allow_rotation",
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("number", "status", "created_at")
    list_filter = ("status", "created_at")
    readonly_fields = ("number", "created_at")
    inlines = [OrderItemInline]


@admin.register(BoxRecommendation)
class BoxRecommendationAdmin(admin.ModelAdmin):
    list_display = ("order", "box", "score", "algorithm_version", "created_at")
    readonly_fields = ("created_at",)
