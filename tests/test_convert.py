import pathlib
import json
import pytest
import convert


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_row(mfg='BUD LIGHT', style='LAGER CANS', category='BEER-DOMESTIC',
             size='24PK', price='25.9900', qty='5', last_updated='20260101',
             row_num='1'):
    """Return a plain dict that looks like a DictReader row."""
    return {
        'manufacturer': mfg,
        'style': style,
        'category': category,
        'size': size,
        'price': price,
        'quantity': qty,
        'last_updated': last_updated,
        'row_number': row_num,
    }


# ---------------------------------------------------------------------------
# validate_filename
# ---------------------------------------------------------------------------

def test_validate_filename_returns_path():
    result = convert.validate_filename('inventory.csv')
    assert result == pathlib.Path('inventory.csv')


def test_validate_filename_raises_on_empty_string():
    with pytest.raises(Exception):
        convert.validate_filename('')


# ---------------------------------------------------------------------------
# extract_run_date
# ---------------------------------------------------------------------------

def test_extract_run_date_valid_filename():
    p = pathlib.Path('202503120915.csv')
    result = convert.extract_run_date(p)
    assert result == 'Wednesday March 12 2025 09:15AM'


def test_extract_run_date_non_date_filename():
    p = pathlib.Path('inventory.csv')
    result = convert.extract_run_date(p)
    assert result == ''

# ---------------------------------------------------------------------------
# validate_row
# ---------------------------------------------------------------------------

def test_validate_row_valid():
    row = make_row()
    assert convert.validate_row(row) is True


def test_validate_row_header_row():
    row = make_row(mfg='BRAND', style='DESCRIP')
    assert convert.validate_row(row) is False


def test_validate_row_missing_field():
    row = make_row(price='## MISSING FIELD ##')
    assert convert.validate_row(row) is False


def test_validate_row_extraneous_field_still_valid(capsys):
    row = make_row()
    row['extraneous'] = ['extra_value']
    result = convert.validate_row(row)
    assert result is True
    captured = capsys.readouterr()
    assert 'too many fields' in captured.out

# ---------------------------------------------------------------------------
# keep_row
# ---------------------------------------------------------------------------

def test_keep_row_valid_item(monkeypatch):
    monkeypatch.setattr(convert, '_SIX_MONTHS_AGO', '20250101')
    row = make_row()  # last_updated='20260101', qty='5'
    assert convert.keep_row(row) is True


def test_keep_row_old_item(monkeypatch):
    monkeypatch.setattr(convert, '_SIX_MONTHS_AGO', '20250101')
    row = make_row(last_updated='20200101')
    assert convert.keep_row(row) is False


def test_keep_row_excludes_355L(monkeypatch):
    monkeypatch.setattr(convert, '_SIX_MONTHS_AGO', '20250101')
    row = make_row(size='.355L')
    assert convert.keep_row(row) is False


def test_keep_row_excludes_473L(monkeypatch):
    monkeypatch.setattr(convert, '_SIX_MONTHS_AGO', '20250101')
    row = make_row(size='.473L')
    assert convert.keep_row(row) is False


def test_keep_row_excludes_32oz(monkeypatch):
    monkeypatch.setattr(convert, '_SIX_MONTHS_AGO', '20250101')
    row = make_row(size='32OZ')
    assert convert.keep_row(row) is False


def test_keep_row_excludes_64oz(monkeypatch):
    monkeypatch.setattr(convert, '_SIX_MONTHS_AGO', '20250101')
    row = make_row(size='64OZ')
    assert convert.keep_row(row) is False


def test_keep_row_excludes_64_oz_with_space(monkeypatch):
    monkeypatch.setattr(convert, '_SIX_MONTHS_AGO', '20250101')
    row = make_row(size='64 OZ')
    assert convert.keep_row(row) is False


def test_keep_row_excludes_accessory_category(monkeypatch):
    monkeypatch.setattr(convert, '_SIX_MONTHS_AGO', '20250101')
    row = make_row(category='ACCESS-GIFTS')
    assert convert.keep_row(row) is False


def test_keep_row_excludes_qty_one(monkeypatch):
    monkeypatch.setattr(convert, '_SIX_MONTHS_AGO', '20250101')
    row = make_row(qty='1')
    assert convert.keep_row(row) is False


def test_keep_row_excludes_qty_zero(monkeypatch):
    monkeypatch.setattr(convert, '_SIX_MONTHS_AGO', '20250101')
    row = make_row(qty='0')
    assert convert.keep_row(row) is False


def test_keep_row_excludes_empty_qty(monkeypatch):
    monkeypatch.setattr(convert, '_SIX_MONTHS_AGO', '20250101')
    row = make_row(qty='')
    assert convert.keep_row(row) is False


def test_keep_row_invalid_qty_returns_false(monkeypatch):
    monkeypatch.setattr(convert, '_SIX_MONTHS_AGO', '20250101')
    row = make_row(qty='not-a-number')
    assert convert.keep_row(row) is False


# ---------------------------------------------------------------------------
# new_item
# ---------------------------------------------------------------------------

def test_new_item_returns_plain_dict():
    from collections import OrderedDict
    row = OrderedDict(make_row())
    result = convert.new_item(row)
    assert isinstance(result, dict)
    assert result['manufacturer'] == 'BUD LIGHT'
    assert result['quantity'] == '5'


# ---------------------------------------------------------------------------
# write_json_inventory
# ---------------------------------------------------------------------------

def test_write_json_inventory_creates_file(tmp_path):
    out = tmp_path / 'inventory.json'
    data = {'report_run_date': 'Today', 'inventory': [make_row()]}
    convert.write_json_inventory(out, data)
    assert out.exists()


def test_write_json_inventory_valid_json(tmp_path):
    out = tmp_path / 'inventory.json'
    data = {
        'report_run_date': 'Wednesday March 12 2025 09:15AM',
        'inventory': [make_row()],
    }
    convert.write_json_inventory(out, data)
    parsed = json.loads(out.read_text())
    assert parsed['report_run_date'] == 'Wednesday March 12 2025 09:15AM'
    assert len(parsed['inventory']) == 1
    assert parsed['inventory'][0]['manufacturer'] == 'BUD LIGHT'
