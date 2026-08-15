# This application is using color from https://colorhunt.co/

import os
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

# Fun fallback emoji per weather condition (used when no GIF available).
CONDITION_EMOJI = {
    'Clear': '😎', 'Clouds': '☁️', 'Rain': '🌧️', 'Drizzle': '🌦️',
    'Thunderstorm': '⛈️', 'Snow': '⛄', 'Mist': '🌫️', 'Haze': '🌫️',
    'Fog': '🌫️', 'Smoke': '💨', 'Dust': '🏜️', 'Tornado': '🌪️',
}


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


def build_forecast(city_name):
    """Aggregate the 3-hour forecast into per-day min/max + condition."""
    params = {'q': city_name, 'appid': API_KEY, 'units': 'metric'}
    try:
        data = requests.get(FORECAST_URL, params=params, timeout=10).json()
    except requests.RequestException:
        return []
    if str(data.get('cod')) != '200':
        return []

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

    forecast = []
    for day in list(days.values())[:6]:
        forecast.append({
            'label': day['label'],
            'min': "{:.0f}".format(day['min']),
            'max': "{:.0f}".format(day['max']),
            'icon': day['icon'],
            'description': day['description'],
        })
    return forecast


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


def fetch_weather(city_name):
    """Return (weather_dict, error_dict). One is always None."""
    if not API_KEY:
        return None, {'city': city_name,
                      'country': 'Server missing OPENWEATHER_API_KEY'}

    params = {'q': city_name, 'appid': API_KEY, 'units': 'metric'}
    try:
        response = requests.get(BASE_URL, params=params, timeout=10).json()
    except requests.RequestException as exc:
        return None, {'city': city_name, 'country': str(exc)}

    if str(response.get('cod')) != '200':
        return None, {'city': city_name,
                      'country': response.get('message', 'unknown error')}

    condition = response['weather'][0]
    temp_c = response['main']['temp']
    weather = {
        'city': city_name,
        'temperature': "{:.1f}".format(temp_c),
        'mood': temp_mood(temp_c),
        'feels_like': "{:.0f}".format(response['main']['feels_like']),
        'humidity': response['main']['humidity'],
        'wind': "{:.0f}".format(response.get('wind', {}).get('speed', 0) * 3.6),
        'description': condition['description'],
        'icon': condition['icon'],
        # 'main' (Clear/Clouds/Rain/Snow...) drives the UI background.
        'main': condition['main'],
        # icon ending 'd' = day, 'n' = night.
        'is_day': condition['icon'].endswith('d'),
        'emoji': CONDITION_EMOJI.get(condition['main'], '🌈'),
        'gif': funny_gif(condition['main']),
        'accessories': dress_character(temp_c, condition['main']),
    }
    return weather, None


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        city_name = request.form['city'].upper()
    else:
        city_name = DEFAULT_CITY

    weather, error = fetch_weather(city_name)
    if error:
        return render_template('index.html', weather_error=error)
    forecast = build_forecast(city_name)
    return render_template('index.html', weather=weather, forecast=forecast)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
