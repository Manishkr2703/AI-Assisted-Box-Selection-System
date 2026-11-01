from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Box, BoxRecommendation, Order, OrderItem, Product


class ManagementViewsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = get_user_model().objects.create_user(
            username="manager",
            password="test-password",
            is_staff=True,
        )
        cls.product = Product.objects.create(
            name="Desk lamp",
            sku="LAMP-001",
            length_cm=Decimal("12"),
            width_cm=Decimal("10"),
            height_cm=Decimal("30"),
            weight_kg=Decimal("1.250"),
        )
        cls.box = Box.objects.create(
            name="Small",
            inner_length_cm=Decimal("40"),
            inner_width_cm=Decimal("30"),
            inner_height_cm=Decimal("20"),
            max_weight_kg=Decimal("10"),
            cost=Decimal("2.50"),
        )

    def setUp(self):
        self.client.force_login(self.staff)

    def test_management_pages_require_staff_login(self):
        self.client.logout()

        response = self.client.get(reverse("box_selection:product-list"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response.url)

    def test_authenticated_non_staff_user_is_forbidden(self):
        customer = get_user_model().objects.create_user(
            username="customer",
            password="test-password",
        )
        self.client.force_login(customer)

        response = self.client.get(reverse("box_selection:box-list"))

        self.assertEqual(response.status_code, 403)

    def test_product_list_detail_create_update_and_delete(self):
        list_response = self.client.get(reverse("box_selection:product-list"))
        detail_response = self.client.get(
            reverse("box_selection:product-detail", args=[self.product.pk])
        )
        self.assertContains(list_response, "LAMP-001")
        self.assertContains(detail_response, "Desk lamp")

        create_response = self.client.post(
            reverse("box_selection:product-add"),
            {
                "name": "Book",
                "sku": "BOOK-001",
                "description": "A paperback book.",
                "category": "Books",
                "price": "499.00",
                "length_cm": "20",
                "width_cm": "15",
                "height_cm": "2",
                "weight_kg": "0.5",
            },
        )
        created = Product.objects.get(sku="BOOK-001")
        self.assertRedirects(
            create_response,
            reverse("box_selection:product-list"),
        )

        update_response = self.client.post(
            reverse("box_selection:product-edit", args=[created.pk]),
            {
                "name": "Updated book",
                "sku": "BOOK-001",
                "description": "An updated paperback book.",
                "category": "Books",
                "price": "599.00",
                "length_cm": "21",
                "width_cm": "15",
                "height_cm": "2",
                "weight_kg": "0.5",
            },
        )
        created.refresh_from_db()
        self.assertRedirects(
            update_response,
            reverse("box_selection:product-list"),
        )
        self.assertEqual(created.name, "Updated book")

        delete_response = self.client.post(
            reverse("box_selection:product-delete", args=[created.pk])
        )
        self.assertRedirects(
            delete_response,
            reverse("box_selection:product-list"),
        )
        self.assertFalse(Product.objects.filter(pk=created.pk).exists())

    def test_box_list_detail_create_update_and_delete(self):
        list_response = self.client.get(reverse("box_selection:box-list"))
        detail_response = self.client.get(
            reverse("box_selection:box-detail", args=[self.box.pk])
        )
        self.assertContains(list_response, "Small")
        self.assertContains(detail_response, "10.000")

        create_response = self.client.post(
            reverse("box_selection:box-add"),
            {
                "name": "Large",
                "inner_length_cm": "60",
                "inner_width_cm": "50",
                "inner_height_cm": "40",
                "max_weight_kg": "20",
                "cost": "5.00",
            },
        )
        created = Box.objects.get(name="Large")
        self.assertRedirects(create_response, reverse("box_selection:box-list"))

        update_response = self.client.post(
            reverse("box_selection:box-edit", args=[created.pk]),
            {
                "name": "Large updated",
                "inner_length_cm": "61",
                "inner_width_cm": "50",
                "inner_height_cm": "40",
                "max_weight_kg": "20",
                "cost": "5.00",
            },
        )
        created.refresh_from_db()
        self.assertRedirects(update_response, reverse("box_selection:box-list"))
        self.assertEqual(created.name, "Large updated")

        delete_response = self.client.post(
            reverse("box_selection:box-delete", args=[created.pk])
        )
        self.assertRedirects(delete_response, reverse("box_selection:box-list"))
        self.assertFalse(Box.objects.filter(pk=created.pk).exists())

    def test_forms_reject_invalid_measurements_capacity_and_cost(self):
        invalid_product_response = self.client.post(
            reverse("box_selection:product-add"),
            {
                "name": "Invalid product",
                "sku": "BAD-001",
                "length_cm": "0",
                "width_cm": "-1",
                "height_cm": "10",
                "weight_kg": "0",
            },
        )
        self.assertEqual(invalid_product_response.status_code, 200)
        self.assertFalse(Product.objects.filter(sku="BAD-001").exists())
        self.assertContains(
            invalid_product_response,
            "Enter a value greater than zero.",
        )

        invalid_box_response = self.client.post(
            reverse("box_selection:box-add"),
            {
                "name": "Invalid box",
                "inner_length_cm": "0",
                "inner_width_cm": "10",
                "inner_height_cm": "10",
                "max_weight_kg": "0",
                "cost": "-1",
            },
        )
        self.assertEqual(invalid_box_response.status_code, 200)
        self.assertFalse(Box.objects.filter(name="Invalid box").exists())
        self.assertContains(invalid_box_response, "Enter a non-negative value.")

    def test_product_used_by_order_cannot_be_deleted(self):
        order = Order.objects.create()
        OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=1,
        )

        response = self.client.post(
            reverse("box_selection:product-delete", args=[self.product.pk]),
            follow=True,
        )

        self.assertTrue(Product.objects.filter(pk=self.product.pk).exists())
        self.assertContains(
            response,
            "This product is used by an order and cannot be deleted.",
        )

    def test_box_used_by_recommendation_cannot_be_deleted(self):
        BoxRecommendation.objects.create(
            order=Order.objects.create(),
            box=self.box,
            algorithm_version="test",
        )

        response = self.client.post(
            reverse("box_selection:box-delete", args=[self.box.pk]),
            follow=True,
        )

        self.assertTrue(Box.objects.filter(pk=self.box.pk).exists())
        self.assertContains(
            response,
            "This box is used by a saved recommendation and cannot be deleted.",
        )
