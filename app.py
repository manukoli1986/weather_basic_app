# This application is using color from https://colorhunt.co/

import os
import requests
from flask import Flask, render_template, request

app = Flask(__name__)
app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

# API key read from environment. Never hard-code secrets in source.
API_KEY = os.environ.get('OPENWEATHER_API_KEY')
BASE_URL = 'https://api.openweathermap.org/data/2.5/weather'
DEFAULT_CITY = os.environ.get('DEFAULT_CITY', 'Lucknow')
# Build version, set by CI at image build time (see Dockerfile ARG APP_VERSION).
APP_VERSION = os.environ.get('APP_VERSION', 'dev')


@app.context_processor
def inject_version():
    return {'app_version': APP_VERSION}


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
    weather = {
        'city': city_name,
        'temperature': "{:.1f}".format(response['main']['temp']),
        'description': condition['description'],
        'icon': condition['icon'],
        # 'main' (Clear/Clouds/Rain/Snow...) drives the UI background.
        'main': condition['main'],
        # icon ending 'd' = day, 'n' = night.
        'is_day': condition['icon'].endswith('d'),
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
    return render_template('index.html', weather=weather)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
