# AI Usage Disclosure

This document describes how AI tools were used to build the **AI-Assisted Box Selection System**. It is based on the **GitHub Copilot chat transcript** of the build (VS Code, Windows), which is included in this repository as [`docs/copilot-chat-transcript.md`](./docs/copilot-chat-transcript.md), and on the project files. The prompts in section 2 are copied from that transcript as written, including typos. Copilot's replies are summarized, not reproduced.

Items marked **[Manish to confirm]** or **[write yourself]** can only be answered by the project owner.

---

## 1. AI tools used

| Tool | Used for |
|---|---|
| **GitHub Copilot (agent mode in VS Code)** | Design discussion, writing and editing code, tests, migrations, templates and CSS. Inside the editor it read and edited project files, ran Django commands in the terminal, ran Pylance syntax and diagnostic checks, drove a Playwright browser for UI checks, and asked multiple-choice questions when a decision was needed. The history also shows it loading a skill named `python-fact-grounded-coding` before coding tasks. The underlying model is not shown in the history. |


The finished application contains **no AI model and calls no AI service**. Box selection is a deterministic Python packing heuristic in `box_selection/algorithms/box_selector.py`.

---

## 2. Prompts given

### 2.1 Copilot prompts, in order

All 36 prompts sent to Copilot are below. Long prompts are in collapsible sections.

**1.**
<details><summary>Requirements analysis</summary>

```text
Act as a senior Python Django developer and software architect. I want to build an AI-Assisted Box Selection System for an e-commerce platform.

Before writing any code, analyze the assignment requirements carefully.

Identify:

1. Functional requirements.
2. Non-functional requirements.
3. Main entities and their relationships.
4. Business rules for selecting shipping boxes.
5. Possible edge cases and limitations.
6. Recommended Django application architecture.
Explain the complete workflow from product creation to order placement and final box recommendation.

Do not generate code yet. Explain your design decisions in simple language so I can understand and defend them in an interview.
```
</details>

**2.**
<details><summary>Database models</summary>

```text
Based on the approved requirements, design Django database models for Product (name, SKU, length, width, height, weight), Box (name, internal dimensions, maximum weight capacity, cost), Order, OrderItem (multiple products and quantities), and a recommendation result if needed. Use suitable field types, relationships, constraints and validations. Explain each design decision and distinguish model validation from business logic. Keep the database simple.
```
</details>

**3.** `implement all this code in my system`

**4.**
<details><summary>Project structure</summary>

```text
Design a clean, maintainable Django project structure for this assignment. Separate responsibilities into appropriate apps, models, views, forms, services, templates and tests. Explain where business logic belongs, how views communicate with services, how to isolate the box selection algorithm, and how to avoid duplication. Show the folder structure first and explain each important file. Assume VS Code on Windows.
```
</details>

**5.** `is all the above is implemented in my system ?`

**6.** `is it necessary currently ? if yes so implement`

**7.**
<details><summary>Product and box management</summary>

```text
Help me implement Product Management and Box Management in Django. Implement add, view, update and delete operations for products and shipping boxes. Validate dimensions, weight and cost, reject zero or negative dimensions and invalid capacities, use Django forms and meaningful errors, and create responsive Bootstrap templates. Work in small steps and explain important code. Avoid unnecessary libraries.
```
</details>

**8.** `Error: Enter a valid username. This value may contain only letters, numbers, and @/./+/-/_ characters`

**9.** `Bypass password validation and create user anyway? [y/N]: `

**10.** `ARNING: This is a development server. Do not use it in a production setting. Use a production WSGI or ASGI server instead.` followed by the Django deployment documentation link (pasted from the terminal; the first letter was cut off when pasted).

**11.** `after that what i have to do`

**12.**
<details><summary>Order management</summary>

```text
Implement Order Management for my Django Box Selection System. An order must support multiple products and quantities. Allow order creation, adding multiple products, specifying quantities, calculating total item weight and displaying order details. Prevent invalid quantities, handle empty orders, and use database transactions where appropriate. Explain Order and OrderItem relationships and provide a practical implementation.
```
</details>

**13.**
<details><summary>Core algorithm</summary>

```text
Design and implement the core shipping box selection algorithm in Python. Accept multiple products and quantities. Consider product dimensions, weights, box internal dimensions and maximum weight. Support allowed product rotations. Check physical placement of multiple products rather than relying only on total volume. Reject overweight boxes and recommend the lowest-cost suitable box. Return an explanation and handle no suitable box. Use a simple understandable 3D packing strategy, document assumptions and limitations, and do not claim a heuristic guarantees optimal packing. Keep the algorithm independent of Django.
```
</details>

**14.**
<details><summary>Recommendation UI</summary>

```text
Build the Django user interface for the box recommendation system. For each selected order, display order ID, products, quantities, total weight, recommended box, dimensions, weight capacity, cost, selection explanation, alternative suitable boxes, and a clear no-suitable-box message. Use Bootstrap for a professional, clean and user-friendly warehouse dashboard.
```
</details>

**15.** `you have created frontend with html css , javascript ? or not`

**16.** `how can i see ui you have made`

**17.** `what is Sku in this`

**18.**
```text
when i am run it shows No suitable box: no shipping boxes are available.

This selector uses a packing heuristic. A failed placement does not prove that no physical arrangement exists; review this order manually or consider additional box sizes.
```

**19.**
<details><summary>QA tests (first request)</summary>

```text
Act as a Python QA engineer. Create comprehensive tests for my Django Box Selection System using Django TestCase or Python unittest where appropriate. Cover a single product fitting, rotation, multiple products, dimensions exceeding all boxes, weight capacity violations, lowest-cost selection, equal-cost tie-breaking, invalid dimensions, empty orders, and no available boxes. Include expected results, boundary cases, negative tests, and explain why each test matters.
```
</details>

**20.** `when i run this  it shows i have to write box details , but i want  box suggestions for products not to write details`

**21.** `how can i run this`

**22.** QA tests, same text as prompt 19, sent a second time.

**23.**
<details><summary>Code review</summary>

```text
Act as a senior Django developer reviewing my actual project code. Identify logical errors in box selection, dimension calculations, weight calculations, Django models and database issues, security vulnerabilities, poor coding practices, missing validations, edge cases and performance problems. Do not rewrite the entire project. Explain each issue and its impact first, then suggest minimal corrections. Never claim code works without supporting tests or execution results.
```
</details>

**24.** `if there is any problem fix that`

**25.**
<details><summary>Documentation review</summary>

```text
Review my completed Django Box Selection System against the original assignment. Help me prepare README.md, AI_USAGE.md, test cases, TEST_OUTPUT.md with actual test execution output, GitHub repository structure, setup instructions, features and known limitations. Do not fabricate test results, AI interactions or verification evidence. Clearly identify information I must write myself, especially the personal learning section and original chat transcript.
```
</details>

**26.** `how can i push this project in my github step by step`

**27.**
<details><summary>Sample data and recommendation system (tables are flattened exactly as pasted)</summary>

```text
Act as a senior Python Django developer. I am building an AI-Assisted Box Selection System for an e-commerce platform.

I want you to add 10 realistic sample products with complete product information and implement an intelligent shipping box recommendation system.

### 1. Create 10 sample products
Add the following products to the database:

ProductLength (cm)Width (cm)Height (cm)Weight (kg)Smartphone16820.20Laptop362531.80Headphones2220100.40Water Bottle28880.50Coffee Mug1210100.35Keyboard451540.80Mouse12740.15Shoes3222121.20Backpack4030150.90Tablet261820.60Each product should also have:

- Unique SKU
- Product name
- Description
- Category
- Price
- Weight
- Length, width and height

### 2. Create sample shipping boxes
Create at least 5 shipping boxes with different internal dimensions, weight capacities and costs.

Use realistic sample values. For example:

BoxLengthWidthHeightMax WeightCostSmall20 cm15 cm10 cm2 kg₹20Medium35 cm25 cm15 cm5 kg₹35Large45 cm35 cm20 cm10 kg₹50Extra Large55 cm40 cm30 cm15 kg₹70Premium65 cm50 cm40 cm25 kg₹100
### 3. Implement intelligent box selection
When an order contains one or multiple products, automatically:

1. Calculate the total order weight, including quantities.
2. Check product dimensions against the internal box dimensions.
3. Allow product rotation where permitted.
4. Check whether all products physically fit inside the box.
5. Reject boxes that exceed maximum weight capacity.
6. Compare the costs of all suitable boxes.
7. Recommend the lowest-cost suitable box.
8. Display alternative suitable boxes.
9. Display a clear message if no box is suitable.
Do not use volume comparison alone to determine whether products fit. Implement a documented 3D packing strategy.

### 4. Recommendation result
For each order, display:

- Order ID
- Products included
- Quantity of each product
- Total product weight
- Recommended box name
- Box dimensions
- Maximum weight capacity
- Actual order weight
- Box cost
- Reason for selecting the box
- Other suitable box options

### 5. Database and implementation

- Use Django models.
- Store products and boxes in the database.
- Create a Django management command or data-seeding mechanism to insert the 10 products and 5 boxes.
- Avoid inserting duplicate sample records when the command is executed multiple times.
- Keep the recommendation algorithm separate from Django views.
- Add appropriate validations and error handling.

### 6. Testing
Test at least:

- All 10 individual products.
- Multiple products in one order.
- Product rotation.
- Weight capacity violations.
- Products that cannot fit in any box.
- Selection of the cheapest suitable box.
- Orders with different quantities.
```
</details>

**28.** `i want to delete this [da5bbadc-5514-497d-80a6-0b61f0a06dc2](http://127.0.0.1:8000/orders/1/) order history only`

**29.** `make ui of this project more attractive, professionally`

**30.** `[Packwise FULFILLMENT WORKSPACE](http://127.0.0.1:8000/products/)[Products](http://127.0.0.1:8000/products/)[Shipping boxes](http://127.0.0.1:8000/boxes/)[Orders](http://127.0.0.1:8000/orders/) in broser ui  it is shown overwritten  please correct it`

**31.** `how can i run`

**32.**
```text
I have a UI bug where text elements are overlapping on top of each other. It looks like an accidental position: absolute or bad margin alignment. Provide a clean CSS fix that resets the positioning to relative or standard block display so the elements respect each other's boundaries."
```

**33.** `why in heading fullfillment Workspace are written in capital and when i click on warehouse section nothing happens`

**34.**
<details><summary>Dashboard redesign brief</summary>

```text
Act as a Senior UI/UX Engineer and Front-End Developer. I need to redesign my warehouse fulfillment dashboard, "Packwise", into a clean, modern, and highly attractive professional web interface using Tailwind CSS and modern UI components (like shadcn/ui or Heroicons). 

Please redesign the page based on these specifications:

1. Layout & Architecture:
- Implement a modern sticky sidebar navigation on the left (instead of the current bottom-right menu). 
- Sidebar items: Dashboard Overview, Orders (Active), Products Management, Shipping Box Configuration, Warehouse Analytics, and Settings. Use minimalist line icons next to text.
- Include a subtle user profile slot and workspace status badge ("● Connected to Local Host") at the bottom of the sidebar.

2. Top Global Navigation / Header:
- A clean top bar featuring a prominent search input (shortcut Cmd+K), a notifications bell icon, and a prominent dark mode toggle.
- Clear breadcrumbs (e.g., Workspace > Orders) to track navigation status.

3. Core Dashboard Content (Orders Workspace):
- A bold header saying "Orders Workspace" with a short subtitle: "Review incoming payloads and intelligent packaging assignments."
- A prominent, highly styled action button for "+ Create New Order" positioned at the top right of the workspace area.
- Metric Cards: Add 3-4 small summary cards at the top of the workspace showing: "Total Pending Orders", "Avg. Weight processed", and "Box Utilization Efficiency %".

4. Professional Data Table (The Core Feature):
- Replace the current list with a robust, perfectly aligned modern data table.
- Table columns: Order ID (shortened with a copy-to-clipboard button), Status (styled as a beautiful pill badge: e.g., amber for 'Draft', green for 'Processed'), Date Created, Items Count, Total Weight (e.g., "0.700 kg"), and Suggested Packaging.
- The "Box Selection" suggestions should use vibrant, distinctive color-coded tags: "Small" (emerald green badge), "Medium" (indigo badge), "Large" (amber/orange badge).
- Actions column: Instead of text buttons for "Delete history", use a subtle trailing three-dot dropdown context menu or a clean trash icon with a tooltip for "Archive/Delete".

5. Visual Aesthetics & Polish:
- Theme: Clean, high-contrast light mode with a soft off-white background (#f8fafc) and crisp white containers with subtle card shadows (shadow-sm).
- Typography: Use a modern, highly readable sans-serif font family (like Inter or Plus Jakarta Sans) with meticulous hierarchical font sizing.
- Alignment & Spacing: Ensure uniform cell padding, explicit column widths, and ample negative space to eliminate visual clutter.

Provide the complete clean, modular frontend component code (React/HTML with Tailwind CSS) that delivers this premium workspace layout.
```
</details>

**35.** `in my project wh orders are drafted or pending`

**36.** `i want orders should be place an option is given for order placement`

### 2.2 Claude prompts

| # | Prompt |
|---|---|
| C1 | `i want like readme.md file as professional software engineer for my project` |
| C2 | Review comments in the editor: fill in the email `krmanish2703@gmail.com`, the GitHub link `https://github.com/Manishkr2703`, and the title `AI-Assisted Box Selection System` |
| C3 | `remove images in top also` and `remove packwise` |
| C4 | The request for `AI_USAGE.md` covering tools, prompts, accepted and rejected output, mistakes, and verification |
| C5 | `use my copilot chat history` (this rewrite) |

---

## 3. Output that was accepted

The history shows these outputs kept and used in the final project:

- **Requirements and design:** the requirements analysis (prompt 1) and the model design (prompt 2): `Product`, `Box`, `Order`, `OrderItem`, `BoxRecommendation`, with `DecimalField`, check constraints, `PROTECT` foreign keys and order-item snapshots.
- **Single-app structure:** asked "is it necessary currently?" (prompt 6), Copilot said separate apps, forms and templates were not necessary yet. The project kept one app, `box_selection`, instead of the separate `catalog`, `packaging` and `orders` apps first proposed.
- **Selector:** deterministic corner-point placement, rotation through six orientations, a weight check, and ranking by cost, then unused volume, then box ID. It returns alternatives and an explanation, and it does not claim optimal packing.
- **CRUD and orders:** staff-only management pages with validation, an inline formset for order lines, a transactional `create_order`, protected deletes, and confirmation-protected order-history deletion (prompt 28).
- **Custom-size fallback:** a suggested box generated from the order when no catalog box is suitable, using the options chosen in Copilot's questions (see section 4).
- **Review fixes (prompt 24):** a per-product rotation setting, optional box tare weight, recommendation invalidation when boxes or order lines change, saved box snapshots on the dashboard, environment-based production settings, and rejecting boolean quantities.
- **Sample data (prompt 27):** a repeat-safe `seed_box_data` command for 10 products and 5 boxes, using the values you supplied.
- **Dashboard (prompts 29 to 34):** the sidebar workspace, short copyable order IDs, dark mode, search shortcut, and an analytics page.
- **Order placement (prompt 36):** a **Place order** action for draft orders.
- **Documents and tests:** 77 tests, `TEST_CASES.md` and `TEST_OUTPUT.md`.

---

## 4. Output that was rejected or modified

**Options you declined.** When Copilot asked how to produce box suggestions without manual box entry (prompt 20), it marked some options as recommended. The transcript records Copilot's questions but not your clicks, so these choices come from Copilot's own summary of your answers:

- It listed "provide standard box sizes and costs to preload" as recommended. You chose automatic custom-size suggestions.
- It recommended 1 cm clearance. You chose 2 cm.
- It recommended showing custom box cost as unknown. You chose to treat it as zero.

That zero-cost choice was later overturned by the review (see below).

**Other changes of direction:**

1. **Zero cost reversed.** The code review (prompt 23) flagged the `0` custom cost as misleading, and the fix (prompt 24) now shows custom suggestions as **not priced**.
2. **Redesign adapted.** Prompt 34 asked for React or HTML with Tailwind. Copilot instead updated the existing Django templates and loaded Tailwind from a CDN. **Settings** is a disabled placeholder.
3. **Behavior added beyond the request.** For prompt 36, Copilot made placement require a saved catalog-box recommendation and blocked custom-size-only suggestions. **[Manish to confirm you want this rule.]**
4. **Navbar fix reworked.** The first fix (prompt 29 follow-up) did not satisfy you. You reported the overlap again (prompt 30), and then asked for a CSS reset (prompt 32). Copilot ended up replacing the collapsible Bootstrap navbar with a flex layout.
5. **Project location.** Copilot first targeted an existing `Smart Box` folder, which then disappeared. After asking you where to work, it built the project in the open `Smart Box Selection System` folder.
6. **Larger structure not built.** The folder structure in prompt 4 (separate apps, `forms.py` per app, templates per app) was not implemented, by Copilot's recommendation.

**[write yourself]** If you personally edited, rewrote or discarded any AI-generated code or text, list it here. The chat history cannot show that.

---

## 5. Mistakes the AI made

Visible in the chat history or caught by testing and review:

- **Insecure defaults.** The first settings used a fixed development secret key and `DEBUG` on by default. The review found this and it was changed to environment variables.
- **Rotation could not be set.** The selector supported "no rotation", but products had no field for it, so every order allowed rotation silently.
- **Misleading cost.** A custom box showed a cost of `0`, which looks like a real price.
- **Stale recommendation data.** The dashboard could show live box values that no longer matched the saved score and explanation.
- **Narrow custom fallback.** It only ran when the catalog was empty, not when every catalog box was too small.
- **Boolean quantity accepted.** `True` passed the integer check in `create_order`.
- **Wrong start address.** Copilot's run instructions said to open `http://127.0.0.1:8000/`, but `box_selection/urls.py` defines no root route. `/orders/` is the working start page.
- **UI bugs shipped.** The navbar text overlapped. Later, browser checks on the redesign found that order IDs were not actually shortened and the mobile layout scrolled sideways.
- **Failing test runs.** Several runs failed after changes (order management, dashboard tests, tare weight, order placement) and needed follow-up edits and extra migrations (`0004` to `0006`).
- **Failed tool calls.** The transcript contains dozens of failed tool results. Several automated patches did not apply, a command used `\.venv\...` without the leading dot, and one used a mistyped `OneDrive\OneDrive` path. Each was retried.
- **Improvised database script.** For the order deletion (prompt 28), Copilot ran a long one-line `manage.py shell` command that opened a transaction by hand. It worked, but a proper script or the new delete view would have been cleaner.
- **Local database side effects.** To check the UI, Copilot created temporary staff accounts (`ui_preview_temporary`, `ui_layout_check`) in your local SQLite database and removed them afterward.

---

## 6. How the final code was verified

Evidence recorded during the work. Full output is in [`TEST_OUTPUT.md`](./TEST_OUTPUT.md).

- **Automated tests.** `python manage.py test box_selection` ran **77 tests, all passing**, in the last recorded run. The count reported by Copilot grew over the session: 6, 16, 23, 31, 34, 37, 48, 53, 56, 60, 65, 68, 72, 77.
- **Django checks.** `python manage.py check` and `python manage.py makemigrations --check --dry-run` reported no problems.
- **Deployment check.** `manage.py check --deploy` was run with production environment variables set.
- **Static checks.** Pylance syntax diagnostics were run on edited Python files.
- **Seeder.** `seed_box_data` was run twice, and a query afterward returned 10 sample products and 5 sample boxes.
- **Browser checks.** The Orders, Products, Shipping Boxes and Analytics pages loaded, and search, the `Ctrl+K` shortcut, dark mode and a mobile-width layout were exercised in a Playwright browser.
- **Order deletion.** The target order was confirmed gone, with product and box counts unchanged.
- **Documents.** A script compared the test names in `TEST_CASES.md` with the real test methods.

