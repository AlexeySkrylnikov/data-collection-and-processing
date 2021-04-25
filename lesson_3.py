# Развернуть у себя на компьютере/виртуальной машине/хостинге MongoDB и реализовать функцию, записывающую собранные
# вакансии в созданную БД. Написать функцию, которая производит поиск и выводит на экран вакансии с заработной платой
# больше введённой суммы. Написать функцию, которая будет добавлять в вашу базу данных только новые вакансии с сайта.


import time
import requests
from bs4 import BeautifulSoup as bs
import pandas as pd
import logging
import json
import sys
import re
from pymongo import MongoClient

headers = {
    "User-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                 "Chrome/90.0.4430.72 Safari/537.36"
}

url = "https://hh.ru"
data_list = []

client = MongoClient('localhost', 27017)
db = client['lessonsdb']
collection = db.hh_vac


# more than the specified value of salary
def find_salary(param):
    if param != 3:
        salary = input("Укажите сумму: ")
    else:
        salary = input("Укажите сумму от:")
        max_salary = input("Укажите сумму до: ")

    # more than in min
    if param == 1:
        salaries_list = collection.find({"min_salary": {"$gt": int(salary)}}).sort("min_salary")
    # more than in max
    elif param == 2:
        salaries_list = collection.find({"max_salary": {"$gt": int(salary)}}).sort("max_salary")
    # from and to
    elif param == 3:
        salaries_list = collection.find({"$and": [{"$and": [{"min_salary": {"$gte": int(salary)}},
                                                            {"min_salary": {"$lte": int(max_salary)}}]},
                                                  {"$and": [{"max_salary": {"$gte": int(salary)}},
                                                            {"max_salary": {"$lte": int(max_salary)}}]}]}).\
                        sort("min_salary")

    if param <= 3:
        for salary_item in salaries_list:
            print(salary_item)
    else:
        print("Ошибка параметра!")


# проверка на уникальность записи в БД
def is_exists(name, field):
    return bool(collection.find_one({name: {"$in": [field]}}))


# реализация get метода в функции
def get_method(base_url, next_page_url, headers_for_site):
    response = requests.get(f"{base_url}{next_page_url}", headers=headers_for_site)
    return response


# для конвертации символа валюты в название
def get_name_currency(currency_name):
        currency_dict = {
            'EUR': {' €'},
            'KZT': {' ₸'},
            'RUB': {' ₽', 'руб.'},
            'UAH': {' ₴', 'грн.'},
            'USD': {' $'}
        }

        name = currency_name

        for item_name, items_list in currency_dict.items():
            if currency_name in items_list:
                name = item_name

        return name


def hh_vacancy_scrap(vacancy_name, headers_for_site, data_list_name, param):
    cnt = 1
    if 'q' != vacancy_name != 'Q':
        url_page_value = f"/search/vacancy?clusters=true&enable_snippets=true&text={vacancy_name}" \
                         f"&L_save_area=true&area=113&showClusters=true&page=0"
        while True:
            response = get_method(url, url_page_value, headers_for_site)
            # print(f"Запрос по URL: {response.url}")
            if response.status_code == 200:
                soup = bs(response.text, "html.parser")
                print(f"Скрапинг вакансий со страницы {cnt}")
                cnt += 1
                vacancy_items = soup.find("div", {"data-qa": "vacancy-serp__results"}). \
                    find_all('div', {'class': 'vacancy-serp-item'})
                for item in vacancy_items:
                    vacancy_dict = {}

                    # название вакансии и ссылка
                    vacancy_name = item.find(attrs={"data-qa": "vacancy-serp__vacancy-title"})
                    # print(vacancy_name.text)
                    vacancy_dict["name"] = vacancy_name.text
                    vacancy_dict["link"] = vacancy_name["href"]

                    # ЗП
                    vacancy_price = item.find(attrs={"data-qa": "vacancy-serp__vacancy-compensation"})
                    if vacancy_price is None:
                        vacancy_dict["min_salary"] = 0
                        vacancy_dict["max_salary"] = 0
                        vacancy_dict["salary_currency"] = None
                    if vacancy_price is not None:
                        salary = vacancy_price.getText().replace(u'\u202f', u'').replace(u'\xa0', u'')
                        salary = re.split(r'\s|-', salary)

                        if salary[0] == "от":
                            vacancy_dict["min_salary"] = int(salary[1])
                            vacancy_dict["max_salary"] = 0
                        elif salary[0] == "до":
                            vacancy_dict["min_salary"] = 0
                            vacancy_dict["max_salary"] = int(salary[1])
                        else:
                            vacancy_dict["min_salary"] = int(salary[0])
                            vacancy_dict["max_salary"] = int(salary[1])

                        vacancy_dict["salary_currency"] = get_name_currency(salary[-1])

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
                    vacancy_dict["site_from"] = url

                    if len(vacancy_dict) != 0:
                        data_list_name.append(vacancy_dict)

                    # пишем в mongo
                    if is_exists("link", vacancy_dict["link"]):
                        collection.update_one({"link": vacancy_dict["link"]}, {'$set': vacancy_dict})
                    else:
                        collection.insert_one(vacancy_dict)
                # cnt += 1

                # next_page_button = soup.find_all(attrs={"data-qa": "pager-next"})
                # for item in next_page_button:
                #     url_page_value = item['href']
                #     time.sleep(1)
                #
                # if cnt == 4:
                #     print(data_list_name)
                #     break

                next_page_button = soup.find_all(attrs={"data-qa": "pager-next"})
                if (len(next_page_button)) != 0:
                    for item in next_page_button:
                        url_page_value = item['href']
                        time.sleep(1)
                else:
                    # print(data_list)
                    # df = pd.DataFrame.from_records(data_list)
                    # print(df)
                    # df.to_csv("data.csv", index=False)
                    # df.to_json("data2.json", indent=2)
                    # with open("data.json", "w") as json_file:
                    #     json.dump(data_list, json_file, indent=2)
                    find_salary(param)
                    break
            else:
                print("Запрос не удался:", response.status_code)
    else:
        sys.exit()


try:
    vacancy_search_text = input("Укажите вакансию для поиска (Q - выход): ")
    param = int(input("1 - найти вакансии с минимальной ЗП больше указанной суммы\n"
                  "2 - найти вакансии с максимальной ЗП больше указанной суммы\n"
                  "3 - найти вакансии с ЗП от и до: "))
    hh_vacancy_scrap(vacancy_search_text, headers, data_list, param)
except Exception as exp:
    logging.error('Возникла ошибка!', exc_info=exp)
