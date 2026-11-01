from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from django.db.models import (
    Avg,
    Count,
    DecimalField,
    ExpressionWrapper,
    F,
    Q,
    Sum,
)
from django.db.models import ProtectedError
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
    View,
)

from .forms import BoxForm, OrderItemFormSet, ProductForm
from .models import Box, BoxRecommendation, Order, Product
from .services import create_order, place_order, recommend_box_for_order


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    login_url = "admin:login"

    def test_func(self):
        return self.request.user.is_staff


class ManagementSuccessMessageMixin:
    success_message = ""

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, self.success_message)
        return response


class ProtectedDeleteMixin:
    protected_message = ""

    def form_valid(self, form):
        try:
            with transaction.atomic():
                self.object.delete()
        except ProtectedError:
            messages.error(self.request, self.protected_message)
            return self.get_success_url_response()

        messages.success(self.request, self.success_message)
        return self.get_success_url_response()

    def get_success_url_response(self):
        return redirect(self.get_success_url())


class ProductListView(StaffRequiredMixin, ListView):
    model = Product
    template_name = "box_selection/product_list.html"
    context_object_name = "products"


class ProductDetailView(StaffRequiredMixin, DetailView):
    model = Product
    template_name = "box_selection/product_detail.html"
    context_object_name = "product"


class ProductCreateView(
    StaffRequiredMixin,
    ManagementSuccessMessageMixin,
    CreateView,
):
    model = Product
    form_class = ProductForm
    template_name = "box_selection/object_form.html"
    success_url = reverse_lazy("box_selection:product-list")
    success_message = "Product added successfully."
    extra_context = {
        "page_title": "Add product",
        "cancel_url": "box_selection:product-list",
    }


class ProductUpdateView(
    StaffRequiredMixin,
    ManagementSuccessMessageMixin,
    UpdateView,
):
    model = Product
    form_class = ProductForm
    template_name = "box_selection/object_form.html"
    success_url = reverse_lazy("box_selection:product-list")
    success_message = "Product updated successfully."
    extra_context = {
        "page_title": "Update product",
        "cancel_url": "box_selection:product-list",
    }


class ProductDeleteView(
    StaffRequiredMixin,
    ProtectedDeleteMixin,
    DeleteView,
):
    model = Product
    template_name = "box_selection/object_confirm_delete.html"
    success_url = reverse_lazy("box_selection:product-list")
    success_message = "Product deleted successfully."
    protected_message = (
        "This product is used by an order and cannot be deleted."
    )


class BoxListView(StaffRequiredMixin, ListView):
    model = Box
    template_name = "box_selection/box_list.html"
    context_object_name = "boxes"


class BoxDetailView(StaffRequiredMixin, DetailView):
    model = Box
    template_name = "box_selection/box_detail.html"
    context_object_name = "box"


class BoxCreateView(
    StaffRequiredMixin,
    ManagementSuccessMessageMixin,
    CreateView,
):
    model = Box
    form_class = BoxForm
    template_name = "box_selection/object_form.html"
    success_url = reverse_lazy("box_selection:box-list")
    success_message = "Shipping box added successfully."
    extra_context = {
        "page_title": "Add shipping box",
        "cancel_url": "box_selection:box-list",
    }


class BoxUpdateView(
    StaffRequiredMixin,
    ManagementSuccessMessageMixin,
    UpdateView,
):
    model = Box
    form_class = BoxForm
    template_name = "box_selection/object_form.html"
    success_url = reverse_lazy("box_selection:box-list")
    success_message = "Shipping box updated successfully."
    extra_context = {
        "page_title": "Update shipping box",
        "cancel_url": "box_selection:box-list",
    }


class BoxDeleteView(
    StaffRequiredMixin,
    ProtectedDeleteMixin,
    DeleteView,
):
    model = Box
    template_name = "box_selection/object_confirm_delete.html"
    success_url = reverse_lazy("box_selection:box-list")
    success_message = "Shipping box deleted successfully."
    protected_message = (
        "This box is used by a saved recommendation and cannot be deleted."
    )


class OrderListView(StaffRequiredMixin, ListView):
    model = Order
    template_name = "box_selection/order_list.html"
    context_object_name = "orders"
    queryset = (
        Order.objects.prefetch_related("items")
        .select_related("box_recommendation", "box_recommendation__box")
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        orders = list(context["orders"])
        context["orders"] = orders

        pending_count = sum(
            order.status == Order.Status.DRAFT
            for order in orders
        )
        placed_orders = [
            order for order in orders
            if order.status == Order.Status.PLACED
        ]
        average_placed_weight = (
            sum(
                (order.total_item_weight for order in placed_orders),
                start=Decimal("0.000"),
            )
            / len(placed_orders)
            if placed_orders
            else None
        )
        average_utilization = BoxRecommendation.objects.filter(
            box__isnull=False,
            score__isnull=False,
        ).aggregate(value=Avg("score"))["value"]

        context["metrics"] = {
            "pending_orders": pending_count,
            "average_placed_weight": (
                average_placed_weight.quantize(Decimal("0.001"))
                if average_placed_weight is not None
                else None
            ),
            "average_box_utilization": (
                average_utilization.quantize(Decimal("0.01"))
                if average_utilization is not None
                else None
            ),
        }
        return context


class WarehouseAnalyticsView(StaffRequiredMixin, TemplateView):
    template_name = "box_selection/warehouse_analytics.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        weight_expression = ExpressionWrapper(
            F("items__weight_kg") * F("items__quantity"),
            output_field=DecimalField(max_digits=18, decimal_places=3),
        )
        average_placed_weight = (
            Order.objects.filter(status=Order.Status.PLACED)
            .annotate(total_weight=Sum(weight_expression))
            .aggregate(value=Avg("total_weight"))["value"]
        )
        average_box_utilization = BoxRecommendation.objects.filter(
            box__isnull=False,
            score__isnull=False,
        ).aggregate(value=Avg("score"))["value"]
        order_counts = Order.objects.aggregate(
            total=Count("pk"),
            pending=Count("pk", filter=Q(status=Order.Status.DRAFT)),
            placed=Count("pk", filter=Q(status=Order.Status.PLACED)),
        )
        context["analytics"] = {
            **order_counts,
            "average_placed_weight": (
                average_placed_weight.quantize(Decimal("0.001"))
                if average_placed_weight is not None
                else None
            ),
            "average_box_utilization": (
                average_box_utilization.quantize(Decimal("0.01"))
                if average_box_utilization is not None
                else None
            ),
            "product_count": Product.objects.count(),
            "box_count": Box.objects.count(),
        }
        return context


class OrderDetailView(StaffRequiredMixin, DetailView):
    model = Order
    template_name = "box_selection/order_detail.html"
    context_object_name = "order"
    queryset = (
        Order.objects.prefetch_related("items")
        .select_related("box_recommendation", "box_recommendation__box")
    )


class OrderDeleteView(StaffRequiredMixin, DeleteView):
    model = Order
    template_name = "box_selection/order_confirm_delete.html"
    success_url = reverse_lazy("box_selection:order-list")

    def form_valid(self, form):
        order_number = self.object.number
        response = super().form_valid(form)
        messages.success(
            self.request,
            f"Order {order_number} and its history were deleted. "
            "Products and shipping boxes were kept.",
        )
        return response


class OrderRecommendationView(StaffRequiredMixin, DetailView):
    model = Order

    def post(self, request, *args, **kwargs):
        order = self.get_object()
        try:
            recommendation = recommend_box_for_order(order)
        except ValueError as error:
            messages.error(request, str(error))
        else:
            if recommendation.box_id is None:
                messages.warning(
                    request,
                    "No suitable box was found for this order.",
                )
            else:
                messages.success(request, "Box recommendation updated.")
        return redirect("box_selection:order-detail", pk=order.pk)


class OrderPlacementView(StaffRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        order = get_object_or_404(Order, pk=kwargs["pk"])
        try:
            place_order(order)
        except ValueError as error:
            messages.error(request, str(error))
        else:
            messages.success(request, "Order placed successfully.")
        return redirect("box_selection:order-detail", pk=order.pk)


class OrderCreateView(StaffRequiredMixin, TemplateView):
    template_name = "box_selection/order_form.html"

    def get_formset(self, data=None):
        return OrderItemFormSet(
            data=data,
            instance=Order(),
            prefix="items",
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault("formset", self.get_formset())
        context["has_products"] = Product.objects.exists()
        return context

    def post(self, request, *args, **kwargs):
        formset = self.get_formset(request.POST)
        if formset.is_valid():
            lines = [
                (form.cleaned_data["product"], form.cleaned_data["quantity"])
                for form in formset.forms
                if form.cleaned_data and form.cleaned_data.get("product")
            ]
            try:
                order = create_order(lines)
            except ValueError as error:
                messages.error(request, str(error))
            else:
                messages.success(request, "Order created successfully.")
                return redirect("box_selection:order-detail", pk=order.pk)

        return self.render_to_response(
            self.get_context_data(formset=formset)
        )
