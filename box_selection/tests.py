from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import Box, BoxRecommendation, Order, OrderItem, Product


class ProductTests(TestCase):
    def make_product(self, **overrides):
        values = {
            "name": "Desk lamp",
            "sku": "LAMP-001",
            "length_cm": Decimal("12.00"),
            "width_cm": Decimal("10.00"),
            "height_cm": Decimal("30.00"),
            "weight_kg": Decimal("1.250"),
        }
        values.update(overrides)
        return Product.objects.create(**values)

    def test_product_requires_positive_dimensions_and_weight(self):
        product = Product(
            name="Invalid product",
            sku="BAD-001",
            length_cm=Decimal("0"),
            width_cm=Decimal("10"),
            height_cm=Decimal("10"),
            weight_kg=Decimal("1"),
        )

        with self.assertRaises(ValidationError):
            product.full_clean()

    def test_sku_must_be_unique(self):
        self.make_product()
        duplicate = Product(
            name="Another product",
            sku="LAMP-001",
            length_cm=Decimal("10"),
            width_cm=Decimal("10"),
            height_cm=Decimal("10"),
            weight_kg=Decimal("1"),
        )

        with self.assertRaises(ValidationError):
            duplicate.full_clean()


class OrderItemTests(TestCase):
    def test_order_item_snapshots_product_details_when_created(self):
        product = Product.objects.create(
            name="Desk lamp",
            sku="LAMP-001",
            length_cm=Decimal("12.00"),
            width_cm=Decimal("10.00"),
            height_cm=Decimal("30.00"),
            weight_kg=Decimal("1.250"),
        )
        order = Order.objects.create()
        item = OrderItem.objects.create(order=order, product=product, quantity=2)

        product.name = "Updated lamp"
        product.length_cm = Decimal("15.00")
        product.save()
        item.quantity = 3
        item.save()
        item.refresh_from_db()

        self.assertEqual(item.product_name, "Desk lamp")
        self.assertEqual(item.length_cm, Decimal("12.00"))
        self.assertEqual(item.quantity, 3)

    def test_order_item_quantity_must_be_at_least_one(self):
        product = Product.objects.create(
            name="Desk lamp",
            sku="LAMP-001",
            length_cm=Decimal("12.00"),
            width_cm=Decimal("10.00"),
            height_cm=Decimal("30.00"),
            weight_kg=Decimal("1.250"),
        )
        item = OrderItem(
            order=Order.objects.create(),
            product=product,
            quantity=0,
        )

        with self.assertRaises(ValidationError):
            item.full_clean()


class BoxRecommendationTests(TestCase):
    def test_recommendation_rejects_scores_above_100(self):
        box = Box.objects.create(
            name="Medium",
            inner_length_cm=Decimal("40.00"),
            inner_width_cm=Decimal("30.00"),
            inner_height_cm=Decimal("20.00"),
            max_weight_kg=Decimal("10.000"),
            cost=Decimal("2.50"),
        )
        recommendation = BoxRecommendation(
            order=Order.objects.create(),
            box=box,
            score=Decimal("100.01"),
            algorithm_version="deterministic-v1",
        )

        with self.assertRaises(ValidationError):
            recommendation.full_clean()

    def test_order_has_one_recommendation(self):
        box = Box.objects.create(
            name="Medium",
            inner_length_cm=Decimal("40.00"),
            inner_width_cm=Decimal("30.00"),
            inner_height_cm=Decimal("20.00"),
            max_weight_kg=Decimal("10.000"),
            cost=Decimal("2.50"),
        )
        order = Order.objects.create()
        BoxRecommendation.objects.create(
            order=order,
            box=box,
            algorithm_version="deterministic-v1",
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                BoxRecommendation.objects.create(
                    order=order,
                    box=box,
                    algorithm_version="deterministic-v1",
                )
