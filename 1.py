# Необходимо собрать информацию о вакансиях на вводимую должность (используем input или через аргументы) с сайта HH.
# Приложение должно анализировать несколько страниц сайта (также вводим через input или аргументы).
# Получившийся список должен содержать в себе минимум:
# Наименование вакансии.
# Предлагаемую зарплату (отдельно минимальную и максимальную).
# Ссылку на саму вакансию.
# Сайт, откуда собрана вакансия.
# По желанию можно добавить ещё параметры вакансии (например, работодателя и расположение).
# Общий результат можно вывести с помощью
# dataFrame через pandas. Сохраните в json либо csv.

import time
import requests
from bs4 import BeautifulSoup as bs
import pandas as pd
import logging
import json
import sys

headers = {
    "User-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                 "Chrome/90.0.4430.72 Safari/537.36"
}

url = "https://hh.ru"
data_list = []

try:
    vacancy_search_text = input("Укажите вакансию для поиска (Q - выход): ")
    if 'q' != vacancy_search_text != 'Q':
        url_page_value = f"/search/vacancy?clusters=true&enable_snippets=true&text={vacancy_search_text}" \
                         f"&L_save_area=true&area=113&showClusters=true&page=0"
        while True:
            response = requests.get(f"{url}{url_page_value}", headers=headers)
            print(f"Запрос по URL: {response.url}")
            soup = bs(response.text, "html.parser")

            if response.status_code == 200:
                vacancy_items = soup.find("div", {"data-qa": "vacancy-serp__results"}).\
                    find_all('div', {'class': 'vacancy-serp-item'})
                for item in vacancy_items:
                    vacancy_dict = {}

                    # название вакансии
                    vacancy_name = item.find(attrs={"data-qa": "vacancy-serp__vacancy-title"})
                    # print(vacancy_name.text)
                    vacancy_dict["name"] = vacancy_name.text
                    vacancy_dict["link"] = vacancy_name["href"]

                    # ЗП
                    vacancy_price = item.find(attrs={"data-qa": "vacancy-serp__vacancy-compensation"})
                    if vacancy_price is None:
                        vacancy_dict["price"] = "ЗП не указана"
                    if vacancy_price is not None:
                        vacancy_dict["price"] = vacancy_price.getText().replace(u'\u202f', u'')

                    # название компании
                    vacancy_company = item.find(attrs={"data-qa": "vacancy-serp__vacancy-employer"})
                    if vacancy_company is None:
                        vacancy_dict["company_name"] = "Компания не указана"
                    if vacancy_company is not None:
                        vacancy_dict["company_name"] = vacancy_company.getText().replace(u'\xa0', u' ')

                    # адрес компании
                    vacancy_address = item.find(attrs={"data-qa": "vacancy-serp__vacancy-address"})
                    if vacancy_address is None:
                        vacancy_dict["company_address"] = "Адрес не указан"
                    if vacancy_address is not None:
                        vacancy_dict["company_address"] = vacancy_address.text

                    # сайт откуда собрана вакансия
                    vacancy_dict["site_from"] = "HH"

                    if len(vacancy_dict) != 0:
                        data_list.append(vacancy_dict)

                next_page_button = soup.find_all(attrs={"data-qa": "pager-next"})
                if (len(next_page_button)) != 0:
                    for item in next_page_button:
                        url_page_value = item['href']
                        time.sleep(1)
                else:
                    # print(data_list)
                    df = pd.DataFrame.from_records(data_list)
                    print(df)
                    df.to_csv("data.csv", index=False)
                    df.to_json("data2.json", indent=2)
                    with open("data.json", "w") as json_file:
                        json.dump(data_list, json_file, indent=2)
                    break
    else:
        sys.exit()
except Exception as exp:
    logging.error('Ошибка!', exc_info=exp)
