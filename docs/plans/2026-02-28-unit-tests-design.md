# Unit Tests Design — norm-inventory

**Date:** 2026-02-28

## Purpose

`convert.py` has no tests. This document describes a unit test suite using **pytest** that covers all meaningful functions in the script without testing the `main()` orchestration layer.

## Structure

```
tests/
  __init__.py               empty
  test_convert.py           all unit tests
  fixtures/
    sample.csv              small synthetic CSV (~10 rows, covers edge cases)
```

The fixture CSV uses the same column format as the real input files but has a small, controlled set of rows designed to exercise every filter condition.

## Test Cases

### `validate_filename(filename)`
- Valid path string → returns `pathlib.Path`
- Empty string → raises `Exception`

### `extract_run_date(inventory_file)`
- Valid filename prefix `202503120915.csv` → `"Thursday March 12 2025 09:15AM"`
- Non-date filename prefix → `""` (empty string, no crash)

### `validate_row(row)`
- Normal valid row → `True`
- Header row (`manufacturer='BRAND'`, `style='DESCRIP'`) → `False`
- Row with missing field (`## MISSING FIELD ##`) → `False`
- Row with extraneous extra column → `True` (warning printed, row still valid)

### `keep_row(row)` — uses `monkeypatch` to freeze `_SIX_MONTHS_AGO`
- Recently-updated item, qty > 1, normal size/category → `True`
- Item updated > 180 days ago → `False`
- Single-serve size `.355L` → `False`
- Single-serve size `.473L` → `False`
- Single-serve size `32OZ` → `False`
- Single-serve size `64OZ` → `False`
- Single-serve size `64 OZ` → `False`
- Category containing `ACCESS` → `False`
- Quantity = 1 → `False`
- Quantity = 0 → `False`
- Invalid quantity string → raises `Exception`

### `new_item(row)`
- Input `OrderedDict` → output is a plain `dict` with identical keys/values

### `write_json_inventory(filename, json_inventory)` — uses `tmp_path`
- File is created and contains valid JSON
- JSON has `report_run_date` and `inventory` keys
- Items match input data

### `write_html_inventory(filename, json_inventory)` — uses `tmp_path`
- File is created
- `<H1>` tags present for each category in the input
- Beer/Wine/Cider categories appear before other categories
- `ACCESS` categories are absent from output
- Line items match format: `MANUFACTURER STYLE (SIZE) $PRICE -- Qty: QUANTITY`

### `read_csv_report(inventory_file)` — uses fixture CSV + `tmp_path`
- Returns dict with `report_run_date` (string) and `inventory` (list)
- Header row excluded from inventory
- Items filtered by age, size, category, quantity
- Raises if file doesn't exist

## Tools / Dependencies

- **pytest** — test runner and fixtures (`tmp_path`, `monkeypatch`)
- No additional libraries needed (project uses stdlib only)
- Install: `pip install pytest`

## Verification

```bash
pip install pytest
pytest tests/ -v
```

All tests should pass. Coverage can be checked with:
```bash
pip install pytest-cov
pytest tests/ --cov=convert --cov-report=term-missing
```
