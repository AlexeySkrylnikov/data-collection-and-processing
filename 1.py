# Посмотреть документацию к API GitHub, разобраться как вывести список репозиториев для конкретного пользователя,
# сохранить JSON-вывод в файле *.json; написать функцию, возвращающую список репозиториев.

import os
import json
import requests
from dotenv import load_dotenv


def get_all_user_repos_from_github(url, file_name, req_headers):
    try:
        response = requests.get(url, headers=req_headers)
        if response.status_code == 200:
            with open(file_name, 'w') as json_file:
                json.dump(response.json(), json_file, indent=2)
            print(f'Запрос выполнен успешно! Результат сохранен в файл {json_file_name}')
            return response.json()
        else:
            print(f'Ошибка при выполнении запроса. Код ошибки: {response.status_code} {response.text}')
    except requests.exceptions.RequestException as req_exp:
        print(f'Попытка GET запроса привела к ошибке: {req_exp}')


load_dotenv()

GITHUB_USERNAME = os.getenv('GITHUB_USRNAME', None)
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', None)
github_url_repos = f'https://api.github.com/users/{GITHUB_USERNAME}/repos'
json_file_name = f'GitHub_{GITHUB_USERNAME}.json'

headers = {
    'Authorization': f'token {GITHUB_TOKEN}'
}

get_all_user_repos_from_github(github_url_repos, json_file_name, headers)
