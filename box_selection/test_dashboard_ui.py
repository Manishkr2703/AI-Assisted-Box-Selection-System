from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Box, BoxRecommendation, Order, OrderItem, Product


class OrdersWorkspaceTests(TestCase):
    def setUp(self):
        staff = get_user_model().objects.create_user(
            username="workspace_staff",
            password="test-password-123",
            is_staff=True,
        )
        self.client.force_login(staff)
        self.product = Product.objects.create(
            name="Sample product",
            sku="WORKSPACE-001",
            category="Sample",
            price=Decimal("100.00"),
            length_cm=Decimal("10"),
            width_cm=Decimal("10"),
            height_cm=Decimal("10"),
            weight_kg=Decimal("1.250"),
        )
        self.box = Box.objects.create(
            name="Medium",
            inner_length_cm=Decimal("20"),
            inner_width_cm=Decimal("20"),
            inner_height_cm=Decimal("20"),
            max_weight_kg=Decimal("5"),
            cost=Decimal("35.00"),
        )

    def test_orders_workspace_shows_database_backed_summary_metrics(self):
        draft = Order.objects.create(status=Order.Status.DRAFT)
        OrderItem.objects.create(
            order=draft,
            product=self.product,
            quantity=1,
        )
        placed = Order.objects.create(status=Order.Status.PLACED)
        OrderItem.objects.create(
            order=placed,
            product=self.product,
            quantity=2,
        )
        BoxRecommendation.objects.create(
            order=placed,
            box=self.box,
            score=Decimal("67.50"),
            algorithm_version="test",
        )

        response = self.client.get(reverse("box_selection:order-list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Orders Workspace")
        self.assertContains(response, "Total Pending Orders")
        self.assertContains(response, "2.500")
        self.assertContains(response, "67.50")
        self.assertContains(response, "Connected to Local Host")
        self.assertContains(response, "Dashboard Overview")
        self.assertContains(response, "Warehouse Analytics")

    def test_order_table_shows_short_id_copy_action_and_packaging_badge(self):
        order = Order.objects.create()
        OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=3,
        )
        BoxRecommendation.objects.create(
            order=order,
            box=self.box,
            selected_box={"name": "Medium"},
            score=Decimal("67.50"),
            algorithm_version="test",
        )

        response = self.client.get(reverse("box_selection:order-list"))

        self.assertContains(
            response,
            f'>#{str(order.number)[:8]}</a>',
        )
        self.assertContains(response, f'data-copy="{order.number}"')
        self.assertContains(response, "3</span><span class=\"items-caption\">items")
        self.assertContains(response, "package-medium")
        self.assertContains(response, "Medium")

    def test_workspace_controls_are_present(self):
        response = self.client.get(reverse("box_selection:order-list"))

        self.assertContains(response, 'id="workspaceSearch"')
        self.assertContains(response, "⌘ K")
        self.assertContains(response, 'id="themeToggle"')
        self.assertContains(response, "Create New Order")
        self.assertContains(response, "aria-label=\"Notifications\"")

    def test_warehouse_analytics_navigation_displays_live_metrics(self):
        draft = Order.objects.create(status=Order.Status.DRAFT)
        OrderItem.objects.create(
            order=draft,
            product=self.product,
            quantity=1,
        )
        placed = Order.objects.create(status=Order.Status.PLACED)
        OrderItem.objects.create(
            order=placed,
            product=self.product,
            quantity=2,
        )
        BoxRecommendation.objects.create(
            order=placed,
            box=self.box,
            score=Decimal("67.50"),
            algorithm_version="test",
        )

        response = self.client.get(reverse("box_selection:warehouse-analytics"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Warehouse Analytics")
        self.assertContains(response, "Average Placed Order Weight")
        self.assertContains(response, "2.500")
        self.assertContains(response, "67.50")
        analytics_url = reverse("box_selection:warehouse-analytics")
        self.assertContains(
            response,
            f'class="sidebar-link active" href="{analytics_url}"',
        )
