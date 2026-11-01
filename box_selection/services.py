from decimal import Decimal

from django.db import transaction

from .algorithms import (
    BoxOption,
    BoxSpec,
    PackingItem,
    select_box,
    suggest_custom_box,
)
from .models import Box, BoxRecommendation, Order, OrderItem, Product


ALGORITHM_VERSION = "corner-point-v2"
CUSTOM_ALGORITHM_VERSION = "single-row-custom-v1"
CUSTOM_BOX_CLEARANCE_CM = Decimal("2")
CUSTOM_BOX_COST = None


def _serialize_box_option(option: BoxOption) -> dict:
    return {
        "box_id": option.box_id if option.box_id > 0 else None,
        "name": option.name,
        "length_cm": str(option.length_cm),
        "width_cm": str(option.width_cm),
        "height_cm": str(option.height_cm),
        "max_weight_kg": str(option.max_weight_kg),
        "cost": str(option.cost) if option.cost is not None else None,
        "score": str(option.score),
        "tare_weight_kg": (
            str(option.tare_weight_kg)
            if option.tare_weight_kg is not None
            else None
        ),
    }


@transaction.atomic
def create_order(items: list[tuple[Product, int]]) -> Order:
    """Create an order and all its product lines as one database operation."""
    if not items:
        raise ValueError("An order must contain at least one product.")

    seen_product_ids = set()
    for product, quantity in items:
        if product.pk is None:
            raise ValueError("Save every product before adding it to an order.")
        if (
            not isinstance(quantity, int)
            or isinstance(quantity, bool)
            or quantity < 1
        ):
            raise ValueError("Each order quantity must be a positive whole number.")
        if product.pk in seen_product_ids:
            raise ValueError("Each product can appear only once per order.")
        seen_product_ids.add(product.pk)

    order = Order.objects.create()
    for product, quantity in items:
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=quantity,
        )
    recommend_box_for_order(order)
    return order


@transaction.atomic
def place_order(order: Order) -> Order:
    """Place a draft order only after it has a suitable catalog-box selection."""
    if order.pk is None:
        raise ValueError("Save the order before placing it.")

    locked_order = Order.objects.select_for_update().get(pk=order.pk)
    if locked_order.status != Order.Status.DRAFT:
        raise ValueError("Only draft orders can be placed.")
    if not locked_order.items.exists():
        raise ValueError("An order must contain at least one product.")

    recommendation = (
        BoxRecommendation.objects.select_related("box")
        .filter(order=locked_order)
        .first()
    )
    if recommendation is None:
        raise ValueError("Run a box recommendation before placing this order.")
    if recommendation.box_id is None:
        raise ValueError(
            "This order has only a custom box suggestion. Add a suitable "
            "shipping box to the catalog and run the recommendation again "
            "before placing it."
        )

    locked_order.status = Order.Status.PLACED
    locked_order.save(update_fields=["status"])
    return locked_order


@transaction.atomic
def recommend_box_for_order(order: Order) -> BoxRecommendation:
    """Save the recommendation and feasible alternatives for an order.

    If no feasible catalog box is found, the recommendation includes a custom
    single-row size suggestion and preserves the selector's rejection details.
    Orders requiring multiple boxes are not supported yet.
    """
    if order.pk is None:
        raise ValueError("Save the order before requesting a box recommendation.")

    order_items = list(order.items.all())
    if not order_items:
        raise ValueError("An order must contain at least one item.")

    items = [
        PackingItem(
            sku=item.sku,
            length_cm=item.length_cm,
            width_cm=item.width_cm,
            height_cm=item.height_cm,
            weight_kg=item.weight_kg,
            quantity=item.quantity,
            allow_rotation=item.allow_rotation,
        )
        for item in order_items
    ]
    boxes = [
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
        for box in Box.objects.all()
    ]

    selection = None
    selected_box = None
    if boxes:
        selection = select_box(items, boxes)
        if selection.box_id is not None and selection.score is not None:
            selected_box = next(
                BoxOption(
                    box_id=box.id,
                    name=box.name,
                    length_cm=box.length_cm,
                    width_cm=box.width_cm,
                    height_cm=box.height_cm,
                    max_weight_kg=box.max_weight_kg,
                    cost=box.cost,
                    score=selection.score,
                    tare_weight_kg=box.tare_weight_kg,
                )
                for box in boxes
                if box.id == selection.box_id
            )

    custom_suggestion = selected_box is None
    if custom_suggestion:
        catalog_result = selection.explanation if selection is not None else ""
        selected_box = suggest_custom_box(
            items,
            clearance_cm=CUSTOM_BOX_CLEARANCE_CM,
            cost=CUSTOM_BOX_COST,
        )
    if selected_box is None:
        raise RuntimeError("Box selection did not produce a catalog or custom box.")

    if custom_suggestion:
        explanation = (
            f"{catalog_result} "
            if catalog_result
            else "No catalog boxes are configured. "
        ) + (
            "A custom box is suggested using a single-row layout, with 2 cm "
            "of clearance on every side of each product. The packaging cost "
            "and empty-box weight are unknown and must be confirmed before "
            "fulfillment."
        )
    else:
        explanation = selection.explanation

    recommendation, _ = BoxRecommendation.objects.update_or_create(
        order=order,
        defaults={
            "box_id": selected_box.box_id if not custom_suggestion else None,
            "selected_box": _serialize_box_option(selected_box),
            "score": selected_box.score,
            "explanation": explanation,
            "alternatives": (
                [
                    _serialize_box_option(option)
                    for option in selection.alternatives
                ]
                if selection is not None and selected_box is not None
                else []
            ),
            "algorithm_version": (
                CUSTOM_ALGORITHM_VERSION if custom_suggestion else ALGORITHM_VERSION
            ),
        },
    )
    return recommendation
