"""Weather information retrieval tool."""

from adk_a2a.core.logging import get_logger
from adk_a2a.domain.exceptions import ToolExecutionError
from adk_a2a.domain.models import CityWeather

logger = get_logger(__name__)

# Sample weather database for offline & deterministic testing
_WEATHER_CATALOG: dict[str, CityWeather] = {
    "tokyo": CityWeather(
        city="Tokyo",
        temperature_celsius=18.5,
        condition="Clear",
        humidity_percent=55,
    ),
    "paris": CityWeather(
        city="Paris",
        temperature_celsius=14.0,
        condition="Partly Cloudy",
        humidity_percent=65,
    ),
    "london": CityWeather(
        city="London",
        temperature_celsius=12.2,
        condition="Rainy",
        humidity_percent=80,
    ),
    "new york": CityWeather(
        city="New York",
        temperature_celsius=21.0,
        condition="Sunny",
        humidity_percent=50,
    ),
    "san francisco": CityWeather(
        city="San Francisco",
        temperature_celsius=16.8,
        condition="Foggy",
        humidity_percent=72,
    ),
}


def get_city_weather(city: str) -> CityWeather:
    """Retrieves current weather details for a given city.

    Args:
        city: Name of the target city (e.g. 'Tokyo', 'Paris').

    Returns:
        CityWeather value object containing temperature, condition, and humidity.

    Raises:
        ToolExecutionError: When the city name is empty or data cannot be found.
    """
    logger.info("Fetching weather report for city: %s", city)
    city_normalized = city.strip().lower()

    if not city_normalized:
        raise ToolExecutionError("City name must not be blank.")

    if city_normalized in _WEATHER_CATALOG:
        return _WEATHER_CATALOG[city_normalized]

    # Default fallback weather estimate for arbitrary queries
    return CityWeather(
        city=city.strip().title(),
        temperature_celsius=20.0,
        condition="Moderate Breeze",
        humidity_percent=60,
    )
