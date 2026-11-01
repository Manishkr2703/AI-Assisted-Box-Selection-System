# Test Execution Record

This record contains output captured from actual command executions in the
project workspace. It is not a predicted or synthesized test result.

## Environment recorded for this run

- Python: `3.14.8`
- Django: `6.1.2`
- Database configured by the project: SQLite

## Django application test suite

Command:

```powershell
.\.venv\Scripts\python.exe manage.py test box_selection
```

Captured output:

```text
Creating test database for alias 'default'...
.............................................................................
----------------------------------------------------------------------
Ran 77 tests in 19.243s

OK
Destroying test database for alias 'default'...
Found 77 test(s).
System check identified no issues (0 silenced).
```

The order placement tests verify that a staff member can place a draft with a
suitable catalog box, custom-size-only recommendations are rejected, GET is
not allowed for the state change, repeated placement is rejected, and the
placement action appears in both order views.

## Django system check and migration drift check

Commands:

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
```

Captured output:

```text
System check identified no issues (0 silenced).
No changes detected
```

## Browser smoke check

The local dashboard was opened in the integrated browser at desktop and mobile
viewport sizes. The Orders, Products, Shipping Boxes, and Warehouse Analytics
routes returned HTTP 200. The browser check also verified that Ctrl+K focuses
the order search, a non-matching query hides order rows, the dark-mode toggle
works, and the mobile table and navigation retain their own horizontal
scrolling without exposing page-level horizontal overflow.

## Sample data command

The seeding command was run twice against the configured local SQLite database:

```powershell
.\.venv\Scripts\python.exe manage.py seed_box_data
.\.venv\Scripts\python.exe manage.py seed_box_data
```

Captured command output:

```text
Seeded 10 products and 5 shipping boxes.
Seeded 10 products and 5 shipping boxes.
```

A database query after those runs returned:

```text
sample_products= 10
sample_boxes= 5
missing_descriptions= 0
```

## What this output does and does not establish

It establishes that the listed test command completed successfully with 72
tests in this workspace, the standard Django system check reported no issues,
and Django reported no model changes needing a migration at the time of the
check. The seeder was also executed twice and the listed sample records were
present afterward. The browser smoke check verifies the specific routes and
interactions described above in the local browser.

It does not establish production deployment readiness, behavior on another
database or Python version, cross-browser compatibility, or performance under
load. The browser reported that the Tailwind CDN is intended for development;
production should use compiled Tailwind assets. No human manual test is
claimed here. Re-run the commands after changing the code; replace this record
with the new captured output if results change.
