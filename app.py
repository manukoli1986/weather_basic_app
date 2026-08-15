# This application is using color from https://colorhunt.co/

import os
import random
import requests
from collections import OrderedDict
from datetime import datetime
from flask import Flask, render_template, request

app = Flask(__name__)
app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

# API key read from environment. Never hard-code secrets in source.
API_KEY = os.environ.get('OPENWEATHER_API_KEY')
BASE_URL = 'https://api.openweathermap.org/data/2.5/weather'
FORECAST_URL = 'https://api.openweathermap.org/data/2.5/forecast'
DEFAULT_CITY = os.environ.get('DEFAULT_CITY', 'Lucknow')
# Optional: enables a funny weather GIF. If unset, we fall back to an emoji.
GIPHY_API_KEY = os.environ.get('GIPHY_API_KEY')
# Build version, set by CI at image build time (see Dockerfile ARG APP_VERSION).
APP_VERSION = os.environ.get('APP_VERSION', 'dev')

# Quick-pick shortcuts shown as buttons under the search box.
POPULAR_CITIES = ['London', 'New York', 'Tokyo', 'Paris', 'Dubai',
                  'Sydney', 'Mumbai', 'Singapore', 'Delhi', 'Toronto']

# Unit systems. temp symbol + wind label + factor to convert API wind to label.
UNITS = {
    'metric':   {'api': 'metric',   'temp': 'C', 'wind': 'km/h', 'wind_factor': 3.6},
    'imperial': {'api': 'imperial', 'temp': 'F', 'wind': 'mph',  'wind_factor': 1.0},
}

# Fun fallback emoji per weather condition (used when no GIF available).
CONDITION_EMOJI = {
    'Clear': '😎', 'Clouds': '☁️', 'Rain': '🌧️', 'Drizzle': '🌦️',
    'Thunderstorm': '⛈️', 'Snow': '⛄', 'Mist': '🌫️', 'Haze': '🌫️',
    'Fog': '🌫️', 'Smoke': '💨', 'Dust': '🏜️', 'Tornado': '🌪️',
}

# Kid-friendly fun facts, picked at random per weather condition.
FUN_FACTS = {
    'Clear': ["The Sun is so big that 1 million Earths could fit inside it!",
              "Sunlight takes about 8 minutes to reach Earth."],
    'Clouds': ["A single cloud can weigh more than a million kilograms!",
               "Clouds are made of tiny water droplets floating in the air."],
    'Rain': ["Raindrops are not tear-shaped — they look like tiny burgers!",
             "Some raindrops fall at 30 km/h — faster than you can run!"],
    'Drizzle': ["Drizzle drops are so tiny they almost float in the air.",
                "Light drizzle can last for hours without soaking you."],
    'Thunderstorm': ["Lightning is 5 times hotter than the surface of the Sun!",
                     "Thunder is the sound lightning makes when it heats the air."],
    'Snow': ["No two snowflakes are exactly the same!",
             "Snow looks white but ice is actually clear."],
    'Mist': ["Mist and fog are just clouds that touch the ground.",
             "You can walk right through a cloud when it's foggy!"],
}
DEFAULT_FACT = "Weather changes every day — that's what makes it exciting!"


@app.context_processor
def inject_globals():
    return {'app_version': APP_VERSION, 'popular_cities': POPULAR_CITIES}


def temp_mood(temp_c):
    """Kid-friendly cartoon reaction by temperature (Celsius).

    Returns dict: css class (animation), big emoji face, and a fun caption.
    """
    if temp_c <= 0:
        return {'cls': 'freezing', 'face': '🥶',
                'caption': "Brrr! It's freezing — I'm an icicle!"}
    if temp_c <= 12:
        return {'cls': 'cold', 'face': '😨',
                'caption': "So chilly! Grab a warm jacket!"}
    if temp_c <= 22:
        return {'cls': 'nice', 'face': '😄',
                'caption': "Perfect weather — let's play outside!"}
    if temp_c <= 30:
        return {'cls': 'warm', 'face': '😎',
                'caption': "Nice and warm — sunglasses on!"}
    return {'cls': 'hot', 'face': '🥵',
            'caption': "Phew! It's boiling — drink lots of water!"}


def funny_gif(condition):
    """Return a funny GIF URL for the weather condition, or None."""
    if not GIPHY_API_KEY:
        return None
    try:
        resp = requests.get(
            'https://api.giphy.com/v1/gifs/random',
            params={'api_key': GIPHY_API_KEY,
                    'tag': '{} weather funny'.format(condition),
                    'rating': 'g'},
            timeout=10).json()
        return resp['data']['images']['downsized']['url']
    except (requests.RequestException, KeyError):
        return None


def build_forecast(location, units):
    """Fetch the 3-hour forecast once; return dict of daily + hourly views."""
    params = dict(location, appid=API_KEY, units=UNITS[units]['api'])
    try:
        data = requests.get(FORECAST_URL, params=params, timeout=10).json()
    except requests.RequestException:
        return {'daily': [], 'hourly': []}
    if str(data.get('cod')) != '200':
        return {'daily': [], 'hourly': []}

    # Hourly: next 8 slots (~24h) for the temperature graph.
    hourly = []
    for item in data['list'][:8]:
        dt = datetime.utcfromtimestamp(item['dt'])
        hourly.append({
            'label': dt.strftime('%-I%p').lower(),   # e.g. 3pm
            'temp': round(item['main']['temp']),
            'icon': item['weather'][0]['icon'],
        })

    days = OrderedDict()
    for item in data['list']:
        dt = datetime.utcfromtimestamp(item['dt'])
        key = dt.strftime('%Y-%m-%d')
        day = days.setdefault(key, {
            'label': dt.strftime('%a'),
            'min': item['main']['temp_min'],
            'max': item['main']['temp_max'],
            'icon': item['weather'][0]['icon'],
            'description': item['weather'][0]['description'],
            'noon_diff': 24,
        })
        day['min'] = min(day['min'], item['main']['temp_min'])
        day['max'] = max(day['max'], item['main']['temp_max'])
        # Pick the icon/description closest to local noon for that day.
        noon_diff = abs(dt.hour - 12)
        if noon_diff < day['noon_diff']:
            day['noon_diff'] = noon_diff
            day['icon'] = item['weather'][0]['icon']
            day['description'] = item['weather'][0]['description']

    daily = []
    for day in list(days.values())[:6]:
        daily.append({
            'label': day['label'],
            'min': "{:.0f}".format(day['min']),
            'max': "{:.0f}".format(day['max']),
            'icon': day['icon'],
            'description': day['description'],
        })
    return {'daily': daily, 'hourly': hourly}


def dress_character(temp_c, condition_main):
    """Accessories the cartoon 'wears' for the weather. List of (emoji, slot)."""
    items = []
    if temp_c <= 12:
        items.append(('🧣', 'neck'))      # scarf when cold
    if temp_c <= 0:
        items.append(('🧤', 'side'))      # mittens when freezing
    if condition_main in ('Rain', 'Drizzle', 'Thunderstorm'):
        items.append(('☂️', 'top'))       # umbrella when wet
    elif condition_main == 'Snow':
        items.append(('🎿', 'side'))
    elif temp_c > 22:
        items.append(('🕶️', 'eyes'))      # sunglasses when warm/sunny
    if temp_c > 30:
        items.append(('🧢', 'top'))        # cap when hot
    return items


def to_celsius(temp, units):
    """Normalise a temperature to Celsius (mood/dress use Celsius thresholds)."""
    if units == 'imperial':
        return (temp - 32) * 5.0 / 9.0
    return temp


def fetch_weather(location, units, fallback_name=''):
    """Return (weather_dict, error_dict). One is always None.

    location: dict of API location params, e.g. {'q': 'London'} or
              {'lat': 51.5, 'lon': -0.1}.
    """
    if not API_KEY:
        return None, {'city': fallback_name or 'Unknown',
                      'country': 'Server missing OPENWEATHER_API_KEY'}

    params = dict(location, appid=API_KEY, units=UNITS[units]['api'])
    try:
        response = requests.get(BASE_URL, params=params, timeout=10).json()
    except requests.RequestException as exc:
        return None, {'city': fallback_name or 'Unknown', 'country': str(exc)}

    if str(response.get('cod')) != '200':
        return None, {'city': fallback_name or 'that place',
                      'country': response.get('message', 'unknown error')}

    condition = response['weather'][0]
    temp = response['main']['temp']
    temp_c = to_celsius(temp, units)
    unit = UNITS[units]
    weather = {
        'city': response.get('name') or fallback_name,
        'temperature': "{:.1f}".format(temp),
        'temp_symbol': unit['temp'],
        'mood': temp_mood(temp_c),
        'feels_like': "{:.0f}".format(response['main']['feels_like']),
        'humidity': response['main']['humidity'],
        'wind': "{:.0f}".format(response.get('wind', {}).get('speed', 0)
                                * unit['wind_factor']),
        'wind_unit': unit['wind'],
        'description': condition['description'],
        'icon': condition['icon'],
        # 'main' (Clear/Clouds/Rain/Snow...) drives the UI background.
        'main': condition['main'],
        # icon ending 'd' = day, 'n' = night.
        'is_day': condition['icon'].endswith('d'),
        'emoji': CONDITION_EMOJI.get(condition['main'], '🌈'),
        'gif': funny_gif(condition['main']),
        'accessories': dress_character(temp_c, condition['main']),
        'fact': random.choice(FUN_FACTS.get(condition['main'], [DEFAULT_FACT])),
    }
    return weather, None


@app.route('/', methods=['GET', 'POST'])
def index():
    src = request.form if request.method == 'POST' else request.args
    units = src.get('units', 'metric')
    if units not in UNITS:
        units = 'metric'

    # Location: prefer browser coordinates, else a typed/quick-pick city.
    lat, lon = src.get('lat'), src.get('lon')
    city_name = (src.get('city') or '').strip()
    if lat and lon:
        location = {'lat': lat, 'lon': lon}
    elif city_name:
        location = {'q': city_name.upper()}
    else:
        location = {'q': DEFAULT_CITY}
        city_name = DEFAULT_CITY

    weather, error = fetch_weather(location, units, fallback_name=city_name)
    if error:
        return render_template('index.html', weather_error=error, units=units)
    forecast = build_forecast(location, units)
    return render_template('index.html', weather=weather, units=units,
                           forecast=forecast['daily'], hourly=forecast['hourly'])


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
