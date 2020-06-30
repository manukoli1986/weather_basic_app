import requests

url = 'http://api.openweathermap.org/data/2.5/weather?q={}&appid=8f5ca370c7041d066e0026e9af47526f'

city_name = 'Del123'

res = requests.get(url.format(city_name)).json()
print(res)