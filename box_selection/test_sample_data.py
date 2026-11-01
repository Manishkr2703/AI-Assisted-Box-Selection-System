from decimal import Decimal
from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from .algorithms import BoxSpec, PackingItem, select_box
from .management.commands.seed_box_data import BOXES, PRODUCTS
from .models import Box, Product
from .services import create_order


class SampleDataTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_box_data", stdout=StringIO())
        cls.products = list(Product.objects.filter(sku__startswith="SAMPLE-"))
        cls.boxes = list(Box.objects.filter(name__in=[box["name"] for box in BOXES]))

    def test_seed_command_creates_all_requested_product_details(self):
        self.assertEqual(len(self.products), 10)
        products_by_sku = {product.sku: product for product in self.products}

        for expected in PRODUCTS:
            with self.subTest(sku=expected["sku"]):
                product = products_by_sku[expected["sku"]]
                self.assertEqual(product.name, expected["name"])
                self.assertTrue(product.description)
                self.assertTrue(product.category)
                self.assertGreater(product.price, Decimal("0"))
                self.assertEqual(product.length_cm, expected["length_cm"])
                self.assertEqual(product.width_cm, expected["width_cm"])
                self.assertEqual(product.height_cm, expected["height_cm"])
                self.assertEqual(product.weight_kg, expected["weight_kg"])

    def test_each_of_ten_sample_products_fits_at_least_one_seeded_box(self):
        box_specs = [
            BoxSpec(
                id=box.pk,
                name=box.name,
                length_cm=box.inner_length_cm,
                width_cm=box.inner_width_cm,
                height_cm=box.inner_height_cm,
                max_weight_kg=box.max_weight_kg,
                cost=box.cost,
                tare_weight_kg=box.tare_weight_kg,
            )
            for box in self.boxes
        ]

        for product in self.products:
            with self.subTest(product=product.name):
                selection = select_box(
                    [
                        PackingItem(
                            sku=product.sku,
                            length_cm=product.length_cm,
                            width_cm=product.width_cm,
                            height_cm=product.height_cm,
                            weight_kg=product.weight_kg,
                            allow_rotation=product.allow_rotation,
                        )
                    ],
                    box_specs,
                )
                self.assertTrue(selection.is_feasible, selection.explanation)

    def test_seed_command_creates_five_boxes_with_requested_specs(self):
        boxes_by_name = {box.name: box for box in self.boxes}
        self.assertEqual(len(boxes_by_name), 5)

        for expected in BOXES:
            with self.subTest(box=expected["name"]):
                box = boxes_by_name[expected["name"]]
                self.assertEqual(box.inner_length_cm, expected["inner_length_cm"])
                self.assertEqual(box.inner_width_cm, expected["inner_width_cm"])
                self.assertEqual(box.inner_height_cm, expected["inner_height_cm"])
                self.assertEqual(box.max_weight_kg, expected["max_weight_kg"])
                self.assertEqual(box.cost, expected["cost"])

    def test_seed_command_is_idempotent(self):
        call_command("seed_box_data", stdout=StringIO())
        call_command("seed_box_data", stdout=StringIO())

        self.assertEqual(
            Product.objects.filter(sku__startswith="SAMPLE-").count(),
            10,
        )
        self.assertEqual(
            Box.objects.filter(name__in=[box["name"] for box in BOXES]).count(),
            5,
        )

    def test_multi_product_quantities_create_order_and_recommendation(self):
        products_by_name = {product.name: product for product in self.products}

        order = create_order(
            [
                (products_by_name["Smartphone"], 2),
                (products_by_name["Mouse"], 3),
            ]
        )

        self.assertEqual(order.items.count(), 2)
        self.assertEqual(order.total_item_weight, Decimal("0.850"))
        self.assertTrue(order.box_recommendation.selected_box["name"])
