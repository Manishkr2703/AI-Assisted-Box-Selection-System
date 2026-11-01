from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Box, BoxRecommendation, Order, OrderItem, Product
from .services import ALGORITHM_VERSION, recommend_box_for_order


class RecommendationServiceTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name="Desk lamp",
            sku="LAMP-001",
            length_cm=Decimal("12"),
            width_cm=Decimal("10"),
            height_cm=Decimal("30"),
            weight_kg=Decimal("1.250"),
        )
        self.order = Order.objects.create()
        OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=1,
        )
        self.box = Box.objects.create(
            name="Small",
            inner_length_cm=Decimal("12"),
            inner_width_cm=Decimal("10"),
            inner_height_cm=Decimal("30"),
            max_weight_kg=Decimal("10"),
            cost=Decimal("2.50"),
        )

    def test_saves_recommendation_for_order(self):
        recommendation = recommend_box_for_order(self.order)

        self.assertEqual(recommendation.box, self.box)
        self.assertEqual(recommendation.algorithm_version, ALGORITHM_VERSION)
        self.assertEqual(recommendation.score, Decimal("100.00"))

    def test_new_box_invalidates_recommendation_and_recalculation_selects_it(self):
        first = recommend_box_for_order(self.order)
        another_box = Box.objects.create(
            name="Cheaper",
            inner_length_cm=Decimal("12"),
            inner_width_cm=Decimal("10"),
            inner_height_cm=Decimal("30"),
            max_weight_kg=Decimal("10"),
            cost=Decimal("1.00"),
        )

        self.assertFalse(BoxRecommendation.objects.filter(pk=first.pk).exists())
        updated = recommend_box_for_order(self.order)

        self.assertEqual(updated.box, another_box)
        self.assertEqual(BoxRecommendation.objects.filter(order=self.order).count(), 1)

    def test_suggests_custom_box_when_catalog_boxes_do_not_fit(self):
        recommendation = recommend_box_for_order(self.order)
        self.box.max_weight_kg = Decimal("0.500")
        self.box.save()

        result = recommend_box_for_order(self.order)

        self.assertNotEqual(result.pk, recommendation.pk)
        self.assertIsNone(result.box)
        self.assertEqual(result.selected_box["name"], "Custom suggested box")
        self.assertIn("exceeds capacity", result.explanation)
        self.assertFalse(BoxRecommendation.objects.filter(pk=recommendation.pk).exists())
        self.assertTrue(BoxRecommendation.objects.filter(pk=result.pk).exists())

    def test_suggests_custom_box_when_catalog_is_empty(self):
        self.box.delete()

        recommendation = recommend_box_for_order(self.order)

        self.assertIsNone(recommendation.box)
        self.assertEqual(
            recommendation.selected_box["name"],
            "Custom suggested box",
        )
        self.assertEqual(recommendation.selected_box["length_cm"], "14.00")
        self.assertEqual(recommendation.selected_box["width_cm"], "16.00")
        self.assertEqual(recommendation.selected_box["height_cm"], "34.00")
        self.assertIsNone(recommendation.selected_box["cost"])
        self.assertIsNone(recommendation.selected_box["tare_weight_kg"])
        self.assertIsNone(recommendation.estimated_gross_weight_kg)
        self.assertIn("2 cm of clearance", recommendation.explanation)
        self.assertIn(
            "packaging cost and empty-box weight are unknown",
            recommendation.explanation,
        )

    def test_saves_other_feasible_boxes_as_alternatives(self):
        alternative = Box.objects.create(
            name="Alternative",
            inner_length_cm=Decimal("20"),
            inner_width_cm=Decimal("20"),
            inner_height_cm=Decimal("40"),
            max_weight_kg=Decimal("5"),
            cost=Decimal("4.00"),
        )

        recommendation = recommend_box_for_order(self.order)

        self.assertEqual(recommendation.box, self.box)
        self.assertEqual(recommendation.alternatives[0]["box_id"], alternative.pk)
        self.assertEqual(recommendation.alternatives[0]["name"], "Alternative")

    def test_product_rotation_rule_is_used_in_recommendation(self):
        self.product.allow_rotation = False
        self.product.save()
        self.order.items.all().delete()
        OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=1,
        )
        item = self.order.items.get()
        self.assertFalse(item.allow_rotation)
        self.box.inner_length_cm = Decimal("10")
        self.box.inner_width_cm = Decimal("12")
        self.box.save()

        recommendation = recommend_box_for_order(self.order)

        self.assertIsNone(recommendation.box)
        self.assertEqual(recommendation.selected_box["name"], "Custom suggested box")
        self.assertIn("heuristic found no", recommendation.explanation)

    def test_box_edits_invalidate_existing_recommendations(self):
        recommendation = recommend_box_for_order(self.order)
        self.box.cost = Decimal("3.00")
        self.box.save()

        self.assertFalse(
            BoxRecommendation.objects.filter(pk=recommendation.pk).exists()
        )

    def test_estimated_gross_weight_includes_saved_tare_weight(self):
        self.box.tare_weight_kg = Decimal("0.750")
        self.box.save()
        recommendation = recommend_box_for_order(self.order)

        self.assertEqual(
            recommendation.estimated_gross_weight_kg,
            Decimal("2.000"),
        )


    def test_requires_order_items(self):
        empty_order = Order.objects.create()

        with self.assertRaisesMessage(ValueError, "at least one item"):
            recommend_box_for_order(empty_order)


class OrderRecommendationDashboardTests(TestCase):
    def setUp(self):
        self.staff = get_user_model().objects.create_user(
            username="warehouse_manager",
            password="test-password",
            is_staff=True,
        )
        self.client.force_login(self.staff)
        self.order = Order.objects.create()
        self.product = Product.objects.create(
            name="Desk lamp",
            sku="LAMP-001",
            length_cm=Decimal("12"),
            width_cm=Decimal("10"),
            height_cm=Decimal("30"),
            weight_kg=Decimal("1.250"),
        )
        OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=2,
        )

    def test_order_detail_can_run_recommendation_and_display_box(self):
        box = Box.objects.create(
            name="Small",
            inner_length_cm=Decimal("24"),
            inner_width_cm=Decimal("10"),
            inner_height_cm=Decimal("30"),
            max_weight_kg=Decimal("10"),
            cost=Decimal("2.50"),
        )
        Box.objects.create(
            name="Large",
            inner_length_cm=Decimal("30"),
            inner_width_cm=Decimal("10"),
            inner_height_cm=Decimal("30"),
            max_weight_kg=Decimal("10"),
            cost=Decimal("3.50"),
        )

        response = self.client.post(
            reverse("box_selection:order-recommend", args=[self.order.pk])
        )

        self.assertRedirects(
            response,
            reverse("box_selection:order-detail", args=[self.order.pk]),
        )
        detail = self.client.get(
            reverse("box_selection:order-detail", args=[self.order.pk])
        )
        self.assertContains(detail, "Order contents")
        self.assertContains(detail, "2.500 kg")
        self.assertContains(detail, "Recommended shipping box")
        self.assertContains(detail, box.name)
        self.assertContains(detail, "Weight capacity")
        self.assertContains(detail, "Other suitable boxes")
        self.assertContains(detail, "Large")

    def test_custom_box_suggestion_is_shown_when_catalog_is_empty(self):
        response = self.client.post(
            reverse("box_selection:order-recommend", args=[self.order.pk])
        )

        self.assertRedirects(
            response,
            reverse("box_selection:order-detail", args=[self.order.pk]),
        )
        detail = self.client.get(
            reverse("box_selection:order-detail", args=[self.order.pk])
        )
        self.assertContains(detail, "Custom size suggestion")
        self.assertContains(detail, "Custom suggested box")
        self.assertContains(detail, "Estimated shipment gross weight")
        self.assertContains(detail, "Empty-box weight is unavailable.")
        for dimension in ("28.00", "16.00", "34.00"):
            self.assertContains(detail, dimension)
        self.assertContains(detail, "Not priced")

    def test_custom_box_fallback_shown_if_configured_boxes_do_not_fit(self):
        Box.objects.create(
            name="Too small",
            inner_length_cm=Decimal("5"),
            inner_width_cm=Decimal("5"),
            inner_height_cm=Decimal("5"),
            max_weight_kg=Decimal("1"),
            cost=Decimal("1"),
        )
        response = self.client.post(
            reverse("box_selection:order-recommend", args=[self.order.pk])
        )
        self.assertRedirects(
            response,
            reverse("box_selection:order-detail", args=[self.order.pk]),
        )

        detail = self.client.get(
            reverse("box_selection:order-detail", args=[self.order.pk])
        )
        self.assertContains(detail, "Custom size suggestion")
        self.assertContains(detail, "No suitable single box was found")
        self.assertContains(detail, "Not priced")
