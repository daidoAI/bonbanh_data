import json
from csv import writer
import time
import csv
import chromedriver_autoinstaller
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import logging
import os
import random
import re
from concurrent.futures.thread import ThreadPoolExecutor
from datetime import date, datetime
from traceback import format_exc
from typing import List
from selenium import webdriver
import pandas as pd
import requests
from bs4 import BeautifulSoup

PATH = chromedriver_autoinstaller.install()
df = []

def get_info_single_page(car_url):
    car_title = None
    id_post = None
    model = None
    company = None
    version = None
    price = None
    year = None
    style = None
    status = None
    origin = None
    transmission = None
    fuel_type = None
    sell_name = None
    sell_phone = None
    public_date = None
    img_link = None
    num_door = None
    num_seat = None
    color_out = None
    color_in = None
    used_km = None
    consumption = None
    drive = None
    fuel_load = None
    description = None

    result = requests.get(f"{car_url}", proxies = get_proxy(), timeout = 30)
    soup = BeautifulSoup(result.text, 'html.parser')
    # Get car_title

    try:
        car_title = soup.find("div", {"id": "car_detail"})
        car_title = car_title.select_one("div.title h1").get_text()
        car_title = car_title.replace('\t', ' ')
    except:
        raise Exception(f"Page {car_url} not found")

    # Get company, model, version
    listText = soup.findAll('span', attrs={'itemprop': 'itemListElement'})
    # if (len(listText)) > 4:
    company_lowercase = listText[2].text.replace('Loading...', '')
    if 'Hãng khác' in listText[2].text:
        company_lowercase = listText[2].text.replace('Loading...', '')
        company = company_lowercase.strip()
        if 'Trước' in car_title:
            index_year_start = car_title.index('Trước')
            index_year_end = car_title.index('-') - 1
            year = car_title[index_year_start:index_year_end]
        else:
            index_year_start = car_title.index('-') - 5
            index_year_end = car_title.index('-') - 1
            year = car_title[index_year_start:index_year_end]
        model = None
        version = car_title[3:(index_year_start -1)]
    else:
        company_lowercase = listText[2].text.replace('Loading...', '')
        company = company_lowercase.strip()
        if listText[3].text.replace('Loading...', '') == 'Khác':
            index_model = car_title.index(company_lowercase) + len(company_lowercase) + 1
            preModel = company_lowercase
            if 'Trước' in car_title:
                index_year_start = car_title.index('Trước')
                index_year_end = car_title.index('-')
                year = car_title[index_year_start: index_year_end]
                preModel = car_title[(index_model): (index_year_end - 1)]
            else:
                preModel = 'Khác'
            model = preModel.strip()
            version = None
        else:
            preModel = listText[3].text.replace('Loading...', '')
            model = preModel
            index_model = car_title.index(preModel)
            if 'Trước' in car_title:
                index_year_start = car_title.index('Trước')
                index_year_end = car_title.index('-') - 1
                year = car_title[index_year_start: index_year_end]
            else:
                year = listText[4].text.replace('Loading...', '')
                index_year_start = car_title.index(year) - 1
            index_version = index_model + 1 + len(preModel)
            version = str(car_title[index_version: index_year_start]).strip()

    if model == '':
        model = None
    if version == '':
        version = None

    # Regex pattern
    pattern = r"\d\s*-\s*((\d*)\s*Tỷ)*\s*((\d*)\s*Triệu)*"

    # Match pattern to input string
    match = re.findall(pattern, car_title)

    # Calculate total value
    price = -1
    if len(match) > 0:
        billions = int(match[-1][1]) if match[-1][1] != '' else 0
        millions = int(match[-1][3]) if match[-1][3] != '' else 0
        price = billions * 1000 + millions

    get_maTin = soup.find('title').text
    id_post = str(get_maTin.split('|')[1].replace(' ', ''))
    raw_public_date = soup.find('div', {'class': 'notes'}).text
    date_patten = "\d{1,2}/\d{2}/\d{4}"
    public_date = re.findall(string=raw_public_date, pattern=date_patten)

    if len(public_date) > 0:
        public_date = public_date[0]
    else:
        public_date = None
    date_obj = datetime.strptime(public_date, '%d/%m/%Y')
    public_date = date_obj.strftime('%Y-%m-%d')

    sell_name = soup.findAll("a", {"class": "cname"})
    if len(sell_name) == 0:
        sell_name = soup.findAll("span", {"class": "cname"})

    if len(sell_name) > 0:
        sell_name = sell_name[0].get_text()
        sell_phone = str(soup.find("span", {"class": "cphone"}).get_text())

    info2_Car = soup.findAll('div', {'class': 'txt_input'})
    origin = info2_Car[0].text
    status = info2_Car[1].text
    style = info2_Car[2].text
    used_km = int(str(info2_Car[3].text).replace(',', '').replace('Km', '').strip())
    color_out = info2_Car[4].text
    color_in = info2_Car[5].text
    num_door = info2_Car[6].text
    num_seat = soup.find('div', {'class': 'inputbox'}).text.strip()
    fuel_type = str(info2_Car[7].text).replace('\t', ' ')
    fuel_load = info2_Car[8].text
    transmission = info2_Car[9].text
    drive = info2_Car[10].text
    consumption = str(info2_Car[11].text).replace('\t', ' ')
    # name_website = self.website_name

    description = soup.find('div', {'class': 'des_txt'}).text

    img_link = ''
    for link in soup.find_all('a', {'class': 'highslide'}):
        img_link = img_link + str(link.get('href') + ', ')

    result_dict = {
        'name': id_post,
        'car_title': car_title,
        'url': f"{car_url}",
        'version': version,
        'model': model,
        'company': company,
        'year': year,
        'price': price,
        'status': status,
        'origin': origin,
        'style': style,
        'transmission': transmission,
        'fuel_type': fuel_type,
        'sell_name': sell_name,
        'sell_phone': sell_phone,
        'public_date': public_date,
        'img_link': img_link,
        'num_door': num_door,
        'num_seat': num_seat,
        'color_in': color_in,
        'color_out': color_out,
        'used_km': used_km,
        'consumption': consumption,
        'drive': drive,
        'fuel_load': fuel_load,
        'description': description
    }
    return result_dict
PROXY_LIST = [
                '54.169.59.221:8888', '13.212.246.164:8888', '54.179.91.224:8888',
                '18.142.139.250:8888','54.255.205.203:8888',
                '18.141.189.235:8888','13.229.97.173:8888',
                '3.0.99.75:8888','13.250.39.147:8888','54.179.119.184:8888'
                ]
def get_proxy():
    ip = random.choice(PROXY_LIST)
    proxy = {
        'https': ip,
        'http': ip,
    }
    return proxy

proxies = [
    {'ip': '54.169.59.221', 'port': '8888'},
    {'ip': '18.142.139.250', 'port': '8888'},
    {'ip': '18.141.189.235', 'port': '8888'},
    {'ip': '3.0.99.75', 'port': '8888'},
    {'ip': '13.212.246.164', 'port': '8888'},
    {'ip': '54.179.91.224', 'port': '8888'},
    {'ip': '54.255.205.203', 'port': '8888'},
    {'ip': '13.229.97.173', 'port': '8888'},
    {'ip': '13.250.39.147', 'port': '8888'},
    {'ip': '54.179.119.184', 'port': '8888'}
]


def create_driver_with_proxy():
    # Chọn ngẫu nhiên một proxy từ danh sách
    
    random_proxy = random.choice(proxies)
    proxy_ip = random_proxy['ip']
    proxy_port = random_proxy['port']

    # Tạo tùy chọn của trình duyệt Chrome với proxy ngẫu nhiên đã chọn
    chrome_options = Options()
    chrome_options.headless = False
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_prefs = {}
    chrome_options.experimental_options["prefs"] = chrome_prefs
    chrome_prefs["profile.default_content_settings"] = {"images": 2}
    chrome_options.add_argument(f'--proxy-server={proxy_ip}:{proxy_port}')

    # Khởi tạo trình điều khiển Chrome với tùy chọn đã cấu hình
    driver = webdriver.Chrome(PATH, options=chrome_options)
    return driver
dataframe = pd.DataFrame()
final_df = []
def create_folder(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

def export_json(id, post_dict):
    with open(f'{folder_path}/json/{id}.json', 'w+', encoding='utf-8') as f:
        json.dump(post_dict, f)

def run_selenium_task(i, start_id, end_id):
    # Khởi tạo driver và thực hiện các thao tác cần thiết với ID trong phạm vi
    driver = create_driver_with_proxy()
    for id in range(start_id, end_id + 1):
        # Kiểm tra ID đã hoàn thành hay chưa
        if id not in completed_ids:
            driver.get(f'https://duckduckgo.com/?q={id}+inurl%3Abonbanh.com')
            try:
                driver.find_element(By.CLASS_NAME, 'wLL07_0Xnd1QZpzpfR4W')
            except:
                driver.quit()
                driver = create_driver_with_proxy()
                driver.get(f'https://duckduckgo.com/?q={id}+inurl%3Abonbanh.com')
            tags = driver.find_elements(By.CLASS_NAME, 'wLL07_0Xnd1QZpzpfR4W')

            for tag in tags[:5]:
                # print(tag)
                link = tag.find_element(By.CLASS_NAME, 'Rn_JXVtoPVAFyGkcaXyK')
                link = (link.get_attribute("href"))
                if link.startswith("https://bonbanh.com/xe-"):
                    print(link)
                    with open(f"{folder_path}/link_bonbanh.txt", "a+") as f:
                        f.write(link + "\n")
                    post_dict = get_info_single_page(link)
                    export_json(id, post_dict)
                    # with open(f'{folder_path}/json/{id}.json', 'w+') as f:
                    #     json.dump(post_dict, f)
                    final_df.append(post_dict)
                else:
                    with open(f"{folder_path}/id_failed.txt", "a+") as f:
                        f.write(str(id) + "\n")         
            
            completed_ids.append(id)
            with open(f"{folder_path}/completed_ids.txt", "a+") as file:
                file.write(str(id) + "\n")

completed_ids = []
folder_path = "/data/"

try:
    with open(f"{folder_path}/completed_ids.txt", "r") as file:
        completed_ids = [int(line.strip()) for line in file.readlines()]
except FileNotFoundError:
    pass
create_folder(folder_path)
start_time = time.time()
# Số lượng thread muốn chạy
num_threads = 3
# ID bắt đầu
start_id = 4600000
# ID kết thúc
end_id = 4600020

# Số lượng ID trong mỗi thread
ids_per_thread = (end_id - start_id + 1) // num_threads

# Khởi tạo ThreadPoolExecutor với số lượng thread tương ứng
with ThreadPoolExecutor(max_workers=num_threads) as executor:
    # Chia ID thành các phạm vi tương ứng cho mỗi thread và chạy công việc
    for i in range(num_threads):
        # Tính toán start_id và end_id cho mỗi thread
        start = start_id + i * ids_per_thread
        end = start + ids_per_thread - 1
        # Chạy công việc trên mỗi thread
        executor.submit(run_selenium_task,i, start, end)
final_dataframe = pd.DataFrame(final_df)
final_dataframe.to_csv(f"{folder_path}/{start_id}_{end_id}.csv")