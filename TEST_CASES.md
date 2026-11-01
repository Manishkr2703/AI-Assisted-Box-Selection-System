# Test Cases

The automated tests use Django `TestCase` for database and web behavior and
Django `SimpleTestCase` for the standalone packing algorithm. Run them with:

```powershell
.\.venv\Scripts\python.exe manage.py test box_selection
```

All cases below refer to test methods currently present in the repository.
“Expected result” describes the behavior asserted by that test; passing the
suite is recorded separately in [TEST_OUTPUT.md](./TEST_OUTPUT.md).

## Models and database constraints — `box_selection/tests.py`

| Test method | Expected result |
|---|---|
| `ProductTests.test_product_requires_positive_dimensions_and_weight` | `full_clean()` rejects a zero product dimension. |
| `ProductTests.test_sku_must_be_unique` | `full_clean()` rejects a duplicate SKU. |
| `OrderItemTests.test_order_item_snapshots_product_details_when_created` | An order line keeps its saved product name and dimensions after the catalog product changes; quantity can be updated. |
| `OrderItemTests.test_order_item_quantity_must_be_at_least_one` | `full_clean()` rejects quantity zero. |
| `BoxRecommendationTests.test_recommendation_rejects_scores_above_100` | `full_clean()` rejects a utilization score greater than 100. |
| `BoxRecommendationTests.test_order_has_one_recommendation` | The database uniqueness constraint prevents a second recommendation for one order. |

## Packing algorithm — `box_selection/test_box_selector.py`

| Test method | Expected result |
|---|---|
| `test_single_product_fits_exact_box_dimensions` | A product exactly matching the box dimensions is accepted. |
| `test_selects_box_when_item_fits_after_rotation` | A rotated product fits when rotation is allowed. |
| `test_rotation_can_be_disabled_for_an_item` | The same orientation-dependent fit is rejected when rotation is disabled. |
| `test_multiple_products_fit_when_placed_side_by_side` | Two products can occupy separate, non-overlapping positions. |
| `test_products_touching_box_boundary_are_allowed` | Products touching the box boundary and exact payload capacity are accepted. |
| `test_selects_lowest_cost_feasible_box` | The lowest-cost feasible option is selected. |
| `test_equal_cost_prefers_box_with_less_unused_volume` | Equal-cost choices prefer less unused volume. |
| `test_equal_cost_and_unused_volume_uses_lower_box_id` | Remaining ties resolve deterministically by box ID. |
| `test_reports_box_that_exceeds_weight_capacity` | An overweight order is rejected with a capacity explanation. |
| `test_total_weight_equal_to_capacity_is_allowed` | Payload exactly equal to capacity is accepted. |
| `test_multiple_product_weights_are_summed_before_capacity_check` | Total payload from multiple lines is used for the capacity check. |
| `test_item_dimensions_exceeding_every_box_return_no_selection` | No selection is returned when every box is too small. |
| `test_rejects_items_that_cannot_be_placed_without_overlap` | A configuration that cannot be placed without overlap is rejected. |
| `test_reports_when_no_boxes_are_available` | An empty box catalog returns a no-box result. |
| `test_invalid_decimal_measurements_are_rejected` | Non-finite product measurements such as NaN are rejected. |
| `test_non_positive_and_non_integer_quantities_are_rejected` | Zero, negative, fractional, and Boolean quantities are rejected. |
| `test_zero_and_negative_item_dimensions_are_rejected` | Non-positive item dimensions or weight are rejected. |
| `test_invalid_box_dimensions_and_capacity_are_rejected` | Invalid box dimensions or capacity are rejected. |
| `test_negative_box_cost_is_rejected` | A negative catalog cost is rejected. |
| `test_zero_cost_box_is_valid_and_is_preferred` | Zero cost is valid and ranks ahead of a more expensive feasible box. |
| `test_exact_maximum_item_count_is_supported` | The configured maximum of 100 individual units is supported. |
| `test_custom_box_suggestion_includes_clearance_for_each_item` | Custom suggested dimensions include the specified clearance around each product. |
| `test_custom_box_suggestion_preserves_orientation_when_rotation_disabled` | Custom sizing keeps the listed orientation when rotation is disabled. |
| `test_custom_box_rejects_negative_clearance` | Negative custom-box clearance raises `ValueError`. |
| `test_empty_orders_are_invalid` | An empty order raises `ValueError` in the selector/custom suggestion path. |
| `test_limits_single_box_item_count` | More than 100 individual units is rejected. |

## Orders and service behavior — `box_selection/test_orders.py`

| Test method | Expected result |
|---|---|
| `test_create_order_with_multiple_products_and_display_total_weight` | Multiple product lines and quantities persist; line and total weight display correctly. |
| `test_empty_order_is_rejected` | The order form rejects an empty order and creates no order. |
| `test_zero_and_non_integer_quantities_are_rejected` | The order form rejects zero and fractional quantities. |
| `test_duplicate_products_are_rejected` | Duplicate product lines are rejected by the form. |
| `test_order_views_require_staff` | An unauthenticated user cannot access order pages. |
| `test_empty_order_is_not_created` | The order service rejects an empty list and creates no order. |
| `test_invalid_quantity_is_not_created` | The order service rejects a non-positive quantity and creates no order. |
| `test_boolean_quantity_is_not_created` | The service rejects `True` even though Python treats booleans as integers. |
| `test_duplicate_product_lines_are_rejected` | The service rejects repeated products in one order. |
| `test_get_requires_confirmation_without_deleting_order` | Opening the delete page does not delete the order before confirmation. |
| `test_post_deletes_only_order_history_and_keeps_catalog` | Confirming deletion removes the order, order lines, and recommendation while preserving the product and box. |
| `test_order_history_delete_requires_staff` | Anonymous users cannot delete an order. |

## Recommendation service and dashboard — `box_selection/test_services.py`

| Test method | Expected result |
|---|---|
| `test_saves_recommendation_for_order` | A feasible catalog selection is persisted with the selector version and score. |
| `test_new_box_invalidates_recommendation_and_recalculation_selects_it` | Adding a box invalidates stale recommendations; recalculation can select the cheaper new box. |
| `test_suggests_custom_box_when_catalog_boxes_do_not_fit` | A custom suggestion is persisted when catalog boxes fail; the catalog rejection explanation remains available. |
| `test_suggests_custom_box_when_catalog_is_empty` | An empty catalog yields dimensions with clearance, unpriced cost, unknown tare weight, and no fabricated gross weight. |
| `test_saves_other_feasible_boxes_as_alternatives` | Other feasible catalog options are saved as alternatives. |
| `test_product_rotation_rule_is_used_in_recommendation` | The order-line rotation snapshot is passed into recommendation selection. |
| `test_box_edits_invalidate_existing_recommendations` | Editing a box removes stale saved recommendations. |
| `test_estimated_gross_weight_includes_saved_tare_weight` | Known tare is added to total item weight. |
| `test_requires_order_items` | Requesting a recommendation for an empty order raises `ValueError`. |
| `test_order_detail_can_run_recommendation_and_display_box` | A staff user can request a recommendation and see the selected box and alternatives on the order page. |
| `test_custom_box_suggestion_is_shown_when_catalog_is_empty` | The dashboard displays custom dimensions and the “Not priced” label when the catalog is empty. |
| `test_custom_box_fallback_shown_if_configured_boxes_do_not_fit` | The dashboard displays the custom fallback when configured catalog boxes do not fit. |

## Management pages — `box_selection/test_management.py`

| Test method | Expected result |
|---|---|
| `test_management_pages_require_staff_login` | Anonymous users are redirected to sign in. |
| `test_authenticated_non_staff_user_is_forbidden` | Authenticated non-staff users cannot manage products or boxes. |
| `test_product_list_detail_create_update_and_delete` | Product management pages support the tested CRUD flow. |
| `test_box_list_detail_create_update_and_delete` | Box management pages support the tested CRUD flow. |
| `test_forms_reject_invalid_measurements_capacity_and_cost` | Product/box forms reject invalid dimensions, capacity, and cost. |
| `test_product_used_by_order_cannot_be_deleted` | A product referenced by an order is protected from deletion. |
| `test_box_used_by_recommendation_cannot_be_deleted` | A box referenced by a recommendation is protected from deletion. |

## Sample catalog and seeded-box packing — `box_selection/test_sample_data.py`

| Test method | Expected result |
|---|---|
| `test_seed_command_creates_all_requested_product_details` | All ten sample products have the declared SKU, name, description, category, price, dimensions, and weight. |
| `test_each_of_ten_sample_products_fits_at_least_one_seeded_box` | Each sample product individually has at least one physically feasible catalog box. |
| `test_seed_command_creates_five_boxes_with_requested_specs` | The five sample boxes use the declared dimensions, payload capacities, and costs. |
| `test_seed_command_is_idempotent` | Running the seeder repeatedly leaves exactly ten sample SKUs and five sample box names. |
| `test_multi_product_quantities_create_order_and_recommendation` | Two sample product lines with quantities produce the expected total payload and an automatically saved recommendation. |
