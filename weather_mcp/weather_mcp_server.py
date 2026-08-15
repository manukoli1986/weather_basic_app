"""MCP server for the weather app.

Exposes OpenWeatherMap data as MCP tools + a resource so any MCP client
(Claude Code, Claude Desktop) can fetch weather.

Run locally:
    export OPENWEATHER_API_KEY=<key>
    python weather_mcp_server.py
"""

import os
import requests
from mcp.server.mcpserver import MCPServer

mcp = MCPServer("weather")

API_KEY = os.environ.get("OPENWEATHER_API_KEY")
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"


def _fetch(url, city):
    """Call OpenWeather. Return (data, error) — one is always None."""
    if not API_KEY:
        return None, "OPENWEATHER_API_KEY not set on the server"
    params = {"q": city, "appid": API_KEY, "units": "metric"}
    try:
        data = requests.get(url, params=params, timeout=10).json()
    except requests.RequestException as exc:
        return None, str(exc)
    if str(data.get("cod")) != "200":
        return None, data.get("message", "unknown error")
    return data, None


@mcp.tool()
def get_weather(city: str) -> dict:
    """Get the current weather for a city.

    Args:
        city: City name, e.g. "London" or "Mumbai".

    Returns temperature (Celsius), description, condition and humidity.
    """
    data, error = _fetch(BASE_URL, city)
    if error:
        return {"error": error, "city": city}
    return {
        "city": city,
        "temperature_c": data["main"]["temp"],
        "feels_like_c": data["main"]["feels_like"],
        "humidity_pct": data["main"]["humidity"],
        "description": data["weather"][0]["description"],
        "condition": data["weather"][0]["main"],
        "wind_speed_ms": data.get("wind", {}).get("speed"),
    }


@mcp.tool()
def get_forecast(city: str, slots: int = 5) -> dict:
    """Get a short weather forecast for a city (3-hour steps).

    Args:
        city: City name.
        slots: How many 3-hour steps to return (1-10). 5 = ~15 hours ahead.
    """
    slots = max(1, min(slots, 10))
    data, error = _fetch(FORECAST_URL, city)
    if error:
        return {"error": error, "city": city}
    steps = [
        {
            "time": item["dt_txt"],
            "temperature_c": item["main"]["temp"],
            "description": item["weather"][0]["description"],
        }
        for item in data["list"][:slots]
    ]
    return {"city": city, "forecast": steps}


@mcp.resource("weather://{city}/current")
def current_weather_resource(city: str) -> str:
    """Readable resource: current weather as a short text line."""
    w = get_weather(city)
    if "error" in w:
        return f"Weather for {city}: error — {w['error']}"
    return (f"{city}: {w['temperature_c']}°C, {w['description']}, "
            f"humidity {w['humidity_pct']}%")


if __name__ == "__main__":
    mcp.run()  # stdio transport
