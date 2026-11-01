import uuid
from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, transaction
from django.db.models import Q


class Product(models.Model):
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=64, unique=True)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=100, default="General")
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0"))],
    )
    length_cm = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    width_cm = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    height_cm = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    weight_kg = models.DecimalField(
        max_digits=9,
        decimal_places=3,
        validators=[MinValueValidator(Decimal("0.001"))],
    )
    allow_rotation = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(price__gte=0),
                name="product_price_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(length_cm__gt=0),
                name="product_length_positive",
            ),
            models.CheckConstraint(
                condition=Q(width_cm__gt=0),
                name="product_width_positive",
            ),
            models.CheckConstraint(
                condition=Q(height_cm__gt=0),
                name="product_height_positive",
            ),
            models.CheckConstraint(
                condition=Q(weight_kg__gt=0),
                name="product_weight_positive",
            ),
        ]
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.sku})"


class Box(models.Model):
    name = models.CharField(max_length=100)
    inner_length_cm = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    inner_width_cm = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    inner_height_cm = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    max_weight_kg = models.DecimalField(
        max_digits=9,
        decimal_places=3,
        validators=[MinValueValidator(Decimal("0.001"))],
    )
    tare_weight_kg = models.DecimalField(
        max_digits=9,
        decimal_places=3,
        null=True,
        default=None,
        blank=True,
        validators=[MinValueValidator(Decimal("0"))],
        help_text="Optional empty-box weight in kilograms.",
    )
    cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(inner_length_cm__gt=0),
                name="box_length_positive",
            ),
            models.CheckConstraint(
                condition=Q(inner_width_cm__gt=0),
                name="box_width_positive",
            ),
            models.CheckConstraint(
                condition=Q(inner_height_cm__gt=0),
                name="box_height_positive",
            ),
            models.CheckConstraint(
                condition=Q(max_weight_kg__gt=0),
                name="box_capacity_positive",
            ),
            models.CheckConstraint(
                condition=(
                    Q(tare_weight_kg__isnull=True)
                    | Q(tare_weight_kg__gte=0)
                ),
                name="box_tare_weight_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(cost__gte=0),
                name="box_cost_nonnegative",
            ),
        ]
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        invalidate_recommendations = self._state.adding
        if not invalidate_recommendations and self.pk is not None:
            previous = type(self).objects.filter(pk=self.pk).values(
                "name",
                "inner_length_cm",
                "inner_width_cm",
                "inner_height_cm",
                "max_weight_kg",
                "tare_weight_kg",
                "cost",
            ).first()
            update_fields = kwargs.get("update_fields")
            invalidate_recommendations = previous is not None and any(
                (update_fields is None or field in update_fields)
                and previous[field] != getattr(self, field)
                for field in previous
            )

        with transaction.atomic():
            super().save(*args, **kwargs)
            if invalidate_recommendations:
                BoxRecommendation.objects.all().delete()

    def delete(self, *args, **kwargs):
        if self.pk is not None and BoxRecommendation.objects.filter(
            box_id=self.pk
        ).exists():
            return super().delete(*args, **kwargs)

        with transaction.atomic():
            BoxRecommendation.objects.all().delete()
            return super().delete(*args, **kwargs)


class Order(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PLACED = "placed", "Placed"
        CANCELLED = "cancelled", "Cancelled"

    number = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def total_item_weight(self):
        return sum(
            (
                item.weight_kg * item.quantity
                for item in self.items.all()
            ),
            start=Decimal("0.000"),
        )

    @property
    def total_item_count(self):
        return sum(item.quantity for item in self.items.all())

    def __str__(self):
        return str(self.number)


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="order_items",
    )
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
    )
    product_name = models.CharField(max_length=200, editable=False)
    sku = models.CharField(max_length=64, editable=False)
    length_cm = models.DecimalField(max_digits=9, decimal_places=2, editable=False)
    width_cm = models.DecimalField(max_digits=9, decimal_places=2, editable=False)
    height_cm = models.DecimalField(max_digits=9, decimal_places=2, editable=False)
    weight_kg = models.DecimalField(max_digits=9, decimal_places=3, editable=False)
    allow_rotation = models.BooleanField(default=True, editable=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["order", "product"],
                name="one_line_per_product_per_order",
            ),
            models.CheckConstraint(
                condition=Q(quantity__gte=1),
                name="order_item_quantity_positive",
            ),
        ]

    def save(self, *args, **kwargs):
        snapshot_product = self._state.adding
        previous_order_id = None
        if not snapshot_product:
            previous = (
                type(self)
                .objects.filter(pk=self.pk)
                .values("product_id", "order_id")
                .first()
            )
            if previous is not None:
                snapshot_product = previous["product_id"] != self.product_id
                previous_order_id = previous["order_id"]

        if snapshot_product:
            self.product_name = self.product.name
            self.sku = self.product.sku
            self.length_cm = self.product.length_cm
            self.width_cm = self.product.width_cm
            self.height_cm = self.product.height_cm
            self.weight_kg = self.product.weight_kg
            self.allow_rotation = self.product.allow_rotation
            if kwargs.get("update_fields") is not None:
                kwargs["update_fields"] = set(kwargs["update_fields"]) | {
                    "product_name",
                    "sku",
                    "length_cm",
                    "width_cm",
                    "height_cm",
                    "weight_kg",
                    "allow_rotation",
                }
        with transaction.atomic():
            super().save(*args, **kwargs)
            affected_order_ids = {self.order_id}
            if previous_order_id is not None:
                affected_order_ids.add(previous_order_id)
            BoxRecommendation.objects.filter(
                order_id__in=affected_order_ids
            ).delete()

    def delete(self, *args, **kwargs):
        order_id = self.order_id
        with transaction.atomic():
            result = super().delete(*args, **kwargs)
            BoxRecommendation.objects.filter(order_id=order_id).delete()
            return result

    def __str__(self):
        return f"{self.product_name} x {self.quantity}"

    @property
    def line_weight(self):
        return self.weight_kg * self.quantity


class BoxRecommendation(models.Model):
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name="box_recommendation",
    )
    box = models.ForeignKey(
        Box,
        on_delete=models.PROTECT,
        related_name="recommendations",
        null=True,
        blank=True,
    )
    selected_box = models.JSONField(default=dict, blank=True)
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(Decimal("0")),
            MaxValueValidator(Decimal("100")),
        ],
    )
    explanation = models.TextField(blank=True)
    alternatives = models.JSONField(default=list, blank=True)
    algorithm_version = models.CharField(max_length=32)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(score__isnull=True)
                    | Q(score__gte=0, score__lte=100)
                ),
                name="recommendation_score_between_0_and_100",
            ),
        ]

    def __str__(self):
        return f"Box recommendation for {self.order}"

    @property
    def estimated_gross_weight_kg(self):
        if "tare_weight_kg" in self.selected_box:
            tare_weight_value = self.selected_box["tare_weight_kg"]
        elif self.box_id is not None:
            tare_weight_value = self.box.tare_weight_kg
        else:
            return None
        if tare_weight_value is None:
            return None
        tare_weight = Decimal(str(tare_weight_value))
        return self.order.total_item_weight + tare_weight
