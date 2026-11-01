from decimal import Decimal

from django.test import SimpleTestCase

from .algorithms import (
    BoxSpec,
    PackingItem,
    select_box,
    suggest_custom_box,
)


def make_item(**overrides):
    values = {
        "sku": "LAMP-001",
        "length_cm": Decimal("12"),
        "width_cm": Decimal("10"),
        "height_cm": Decimal("30"),
        "weight_kg": Decimal("1.250"),
    }
    values.update(overrides)
    return PackingItem(**values)


def make_box(**overrides):
    values = {
        "id": 1,
        "name": "Small",
        "length_cm": Decimal("12"),
        "width_cm": Decimal("10"),
        "height_cm": Decimal("30"),
        "max_weight_kg": Decimal("10"),
        "cost": Decimal("2.50"),
    }
    values.update(overrides)
    return BoxSpec(**values)


class BoxSelectorTests(SimpleTestCase):
    def test_single_product_fits_exact_box_dimensions(self):
        selected = select_box(
            [make_item()],
            [make_box()],
        )

        self.assertTrue(selected.is_feasible)
        self.assertEqual(selected.box_id, 1)

    def test_selects_box_when_item_fits_after_rotation(self):
        selected = select_box(
            [make_item()],
            [make_box(length_cm=Decimal("10"), width_cm=Decimal("12"))],
        )

        self.assertTrue(selected.is_feasible)
        self.assertEqual(selected.box_id, 1)
        self.assertEqual(selected.score, Decimal("100.00"))
        self.assertIn("Rotations were allowed", selected.explanation)

    def test_rotation_can_be_disabled_for_an_item(self):
        selected = select_box(
            [make_item(allow_rotation=False)],
            [make_box(length_cm=Decimal("10"), width_cm=Decimal("12"))],
        )

        self.assertFalse(selected.is_feasible)
        self.assertIn("no non-overlapping placement", selected.explanation)

    def test_multiple_products_fit_when_placed_side_by_side(self):
        first = make_item(
            sku="CUBE-A",
            length_cm=Decimal("5"),
            width_cm=Decimal("5"),
            height_cm=Decimal("5"),
            weight_kg=Decimal("1"),
        )
        second = make_item(
            sku="CUBE-B",
            length_cm=Decimal("5"),
            width_cm=Decimal("5"),
            height_cm=Decimal("5"),
            weight_kg=Decimal("2"),
        )
        box = make_box(
            length_cm=Decimal("10"),
            width_cm=Decimal("5"),
            height_cm=Decimal("5"),
            max_weight_kg=Decimal("3"),
        )

        selected = select_box([first, second], [box])

        self.assertTrue(selected.is_feasible)
        self.assertEqual(selected.box_id, box.id)
        self.assertIn("Fits 2 item(s)", selected.explanation)

    def test_products_touching_box_boundary_are_allowed(self):
        cube = make_item(
            length_cm=Decimal("5"),
            width_cm=Decimal("5"),
            height_cm=Decimal("5"),
            quantity=2,
        )
        box = make_box(
            length_cm=Decimal("10"),
            width_cm=Decimal("5"),
            height_cm=Decimal("5"),
            max_weight_kg=Decimal("2.500"),
        )

        selected = select_box([cube], [box])

        self.assertTrue(selected.is_feasible)

    def test_selects_lowest_cost_feasible_box(self):
        expensive = make_box(id=1, name="Large", cost=Decimal("8"))
        cheap = make_box(id=2, name="Right-sized", cost=Decimal("2"))

        selected = select_box([make_item()], [expensive, cheap])

        self.assertEqual(selected.box_id, 2)

    def test_equal_cost_prefers_box_with_less_unused_volume(self):
        larger_unused = make_box(
            id=1,
            name="Larger",
            length_cm=Decimal("20"),
            width_cm=Decimal("10"),
            height_cm=Decimal("30"),
            cost=Decimal("2.50"),
        )
        right_sized = make_box(
            id=2,
            name="Right-sized",
            length_cm=Decimal("12"),
            width_cm=Decimal("10"),
            height_cm=Decimal("30"),
            cost=Decimal("2.50"),
        )

        selected = select_box([make_item()], [larger_unused, right_sized])

        self.assertEqual(selected.box_id, right_sized.id)

    def test_equal_cost_and_unused_volume_uses_lower_box_id(self):
        higher_id = make_box(id=9, name="Later", cost=Decimal("2.50"))
        lower_id = make_box(id=3, name="Earlier", cost=Decimal("2.50"))

        selected = select_box([make_item()], [higher_id, lower_id])

        self.assertEqual(selected.box_id, lower_id.id)

    def test_reports_box_that_exceeds_weight_capacity(self):
        selected = select_box(
            [make_item(weight_kg=Decimal("5"))],
            [make_box(max_weight_kg=Decimal("4"))],
        )

        self.assertFalse(selected.is_feasible)
        self.assertIn("exceeds capacity", selected.explanation)

    def test_total_weight_equal_to_capacity_is_allowed(self):
        selected = select_box(
            [make_item(weight_kg=Decimal("2.500"))],
            [make_box(max_weight_kg=Decimal("2.500"))],
        )

        self.assertTrue(selected.is_feasible)

    def test_multiple_product_weights_are_summed_before_capacity_check(self):
        first = make_item(sku="ITEM-A", weight_kg=Decimal("1.250"))
        second = make_item(sku="ITEM-B", weight_kg=Decimal("1.250"))

        selected = select_box(
            [first, second],
            [make_box(max_weight_kg=Decimal("2.499"))],
        )

        self.assertFalse(selected.is_feasible)
        self.assertIn("total item weight 2.500 kg", selected.explanation)

    def test_item_dimensions_exceeding_every_box_return_no_selection(self):
        item = make_item(
            length_cm=Decimal("31"),
            width_cm=Decimal("21"),
            height_cm=Decimal("11"),
        )
        boxes = [
            make_box(id=1, length_cm=Decimal("30")),
            make_box(id=2, width_cm=Decimal("20")),
        ]

        selected = select_box([item], boxes)

        self.assertFalse(selected.is_feasible)
        self.assertIsNone(selected.box_id)
        self.assertIn("No suitable single box", selected.explanation)
        self.assertIn("heuristic found no", selected.explanation)

    def test_rejects_items_that_cannot_be_placed_without_overlap(self):
        cube = make_item(
            length_cm=Decimal("6"),
            width_cm=Decimal("6"),
            height_cm=Decimal("6"),
            quantity=2,
        )
        box = make_box(
            length_cm=Decimal("10"),
            width_cm=Decimal("10"),
            height_cm=Decimal("6"),
        )

        selected = select_box([cube], [box])
        self.assertFalse(selected.is_feasible)
        self.assertIn("heuristic found no", selected.explanation)

    def test_reports_when_no_boxes_are_available(self):
        selected = select_box([make_item()], [])

        self.assertFalse(selected.is_feasible)
        self.assertIn("no shipping boxes are available", selected.explanation)

    def test_invalid_decimal_measurements_are_rejected(self):
        with self.assertRaisesMessage(ValueError, "must be positive"):
            select_box(
                [make_item(length_cm=Decimal("NaN"))],
                [make_box()],
            )

    def test_non_positive_and_non_integer_quantities_are_rejected(self):
        for quantity in (0, -1, 1.5, True):
            with self.subTest(quantity=quantity):
                with self.assertRaisesMessage(ValueError, "positive integer"):
                    select_box(
                        [make_item(quantity=quantity)],
                        [make_box()],
                    )

    def test_zero_and_negative_item_dimensions_are_rejected(self):
        for invalid_dimension in (Decimal("0"), Decimal("-1")):
            with self.subTest(dimension=invalid_dimension):
                with self.assertRaisesMessage(ValueError, "must be positive"):
                    select_box(
                        [make_item(width_cm=invalid_dimension)],
                        [make_box()],
                    )

    def test_invalid_box_dimensions_and_capacity_are_rejected(self):
        for field in ("length_cm", "width_cm", "height_cm", "max_weight_kg"):
            with self.subTest(field=field):
                with self.assertRaisesMessage(ValueError, "must be positive"):
                    select_box(
                        [make_item()],
                        [make_box(**{field: Decimal("0")})],
                    )

    def test_negative_box_cost_is_rejected(self):
        with self.assertRaisesMessage(ValueError, "non-negative"):
            select_box(
                [make_item()],
                [make_box(cost=Decimal("-0.01"))],
            )

    def test_zero_cost_box_is_valid_and_is_preferred(self):
        free = make_box(id=2, name="Free", cost=Decimal("0"))
        paid = make_box(id=1, name="Paid", cost=Decimal("0.01"))

        selected = select_box([make_item()], [paid, free])

        self.assertTrue(selected.is_feasible)
        self.assertEqual(selected.box_id, free.id)

    def test_exact_maximum_item_count_is_supported(self):
        selected = select_box(
            [
                make_item(
                    length_cm=Decimal("1"),
                    width_cm=Decimal("1"),
                    height_cm=Decimal("1"),
                    quantity=100,
                )
            ],
            [
                make_box(
                    length_cm=Decimal("10"),
                    width_cm=Decimal("10"),
                    height_cm=Decimal("1"),
                    max_weight_kg=Decimal("200"),
                )
            ],
        )

        self.assertTrue(selected.is_feasible)

    def test_custom_box_suggestion_includes_clearance_for_each_item(self):
        item = make_item(
            length_cm=Decimal("10"),
            width_cm=Decimal("8"),
            height_cm=Decimal("6"),
            quantity=2,
        )

        suggestion = suggest_custom_box([item], clearance_cm=Decimal("2"))

        self.assertEqual(suggestion.length_cm, Decimal("20"))
        self.assertEqual(suggestion.width_cm, Decimal("12"))
        self.assertEqual(suggestion.height_cm, Decimal("14"))
        self.assertEqual(suggestion.max_weight_kg, Decimal("2.500"))

    def test_custom_box_suggestion_preserves_orientation_when_rotation_disabled(self):
        item = make_item(
            length_cm=Decimal("10"),
            width_cm=Decimal("8"),
            height_cm=Decimal("6"),
            allow_rotation=False,
        )

        suggestion = suggest_custom_box([item], clearance_cm=Decimal("2"))

        self.assertEqual(suggestion.length_cm, Decimal("14"))
        self.assertEqual(suggestion.width_cm, Decimal("12"))
        self.assertEqual(suggestion.height_cm, Decimal("10"))

    def test_custom_box_rejects_negative_clearance(self):
        with self.assertRaisesMessage(ValueError, "Clearance must"):
            suggest_custom_box([make_item()], clearance_cm=Decimal("-1"))

    def test_empty_orders_are_invalid(self):
        with self.assertRaisesMessage(ValueError, "At least one order item"):
            select_box([], [make_box()])

    def test_limits_single_box_item_count(self):
        with self.assertRaisesMessage(ValueError, "Multi-box packing is not implemented"):
            select_box(
                [make_item(quantity=101)],
                [make_box()],
            )
