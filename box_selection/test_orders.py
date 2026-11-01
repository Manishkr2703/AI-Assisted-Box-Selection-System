from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Box, BoxRecommendation, Order, OrderItem, Product
from .services import create_order


class OrderManagementTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = get_user_model().objects.create_user(
            username="order_manager",
            password="test-password",
            is_staff=True,
        )
        cls.lamp = Product.objects.create(
            name="Desk lamp",
            sku="LAMP-001",
            length_cm=Decimal("12"),
            width_cm=Decimal("10"),
            height_cm=Decimal("30"),
            weight_kg=Decimal("1.250"),
        )
        cls.book = Product.objects.create(
            name="Book",
            sku="BOOK-001",
            length_cm=Decimal("20"),
            width_cm=Decimal("15"),
            height_cm=Decimal("2"),
            weight_kg=Decimal("0.500"),
        )

    def setUp(self):
        self.client.force_login(self.staff)

    def post_lines(self, lines):
        data = {
            "items-TOTAL_FORMS": str(len(lines)),
            "items-INITIAL_FORMS": "0",
            "items-MIN_NUM_FORMS": "1",
            "items-MAX_NUM_FORMS": "1000",
        }
        for index, (product_id, quantity) in enumerate(lines):
            data[f"items-{index}-product"] = str(product_id)
            data[f"items-{index}-quantity"] = str(quantity)
        return self.client.post(reverse("box_selection:order-add"), data)

    def test_create_order_with_multiple_products_and_display_total_weight(self):
        response = self.post_lines(
            [(self.lamp.pk, "2"), (self.book.pk, "3")]
        )

        order = Order.objects.get()
        self.assertRedirects(
            response,
            reverse("box_selection:order-detail", args=[order.pk]),
        )
        self.assertEqual(order.items.count(), 2)
        self.assertEqual(order.total_item_weight, Decimal("4.000"))
        self.assertTrue(hasattr(order, "box_recommendation"))

        detail = self.client.get(
            reverse("box_selection:order-detail", args=[order.pk])
        )
        self.assertContains(detail, "Desk lamp")
        self.assertContains(detail, "BOOK-001")
        self.assertContains(detail, "4.000 kg")
        self.assertContains(detail, "Recommended shipping box")

    def test_empty_order_is_rejected(self):
        response = self.client.post(
            reverse("box_selection:order-add"),
            {
                "items-TOTAL_FORMS": "0",
                "items-INITIAL_FORMS": "0",
                "items-MIN_NUM_FORMS": "1",
                "items-MAX_NUM_FORMS": "1000",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Order.objects.exists())
        self.assertContains(response, "Add at least one product to the order.")

    def test_zero_and_non_integer_quantities_are_rejected(self):
        for quantity in ("0", "1.5"):
            with self.subTest(quantity=quantity):
                response = self.post_lines([(self.lamp.pk, quantity)])
                self.assertEqual(response.status_code, 200)
                self.assertFalse(Order.objects.exists())

    def test_duplicate_products_are_rejected(self):
        response = self.post_lines(
            [(self.lamp.pk, "1"), (self.lamp.pk, "2")]
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Order.objects.exists())
        self.assertContains(response, "Choose each product only once per order.")

    def test_order_views_require_staff(self):
        self.client.logout()

        response = self.client.get(reverse("box_selection:order-list"))

        self.assertEqual(response.status_code, 302)


class OrderHistoryDeleteTests(TestCase):
    def setUp(self):
        self.staff = get_user_model().objects.create_user(
            username="history_manager",
            password="test-password-123",
            is_staff=True,
        )
        self.client.force_login(self.staff)
        self.product = Product.objects.create(
            name="Sample product",
            sku="HISTORY-001",
            category="Sample",
            price=Decimal("100.00"),
            length_cm=Decimal("10"),
            width_cm=Decimal("10"),
            height_cm=Decimal("10"),
            weight_kg=Decimal("1.000"),
        )
        self.box = Box.objects.create(
            name="History test box",
            inner_length_cm=Decimal("20"),
            inner_width_cm=Decimal("20"),
            inner_height_cm=Decimal("20"),
            max_weight_kg=Decimal("5"),
            cost=Decimal("10.00"),
        )
        self.order = Order.objects.create()
        OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=1,
        )
        BoxRecommendation.objects.create(
            order=self.order,
            box=self.box,
            algorithm_version="test",
        )

    def test_get_requires_confirmation_without_deleting_order(self):
        response = self.client.get(
            reverse("box_selection:order-delete", args=[self.order.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, str(self.order.number))
        self.assertTrue(Order.objects.filter(pk=self.order.pk).exists())

    def test_post_deletes_only_order_history_and_keeps_catalog(self):
        order_id = self.order.pk
        product_id = self.product.pk
        box_id = self.box.pk

        response = self.client.post(
            reverse("box_selection:order-delete", args=[order_id])
        )

        self.assertRedirects(response, reverse("box_selection:order-list"))
        self.assertFalse(Order.objects.filter(pk=order_id).exists())
        self.assertFalse(OrderItem.objects.filter(order_id=order_id).exists())
        self.assertFalse(
            BoxRecommendation.objects.filter(order_id=order_id).exists()
        )
        self.assertTrue(Product.objects.filter(pk=product_id).exists())
        self.assertTrue(Box.objects.filter(pk=box_id).exists())

    def test_order_history_delete_requires_staff(self):
        self.client.logout()

        response = self.client.get(
            reverse("box_selection:order-delete", args=[self.order.pk])
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Order.objects.filter(pk=self.order.pk).exists())


class OrderPlacementTests(TestCase):
    def setUp(self):
        staff = get_user_model().objects.create_user(
            username="placement_manager",
            password="test-password-123",
            is_staff=True,
        )
        self.client.force_login(staff)
        self.product = Product.objects.create(
            name="Placement sample",
            sku="PLACE-001",
            length_cm=Decimal("10"),
            width_cm=Decimal("10"),
            height_cm=Decimal("10"),
            weight_kg=Decimal("1.000"),
        )
        self.box = Box.objects.create(
            name="Placement box",
            inner_length_cm=Decimal("20"),
            inner_width_cm=Decimal("20"),
            inner_height_cm=Decimal("20"),
            max_weight_kg=Decimal("5"),
            cost=Decimal("10.00"),
        )
        self.order = create_order([(self.product, 2)])
        self.place_url = reverse(
            "box_selection:order-place",
            args=[self.order.pk],
        )

    def test_staff_can_place_draft_with_suitable_catalog_box(self):
        response = self.client.post(self.place_url, follow=True)

        self.assertEqual(
            response.redirect_chain,
            [(reverse("box_selection:order-detail", args=[self.order.pk]), 302)],
        )
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.PLACED)
        self.assertContains(response, "Order placed successfully.")
        self.assertNotContains(response, ">Place order</button>")
        self.assertContains(
            self.client.get(reverse("box_selection:order-list")),
            "Placed",
        )

    def test_custom_box_suggestion_cannot_be_used_to_place_order(self):
        BoxRecommendation.objects.filter(order=self.order).update(box=None)

        response = self.client.post(self.place_url, follow=True)

        self.assertEqual(
            response.redirect_chain,
            [(reverse("box_selection:order-detail", args=[self.order.pk]), 302)],
        )
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.DRAFT)
        self.assertContains(
            response,
            "This order has only a custom box suggestion. Add a suitable "
            "shipping box to the catalog",
        )

    def test_placing_an_order_requires_post(self):
        response = self.client.get(self.place_url)

        self.assertEqual(response.status_code, 405)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.DRAFT)

    def test_placed_order_cannot_be_placed_again(self):
        self.client.post(self.place_url)
        self.client.get(
            reverse("box_selection:order-detail", args=[self.order.pk])
        )

        response = self.client.post(self.place_url, follow=True)

        self.assertEqual(
            response.redirect_chain,
            [(reverse("box_selection:order-detail", args=[self.order.pk]), 302)],
        )
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.PLACED)
        self.assertContains(response, "Only draft orders can be placed.")

    def test_detail_and_order_action_menu_offer_place_option_for_drafts(self):
        detail = self.client.get(
            reverse("box_selection:order-detail", args=[self.order.pk])
        )
        order_list = self.client.get(reverse("box_selection:order-list"))

        self.assertContains(detail, f'action="{self.place_url}"')
        self.assertContains(detail, ">Place order</button>")
        self.assertContains(order_list, f'action="{self.place_url}"')
        self.assertContains(order_list, ">Place order</button>")


class CreateOrderServiceTests(TestCase):
    def test_empty_order_is_not_created(self):
        with self.assertRaisesMessage(ValueError, "at least one product"):
            create_order([])

        self.assertFalse(Order.objects.exists())

    def test_invalid_quantity_is_not_created(self):
        product = Product.objects.create(
            name="Desk lamp",
            sku="LAMP-001",
            length_cm=Decimal("12"),
            width_cm=Decimal("10"),
            height_cm=Decimal("30"),
            weight_kg=Decimal("1.250"),
        )

        with self.assertRaisesMessage(ValueError, "positive whole number"):
            create_order([(product, 0)])

        self.assertFalse(Order.objects.exists())

    def test_boolean_quantity_is_not_created(self):
        product = Product.objects.create(
            name="Desk lamp",
            sku="LAMP-001",
            length_cm=Decimal("12"),
            width_cm=Decimal("10"),
            height_cm=Decimal("30"),
            weight_kg=Decimal("1.250"),
        )

        with self.assertRaisesMessage(ValueError, "positive whole number"):
            create_order([(product, True)])

        self.assertFalse(Order.objects.exists())

    def test_duplicate_product_lines_are_rejected(self):
        product = Product.objects.create(
            name="Desk lamp",
            sku="LAMP-001",
            length_cm=Decimal("12"),
            width_cm=Decimal("10"),
            height_cm=Decimal("30"),
            weight_kg=Decimal("1.250"),
        )

        with self.assertRaisesMessage(ValueError, "only once"):
            create_order([(product, 1), (product, 2)])

        self.assertFalse(Order.objects.exists())
