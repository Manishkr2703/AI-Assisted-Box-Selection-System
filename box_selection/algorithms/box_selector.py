from dataclasses import dataclass
from decimal import Decimal
from itertools import permutations
from typing import Sequence


MAX_ITEMS_PER_BOX = 100


@dataclass(frozen=True)
class PackingItem:
    sku: str
    length_cm: Decimal
    width_cm: Decimal
    height_cm: Decimal
    weight_kg: Decimal
    quantity: int = 1
    allow_rotation: bool = True


@dataclass(frozen=True)
class BoxSpec:
    id: int
    name: str
    length_cm: Decimal
    width_cm: Decimal
    height_cm: Decimal
    max_weight_kg: Decimal
    cost: Decimal
    tare_weight_kg: Decimal | None = None


@dataclass(frozen=True)
class Selection:
    box_id: int | None
    score: Decimal | None
    explanation: str
    alternatives: tuple["BoxOption", ...] = ()

    @property
    def is_feasible(self) -> bool:
        return self.box_id is not None


@dataclass(frozen=True)
class BoxOption:
    box_id: int
    name: str
    length_cm: Decimal
    width_cm: Decimal
    height_cm: Decimal
    max_weight_kg: Decimal
    cost: Decimal | None
    score: Decimal
    tare_weight_kg: Decimal | None = None


@dataclass(frozen=True)
class _Placement:
    x: Decimal
    y: Decimal
    z: Decimal
    length: Decimal
    width: Decimal
    height: Decimal


def _validate_inputs(items: Sequence[PackingItem], boxes: Sequence[BoxSpec]) -> None:
    if not items:
        raise ValueError("At least one order item is required.")

    item_count = 0
    for item in items:
        if (
            not isinstance(item.quantity, int)
            or isinstance(item.quantity, bool)
            or item.quantity < 1
        ):
            raise ValueError(f"Quantity for SKU {item.sku} must be a positive integer.")
        measurements = (
            item.length_cm,
            item.width_cm,
            item.height_cm,
            item.weight_kg,
        )
        if any(
            not isinstance(value, Decimal)
            or not value.is_finite()
            or value <= 0
            for value in measurements
        ):
            raise ValueError(f"Dimensions and weight for SKU {item.sku} must be positive.")
        item_count += item.quantity

    if item_count > MAX_ITEMS_PER_BOX:
        raise ValueError(
            f"This single-box selector supports at most {MAX_ITEMS_PER_BOX} "
            "individual items. Multi-box packing is not implemented."
        )

    for box in boxes:
        measurements = (
            box.length_cm,
            box.width_cm,
            box.height_cm,
            box.max_weight_kg,
        )
        if any(
            not isinstance(value, Decimal)
            or not value.is_finite()
            or value < 0
            for value in measurements
        ):
            raise ValueError(
                f"Box {box.name} measurements must be finite and non-negative."
            )
        if min(
            box.length_cm,
            box.width_cm,
            box.height_cm,
            box.max_weight_kg,
        ) <= 0:
            raise ValueError(
                f"Dimensions and capacity for box {box.name} must be positive."
            )
        if box.tare_weight_kg is not None and (
            not isinstance(box.tare_weight_kg, Decimal)
            or not box.tare_weight_kg.is_finite()
            or box.tare_weight_kg < 0
        ):
            raise ValueError(
                f"Box {box.name} tare weight must be finite and non-negative."
            )
        if (
            not isinstance(box.cost, Decimal)
            or not box.cost.is_finite()
            or box.cost < 0
        ):
            raise ValueError(
                f"Cost for box {box.name} must be a finite, non-negative number."
            )


def _overlaps(candidate: _Placement, placed: _Placement) -> bool:
    return (
        candidate.x < placed.x + placed.length
        and candidate.x + candidate.length > placed.x
        and candidate.y < placed.y + placed.width
        and candidate.y + candidate.width > placed.y
        and candidate.z < placed.z + placed.height
        and candidate.z + candidate.height > placed.z
    )


def _fits_box(items: Sequence[PackingItem], box: BoxSpec) -> bool:
    units = [
        item
        for item in items
        for _ in range(item.quantity)
    ]
    units.sort(
        key=lambda item: (
            item.length_cm * item.width_cm * item.height_cm,
            max(item.length_cm, item.width_cm, item.height_cm),
        ),
        reverse=True,
    )

    points = {(Decimal("0"), Decimal("0"), Decimal("0"))}
    placed = []
    for item in units:
        original_orientation = (item.length_cm, item.width_cm, item.height_cm)
        orientations = (
            sorted(set(permutations(original_orientation)))
            if item.allow_rotation
            else [original_orientation]
        )
        placement_found = False

        for x, y, z in sorted(points, key=lambda point: (point[2], point[1], point[0])):
            for length, width, height in orientations:
                candidate = _Placement(x, y, z, length, width, height)
                if (
                    x + length <= box.length_cm
                    and y + width <= box.width_cm
                    and z + height <= box.height_cm
                    and not any(_overlaps(candidate, other) for other in placed)
                ):
                    placed.append(candidate)
                    points.update(
                        (
                            (x + length, y, z),
                            (x, y + width, z),
                            (x, y, z + height),
                        )
                    )
                    placement_found = True
                    break
            if placement_found:
                break

        if not placement_found:
            return False

    return True


def select_box(
    items: Sequence[PackingItem],
    boxes: Sequence[BoxSpec],
) -> Selection:
    """Choose a low-cost box with deterministic greedy corner-point packing.

    Items and boxes use Decimal centimetres, kilograms, and cost in one
    consistent currency. Rotation, when allowed for an item, permits any of
    the six axis-aligned dimension permutations. A rejected candidate can be
    a false negative: greedy placement is a heuristic, not an optimal solver.
    Feasible boxes are ordered by cost, then unused volume, then box ID for a
    deterministic tie-break. Items are rigid cuboids; padding is not included.
    Capacity applies to product payload weight, while tare is reported
    separately for estimated gross shipment weight.
    """
    _validate_inputs(items, boxes)

    total_weight = sum(
        (item.weight_kg * item.quantity for item in items),
        start=Decimal("0"),
    )
    total_volume = sum(
        (
            item.length_cm * item.width_cm * item.height_cm * item.quantity
            for item in items
        ),
        start=Decimal("0"),
    )

    feasible = []
    rejected = []
    if not boxes:
        return Selection(
            box_id=None,
            score=None,
            explanation="No suitable box: no shipping boxes are available.",
        )

    for box in boxes:
        if total_weight > box.max_weight_kg:
            rejected.append(
                f"{box.name} rejected: total item weight {total_weight} kg "
                f"exceeds capacity {box.max_weight_kg} kg."
            )
            continue
        if not _fits_box(items, box):
            rejected.append(
                f"{box.name} rejected: the packing heuristic found no "
                "non-overlapping placement within its internal dimensions."
            )
            continue

        box_volume = box.length_cm * box.width_cm * box.height_cm
        unused_volume = box_volume - total_volume
        utilization = (total_volume / box_volume * Decimal("100")).quantize(
            Decimal("0.01")
        )
        option = BoxOption(
            box_id=box.id,
            name=box.name,
            length_cm=box.length_cm,
            width_cm=box.width_cm,
            height_cm=box.height_cm,
            max_weight_kg=box.max_weight_kg,
            cost=box.cost,
            score=min(utilization, Decimal("100.00")),
            tare_weight_kg=box.tare_weight_kg,
        )
        feasible.append((box.cost, unused_volume, box.id, option))

    if not feasible:
        return Selection(
            box_id=None,
            score=None,
            explanation=(
                "No suitable single box was found. A heuristic failure does "
                "not prove that no physical packing exists. "
                + " ".join(rejected)
            ),
        )

    feasible.sort(key=lambda candidate: candidate[:3])
    selected_box = feasible[0][3]
    score = selected_box.score
    item_count = sum(item.quantity for item in items)
    rotation_note = (
        "Rotations were allowed where specified."
        if any(item.allow_rotation for item in items)
        else "All products kept their listed orientation."
    )
    tare_note = (
        f"Empty box weight is {selected_box.tare_weight_kg} kg; estimated "
        f"gross shipment weight is "
        f"{total_weight + selected_box.tare_weight_kg} kg."
        if selected_box.tare_weight_kg is not None
        else "Empty box weight is unknown; gross shipment weight cannot be estimated."
    )
    explanation = (
        f"Fits {item_count} item(s) in {selected_box.name} using deterministic "
        f"corner-point placement. {rotation_note} "
        f"Product weight is {total_weight} kg; box capacity is "
        f"{selected_box.max_weight_kg} kg. {tare_note} "
        f"Box cost is {selected_box.cost}. "
        f"Estimated space utilization is {score}%. Lower-cost feasible boxes "
        "are preferred."
    )
    return Selection(
        box_id=selected_box.box_id,
        score=score,
        explanation=explanation,
        alternatives=tuple(candidate[3] for candidate in feasible[1:]),
    )


def suggest_custom_box(
    items: Sequence[PackingItem],
    clearance_cm: Decimal = Decimal("2"),
    cost: Decimal | None = None,
) -> BoxOption:
    """Build a guaranteed-fit custom box using a simple single-row layout.

    Clearance is added on each side of every item. The resulting internal
    dimensions use one orientation per item and place all units along the
    length axis. This produces a feasible suggestion, not an optimized box.
    """
    _validate_inputs(items, [])
    if (
        not isinstance(clearance_cm, Decimal)
        or not clearance_cm.is_finite()
        or clearance_cm < 0
    ):
        raise ValueError("Clearance must be a finite, non-negative Decimal.")
    if cost is not None and (
        not isinstance(cost, Decimal)
        or not cost.is_finite()
        or cost < 0
    ):
        raise ValueError("Cost must be a finite, non-negative Decimal.")

    unit_dimensions = []
    total_weight = Decimal("0")
    total_volume = Decimal("0")
    for item in items:
        dimensions = (item.length_cm, item.width_cm, item.height_cm)
        if item.allow_rotation:
            dimensions = tuple(sorted(dimensions))
        unit_dimensions.extend([dimensions] * item.quantity)
        total_weight += item.weight_kg * item.quantity
        total_volume += (
            item.length_cm * item.width_cm * item.height_cm * item.quantity
        )

    clearance_per_dimension = clearance_cm * 2
    length_cm = sum(
        (dimensions[0] + clearance_per_dimension for dimensions in unit_dimensions),
        start=Decimal("0"),
    )
    width_cm = max(
        dimensions[1] + clearance_per_dimension
        for dimensions in unit_dimensions
    )
    height_cm = max(
        dimensions[2] + clearance_per_dimension
        for dimensions in unit_dimensions
    )
    box_volume = length_cm * width_cm * height_cm
    score = (total_volume / box_volume * Decimal("100")).quantize(
        Decimal("0.01")
    )
    return BoxOption(
        box_id=0,
        name="Custom suggested box",
        length_cm=length_cm,
        width_cm=width_cm,
        height_cm=height_cm,
        max_weight_kg=max(total_weight, Decimal("0.001")),
        cost=cost,
        score=score,
        tare_weight_kg=None,
    )
