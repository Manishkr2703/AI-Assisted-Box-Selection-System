from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from box_selection.models import Box, Product


PRODUCTS = (
    {
        "name": "Smartphone",
        "sku": "SAMPLE-PHONE-001",
        "description": "Smartphone packed in a protective retail carton.",
        "category": "Electronics",
        "price": Decimal("69999.00"),
        "length_cm": Decimal("16"),
        "width_cm": Decimal("8"),
        "height_cm": Decimal("2"),
        "weight_kg": Decimal("0.200"),
    },
    {
        "name": "Laptop",
        "sku": "SAMPLE-LAPTOP-001",
        "description": "Portable laptop with charger, packed in its carton.",
        "category": "Electronics",
        "price": Decimal("89999.00"),
        "length_cm": Decimal("36"),
        "width_cm": Decimal("25"),
        "height_cm": Decimal("3"),
        "weight_kg": Decimal("1.800"),
    },
    {
        "name": "Headphones",
        "sku": "SAMPLE-HEADPHONES-001",
        "description": "Over-ear headphones in a retail protective case.",
        "category": "Electronics",
        "price": Decimal("3999.00"),
        "length_cm": Decimal("22"),
        "width_cm": Decimal("20"),
        "height_cm": Decimal("10"),
        "weight_kg": Decimal("0.400"),
    },
    {
        "name": "Water Bottle",
        "sku": "SAMPLE-BOTTLE-001",
        "description": "Reusable water bottle packed upright in a carton.",
        "category": "Home & Kitchen",
        "price": Decimal("799.00"),
        "length_cm": Decimal("28"),
        "width_cm": Decimal("8"),
        "height_cm": Decimal("8"),
        "weight_kg": Decimal("0.500"),
    },
    {
        "name": "Coffee Mug",
        "sku": "SAMPLE-MUG-001",
        "description": "Ceramic coffee mug in a protective retail box.",
        "category": "Home & Kitchen",
        "price": Decimal("499.00"),
        "length_cm": Decimal("12"),
        "width_cm": Decimal("10"),
        "height_cm": Decimal("10"),
        "weight_kg": Decimal("0.350"),
    },
    {
        "name": "Keyboard",
        "sku": "SAMPLE-KEYBOARD-001",
        "description": "Full-size keyboard packed in a slim carton.",
        "category": "Computer Accessories",
        "price": Decimal("2999.00"),
        "length_cm": Decimal("45"),
        "width_cm": Decimal("15"),
        "height_cm": Decimal("4"),
        "weight_kg": Decimal("0.800"),
    },
    {
        "name": "Mouse",
        "sku": "SAMPLE-MOUSE-001",
        "description": "Wireless computer mouse in a compact package.",
        "category": "Computer Accessories",
        "price": Decimal("999.00"),
        "length_cm": Decimal("12"),
        "width_cm": Decimal("7"),
        "height_cm": Decimal("4"),
        "weight_kg": Decimal("0.150"),
    },
    {
        "name": "Shoes",
        "sku": "SAMPLE-SHOES-001",
        "description": "Pair of shoes packed together in a shoe box.",
        "category": "Footwear",
        "price": Decimal("4999.00"),
        "length_cm": Decimal("32"),
        "width_cm": Decimal("22"),
        "height_cm": Decimal("12"),
        "weight_kg": Decimal("1.200"),
    },
    {
        "name": "Backpack",
        "sku": "SAMPLE-BACKPACK-001",
        "description": "Everyday backpack folded into its shipping carton.",
        "category": "Bags",
        "price": Decimal("3499.00"),
        "length_cm": Decimal("40"),
        "width_cm": Decimal("30"),
        "height_cm": Decimal("15"),
        "weight_kg": Decimal("0.900"),
    },
    {
        "name": "Tablet",
        "sku": "SAMPLE-TABLET-001",
        "description": "Tablet device packed in a protective retail carton.",
        "category": "Electronics",
        "price": Decimal("32999.00"),
        "length_cm": Decimal("26"),
        "width_cm": Decimal("18"),
        "height_cm": Decimal("2"),
        "weight_kg": Decimal("0.600"),
    },
)

BOXES = (
    {
        "name": "Small",
        "inner_length_cm": Decimal("20"),
        "inner_width_cm": Decimal("15"),
        "inner_height_cm": Decimal("10"),
        "max_weight_kg": Decimal("2"),
        "tare_weight_kg": Decimal("0.100"),
        "cost": Decimal("20.00"),
    },
    {
        "name": "Medium",
        "inner_length_cm": Decimal("35"),
        "inner_width_cm": Decimal("25"),
        "inner_height_cm": Decimal("15"),
        "max_weight_kg": Decimal("5"),
        "tare_weight_kg": Decimal("0.200"),
        "cost": Decimal("35.00"),
    },
    {
        "name": "Large",
        "inner_length_cm": Decimal("45"),
        "inner_width_cm": Decimal("35"),
        "inner_height_cm": Decimal("20"),
        "max_weight_kg": Decimal("10"),
        "tare_weight_kg": Decimal("0.350"),
        "cost": Decimal("50.00"),
    },
    {
        "name": "Extra Large",
        "inner_length_cm": Decimal("55"),
        "inner_width_cm": Decimal("40"),
        "inner_height_cm": Decimal("30"),
        "max_weight_kg": Decimal("15"),
        "tare_weight_kg": Decimal("0.500"),
        "cost": Decimal("70.00"),
    },
    {
        "name": "Premium",
        "inner_length_cm": Decimal("65"),
        "inner_width_cm": Decimal("50"),
        "inner_height_cm": Decimal("40"),
        "max_weight_kg": Decimal("25"),
        "tare_weight_kg": Decimal("0.800"),
        "cost": Decimal("100.00"),
    },
)


class Command(BaseCommand):
    help = "Create or update the sample products and shipping boxes."

    @transaction.atomic
    def handle(self, *args, **options):
        for product_data in PRODUCTS:
            sku = product_data["sku"]
            defaults = {
                key: value
                for key, value in product_data.items()
                if key != "sku"
            }
            Product.objects.update_or_create(sku=sku, defaults=defaults)

        for box_data in BOXES:
            name = box_data["name"]
            defaults = {
                key: value
                for key, value in box_data.items()
                if key != "name"
            }
            Box.objects.update_or_create(name=name, defaults=defaults)

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {len(PRODUCTS)} products and {len(BOXES)} shipping boxes."
            )
        )
