"""Unit tests for agent tools."""

import pytest

from adk_a2a.domain.exceptions import ToolExecutionError
from adk_a2a.tools.calculator import calculate
from adk_a2a.tools.weather import get_city_weather


def test_calculate_valid_expressions() -> None:
    """Tests arithmetic evaluations."""
    assert calculate("2 + 3").result == 5.0
    assert calculate("10 * 5 - 2").result == 48.0
    assert calculate("20 / 4").result == 5.0
    assert calculate("2 ** 3").result == 8.0
    assert calculate("-5 + 10").result == 5.0


def test_calculate_invalid_expression() -> None:
    """Tests calculator error handling on invalid or dangerous input."""
    with pytest.raises(ToolExecutionError):
        calculate("import os; os.system('ls')")

    with pytest.raises(ToolExecutionError):
        calculate("")


def test_get_city_weather_catalog() -> None:
    """Tests retrieval from pre-configured catalog cities."""
    tokyo = get_city_weather("Tokyo")
    assert tokyo.city == "Tokyo"
    assert tokyo.temperature_celsius == 18.5
    assert tokyo.condition == "Clear"


def test_get_city_weather_fallback() -> None:
    """Tests fallback weather generation for arbitrary city."""
    berlin = get_city_weather("Berlin")
    assert berlin.city == "Berlin"
    assert berlin.temperature_celsius == 20.0


def test_get_city_weather_empty() -> None:
    """Tests error on empty city name."""
    with pytest.raises(ToolExecutionError):
        get_city_weather("")
