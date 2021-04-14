import os
import requests
from dotenv import load_dotenv


def get_weather_by_city_name(params):
    try:
        response = requests.get(base_url, params=params)
        if response.status_code == 200:
            res = response.json()
            print(f"Текущая температура в городе {params['q']}: {res['main']['temp']} С, ощущается как "
                  f"{res['main']['feels_like']} С.")
        else:
            print(f'Код ошибки: {response.status_code} {response.text}')
    except requests.exceptions.RequestException as req_exp:
        print('Ошибка выполнения запроса:', req_exp)


load_dotenv()

API_KEY = os.getenv('OPEN_WEATHER_KEY')
base_url = f'https://api.openweathermap.org/data/2.5/weather'

while True:

    city_name = input('Укажите город (Q - для выхода): ')

    if 'q' != city_name != 'Q':
        weather_api_params = {
            'q': city_name,
            'appid': API_KEY,
            'units': 'metric'  # temp in celsius
        }

        get_weather_by_city_name(weather_api_params)
    else:
        print('Вы вышли из программы.')
        break
