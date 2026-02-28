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
