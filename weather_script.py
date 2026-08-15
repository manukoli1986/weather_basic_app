import os
import requests

# API key read from environment. Never hard-code secrets in source.
API_KEY = os.environ.get('OPENWEATHER_API_KEY')
BASE_URL = 'https://api.openweathermap.org/data/2.5/weather'

city_name = 'London'

params = {'q': city_name, 'appid': API_KEY, 'units': 'metric'}
response = requests.get(BASE_URL, params=params, timeout=10).json()

if str(response.get('cod')) == '200':
    weather_of_city = {
        'city': city_name,
        'temperature': "{:.1f}".format(response['main']['temp']),
        'description': response['weather'][0]['description'],
        'icon': response['weather'][0]['icon'],
    }
    print(weather_of_city)
else:
    print({'city': city_name, 'country': response.get('message', 'error')})
