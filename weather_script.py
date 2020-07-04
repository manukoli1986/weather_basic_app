import requests
from flask import request

url = 'http://api.openweathermap.org/data/2.5/weather?q={}&appid=8f5ca370c7041d066e0026e9af47526f'

city_name = 'London'

response = requests.get(url.format(city_name)).json()
if response['cod'] == 200:
    temperature_in_degree = "{:10.2f}".format(((response['main']['temp']) - 273.15))
    weather_of_city = {
        'city' : city_name,
        'temperature' : temperature_in_degree,
        'description' : response['weather'][0]['description'],
        'icon' : response['weather'][0]['icon'],
    }
    print(weather_of_city)
else:
    weather_of_city = {
        'city' : city_name,
        'country' : response['message']
    }
    print(weather_of_city)
# print(response)
