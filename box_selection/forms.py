from django import forms
from django.forms import BaseInlineFormSet, inlineformset_factory

from .models import Box, Order, OrderItem, Product


class BootstrapModelForm(forms.ModelForm):
    dimension_fields = ()
    positive_fields = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs["class"] = (
                "form-check-input"
                if isinstance(field.widget, forms.CheckboxInput)
                else "form-control"
            )
            field.widget.attrs["id"] = f"id_{name}"
            if name in self.dimension_fields:
                field.widget.attrs.update({"min": "0.01", "step": "0.01"})
            elif name in self.positive_fields:
                field.widget.attrs.update({"min": "0.001", "step": "0.001"})
            elif name == "cost":
                field.widget.attrs.update({"min": "0", "step": "0.01"})
            elif name == "tare_weight_kg":
                field.widget.attrs.update({"min": "0", "step": "0.001"})

        for name in self.dimension_fields + self.positive_fields:
            self.fields[name].error_messages["min_value"] = (
                "Enter a value greater than zero."
            )
        for name in ("cost", "tare_weight_kg"):
            if name in self.fields:
                self.fields[name].error_messages["min_value"] = (
                    "Enter a non-negative value."
                )


class ProductForm(BootstrapModelForm):
    dimension_fields = ("length_cm", "width_cm", "height_cm")
    positive_fields = ("weight_kg",)

    class Meta:
        model = Product
        fields = (
            "name",
            "sku",
            "description",
            "category",
            "price",
            "length_cm",
            "width_cm",
            "height_cm",
            "weight_kg",
            "allow_rotation",
        )
        help_texts = {
            "length_cm": "Product length in centimetres.",
            "width_cm": "Product width in centimetres.",
            "height_cm": "Product height in centimetres.",
            "weight_kg": "Product weight in kilograms.",
            "price": "Product price in Indian rupees (INR).",
            "allow_rotation": (
                "Enable if this product may be rotated during packing."
            ),
        }


class BoxForm(BootstrapModelForm):
    dimension_fields = (
        "inner_length_cm",
        "inner_width_cm",
        "inner_height_cm",
    )
    positive_fields = ("max_weight_kg",)

    class Meta:
        model = Box
        fields = (
            "name",
            "inner_length_cm",
            "inner_width_cm",
            "inner_height_cm",
            "max_weight_kg",
            "tare_weight_kg",
            "cost",
        )
        help_texts = {
            "inner_length_cm": "Usable internal length in centimetres.",
            "inner_width_cm": "Usable internal width in centimetres.",
            "inner_height_cm": "Usable internal height in centimetres.",
            "max_weight_kg": "Maximum contents weight in kilograms.",
            "tare_weight_kg": "Optional empty-box weight in kilograms; leave blank if unknown.",
            "cost": "Packaging material cost; zero is allowed.",
        }


class OrderItemForm(forms.ModelForm):
    quantity = forms.IntegerField(
        min_value=1,
        error_messages={
            "min_value": "Quantity must be at least 1.",
            "invalid": "Enter a whole-number quantity.",
        },
        widget=forms.NumberInput(
            attrs={"class": "form-control", "min": "1", "step": "1"}
        ),
    )

    class Meta:
        model = OrderItem
        fields = ("product", "quantity")
        widgets = {
            "product": forms.Select(attrs={"class": "form-select"}),
        }


class BaseOrderItemFormSet(BaseInlineFormSet):
    default_error_messages = {
        **BaseInlineFormSet.default_error_messages,
        "too_few_forms": "Add at least one product to the order.",
    }

    def validate_unique(self):
        # Duplicate products are reported on the relevant product fields below.
        return

    def clean(self):
        super().clean()
        if any(self.errors):
            return

        seen_products = set()
        for form in self.forms:
            if not form.cleaned_data:
                continue
            product = form.cleaned_data.get("product")
            if product is None:
                continue
            if product.pk in seen_products:
                form.add_error(
                    "product",
                    "Choose each product only once per order.",
                )
            seen_products.add(product.pk)


OrderItemFormSet = inlineformset_factory(
    Order,
    OrderItem,
    form=OrderItemForm,
    formset=BaseOrderItemFormSet,
    extra=1,
    min_num=1,
    validate_min=True,
    can_delete=False,
)
