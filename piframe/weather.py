from dataclasses import dataclass
from typing import Optional

import requests

WEATHER_CODE_MAPPING = {
    0: "Clear",
    1: "Mostly Clear",
    2: "Partly Cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Icy Fog",
    51: "Light Drizzle",
    53: "Drizzle",
    55: "Heavy Drizzle",
    80: "Light Showers",
    81: "Showers",
    82: "Heavy Showers",
    61: "Light Rain",
    63: "Rain",
    65: "Heavy Rain",
    56: "Light Freezing Drizzle",
    57: "Freezing Drizzle",
    66: "Light Freezing Rain",
    67: "Freezing Rain",
    71: "Light Snow",
    73: "Snow",
    75: "Heavy Snow",
    77: "Snow Grains",
    85: "Light Snow Showers",
    86: "Snow Showers",
    95: "Thunderstorm",
    96: "Light Thunderstorm w/ Hail",
    99: "Thunderstorm w/ Hail",
}


@dataclass
class Weather:
    temperature: float
    description: str


def get_current_weather() -> Optional[Weather]:
    # SF
    url = f"https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 37.790812,
        "longitude": -122.418431,
        "current_weather": "true",
        "temperature_unit": "fahrenheit",
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        current_weather = data.get("current_weather", {})
        temperature = current_weather["temperature"]
        weather_code = current_weather.get("weathercode")
        description = WEATHER_CODE_MAPPING.get(weather_code)
        return Weather(
            temperature=temperature,
            description=description,
        )
