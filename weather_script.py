import requests

url = 'http://api.openweathermap.org/data/2.5/weather?q={}&appid=XXXXX'

city_name = 'Del123'

res = requests.get(url.format(city_name)).json()
print(res)