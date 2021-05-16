# Написать программу, которая собирает посты из группы https://vk.com/tokyofashion
# Будьте внимательны к сайту!
# Делайте задержки, не делайте частых запросов!
#
# 1) В программе должен быть ввод, который передается в поисковую строку по постам группы
# 2) Соберите данные постов:
# - Дата поста
# - Текст поста
# - Ссылка на пост(полная)
# - Ссылки на изображения(если они есть)
# - Количество лайков, "поделиться" и просмотров поста
# 3) Сохраните собранные данные в MongoDB
# 4) Скролльте страницу, чтобы получить больше постов(хотя бы 2-3 раза)
# 5) (Дополнительно, необязательно) Придумайте как можно скроллить "до конца"
# до тех пор пока посты не перестанут добавляться

# import os
# from selenium import webdriver
#
# driver_path = "./chromedriver"
#
# driver = webdriver.Chrome(driver_path)
#
# url = "https://vk.com/tokyofashion"
# driver.get(url)

import sys
import time
from selenium import  webdriver
from selenium.webdriver.common.keys import Keys
from pymongo import MongoClient
from pprint import pprint

driver_path = "./chromedriver"
url = "https://vk.com/tokyofashion"
driver = webdriver.Chrome(driver_path)

post_info = []

client = MongoClient('localhost', 27017)
db = client['vk']
collection = db.public


# проверка на уникальность записи в БД
def is_exists(name, field):
    return bool(collection.find_one({name: {"$in": [field]}}))


def get_vk_public_items(find_key, url, driver):
    driver.get(url)
    search_field = driver.find_element_by_class_name("ui_tab_search").get_attribute("href")
    driver.get(search_field)
    search = driver.find_element_by_id("wall_search")
    search.send_keys(find_key, Keys.ENTER)

    scroll = 1
    while True:
        time.sleep(2)
        try:
            not_now_btn = driver.find_element_by_class_name("JoinForm__notNow")
            if not_now_btn:
                not_now_btn.click()
        except Exception as exp:
            print("Возникло исключение:", exp)
        finally:
            driver.find_element_by_tag_name("html").send_keys(Keys.END)
            scroll += 1
            time.sleep(1)
            wall_load_more = driver.find_element_by_id("fw_load_more")
            stop_scrolling = wall_load_more.get_attribute("style")
            # print("scroll", scroll)
            if stop_scrolling == "display: none;":
                break

    posts = driver.find_elements_by_xpath("//div[@id='page_wall_posts']//..//"
                                         "img[contains(@alt,'Tokyo Fashion')]/../../..")

    for post in posts:
        post_data = {"post_date": post.find_element_by_class_name("rel_date").text,
                     "post_text": post.find_element_by_class_name("wall_post_text").text,
                     "post_link": post.find_element_by_class_name("post_link").get_attribute("href")}

        post_photos_list = []
        post_photo_links = post.find_elements_by_xpath(".//a[contains(@aria-label, 'Original')]")
        for item in post_photo_links:
            post_photos_list.append(item.get_attribute("aria-label").split()[2])
        post_data["post_photos_links"] = post_photos_list
        post_data["post_likes"] = int(post.find_elements_by_class_name("like_button_count")[0].text)
        post_data["post_share"] = int(post.find_elements_by_class_name("like_button_count")[1].text)
        post_data["post_views"] = post.find_element_by_class_name("like_views").text

        # post_info.append(post_data)

        if is_exists("post_link", post_data["post_link"]):
            collection.update_one({"post_link": post_data["post_link"]}, {'$set': post_data})
        else:
            collection.insert_one(post_data)
    # pprint(sys.getsizeof(post_info), post_info)


find_text = input("Введите искомый текст: ")
get_vk_public_items(find_text, url, driver)
