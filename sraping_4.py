# 1) Написать приложение, которое собирает основные новости с сайтов news.mail.ru, lenta.ru, yandex.news
# Для парсинга использовать xpath. Структура данных должна содержать:
# - название источника,
# - наименование новости,
# - ссылку на новость,
# - дата публикации
#
# Нельзя использовать BeautifulSoup
#
# 2) Сложить все новости в БД(Mongo); без дубликатов, с обновлениями

import requests
from lxml import html
from pymongo import MongoClient
from accessify import private


class NewsScrap:
    def __init__(self, url, headers):
        self.url = url
        self.headers = headers

    @private
    def insert_to_mongo(self, list_name, from_name):
        try:
            for item in list_name:
                collection.update_one({"$and": [{"news_title": {"$eq": item["news_title"]}},
                                                {"origin": {"$eq": item["origin"]}}]},
                                      {"$set": item}, upsert=True)
            print(f'Новости из {from_name} отправлены в БД')
        except Exception as exp:
            print(exp)

    def lenta_news(self):
        try:
            response = requests.get(self.url, headers=self.headers)
            dom = html.fromstring(response.text)
            xpath_news_items = "//section[contains(@class, 'js-top-seven')]//div[contains(@class, 'item')]"
            news_items = dom.xpath(xpath_news_items)
            for item in news_items:
                news = {}
                item_name = ".//a/text()"
                news["origin"] = "lenta.ru"
                news["news_title"] = item.xpath(item_name)[0].replace(u"\xa0", u" ")
                news["news_url"] = self.url + item.xpath(".//a/@href")[0]
                news["news_date"] = item.xpath(".//a/time/@datetime")[0]
                data_list.append(news)
            self.insert_to_mongo(data_list, "lenta.ru")
        except Exception as exp:
            return exp

    @private
    def mail_news_data(self, url, param):
        try:
            response = requests.get(url, headers=self.headers)
            dom = html.fromstring(response.text)
            xpath_news_items = "//div[@class='breadcrumbs breadcrumbs_article js-ago-wrapper']"
            news_items_info = dom.xpath(xpath_news_items)
            for item in news_items_info:
                if param == "source":
                    source = item.xpath(".//a/span/text()")[0]
                    return source
                elif param == "datetime":
                    news_datetime = item.xpath(".//span//@datetime")[0]
                    return news_datetime
        except Exception as exp:
            return exp

    def mail_news(self):
        try:
            response = requests.get(self.url, headers=self.headers)
            dom = html.fromstring(response.text)
            xpath_news_items = "//div[@class='wrapper']//div[@data-module='TrackBlocks']//" \
                               "div[contains(@class, '__item')]"
            news_items = dom.xpath(xpath_news_items)
            for item in news_items:
                news = {}
                item_name = ".//span[contains(@class, '__title')]/text()"
                news["origin"] = self.mail_news_data(item.xpath(".//a/@href")[0], "source")
                news["news_title"] = item.xpath(item_name)[0].replace(u"\xa0", u" ")
                news["news_url"] = item.xpath(".//a/@href")[0]
                news["news_date"] = self.mail_news_data(item.xpath(".//a/@href")[0], "datetime")
                data_list.append(news)
            self.insert_to_mongo(data_list, "mail.ru")
        except Exception as exp:
            return exp

    def yandex_news(self):
        try:
            response = requests.get(self.url, headers=self.headers)
            dom = html.fromstring(response.text)
            xpath_news_items = "//div[contains(@class, 'news-top-flexible-stories')]/div"
            news_items = dom.xpath(xpath_news_items)
            for item in news_items:
                news = {}
                item_name = ".//h2/text()"
                news["origin"] = item.xpath(".//span[contains(@class, '__source')]//a//text()")[0]
                news["news_title"] = item.xpath(item_name)[0].replace(u"\xa0", u" ")
                news["news_url"] = item.xpath(".//a/@href")[0]
                news["news_date"] = item.xpath(".//span[@class='mg-card-source__time']//text()")[0]
                data_list.append(news)
            self.insert_to_mongo(data_list, "yandex.ru")
        except Exception as exp:
            return exp


headers = {
    "User-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                 "Chrome/90.0.4430.72 Safari/537.36"
}

data_list = []
lenta_url = "https://lenta.ru"
mail_news_url = "https://news.mail.ru/"
yandex_news_url = "https://yandex.ru/news/"

client = MongoClient('localhost', 27017)
db = client['newsdb']
collection = db.news

# news_scrap
lenta_news_scrap = NewsScrap(lenta_url, headers)
lenta_news_scrap.lenta_news()

mail_news_scrap = NewsScrap(mail_news_url, headers)
mail_news_scrap.mail_news()

yandex_news_scrap = NewsScrap(yandex_news_url, headers)
yandex_news_scrap.yandex_news()

