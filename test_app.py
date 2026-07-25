import pytest
from app import calculate_discount


def test_calculate_discount_valid():
    """Test standard discount calculation."""
    result = calculate_discount(100, 20)
    assert result == 80.0


def test_calculate_discount_zero():
    """Test 0% discount."""
    result = calculate_discount(50, 0)
    assert result == 50.0


def test_calculate_discount_negative_input():
    """Test that negative inputs raise ValueError."""
    with pytest.raises(ValueError):
        calculate_discount(-10, 10)