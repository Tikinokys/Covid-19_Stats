import csv
import datetime
import json
import os
import re
import time
from collections import defaultdict
from datetime import datetime
from io import StringIO
from typing import Optional

import requests
from dateutil.parser import parse as parsedate

import io_utils
from models import Country, Countries, TimeSeriesItem

timeseries_url = 'https://pomber.github.io/covid19/timeseries.json'


def num(s):
    try:
        return int(s)
    except ValueError:
        return 0


TIMOUT_SEC = 3 * 60 * 60  # 3 часа в секундах

pref_country_persist = {}


def read_pref_country(user_id: int) -> Country:
    country = pref_country_persist.get(user_id)
    if country is None:
        return Countries.US  # значение по умолчанию
    return Countries[country]


def write_pref_country(user_id: int, country: Countries):
    pref_country_persist[user_id] = country.displayValue


def is_remote_file_changed(since_timestamp: int) -> bool:
    r = requests.head(timeseries_url)
    if r.status_code == requests.codes.ok:
        url_time = r.headers['last-modified']
        url_date = parsedate(url_time)
        url_date_sec_epoch = int(time.mktime(url_date.timetuple()))
        return url_date_sec_epoch > since_timestamp
    return True  # по умолчанию изменено


def get_formatted_datetime_change_data() -> str:
    datetime_stamp = io_utils.read_pref_date()
    return time.strftime('%b %d %Y %H:%M:%S %Z', time.gmtime(datetime_stamp))


def should_update_data() -> bool:
    if os.path.exists(io_utils.get_timeseries_data_path()) is False:  # исходных данных не существует
        return True
    sec_now = int(time.time())  # Текущее время
    last_time_modification_sec = int(os.path.getmtime(io_utils.get_timeseries_data_path()))
    timeout_expire_diff = sec_now - last_time_modification_sec  # нужно обновить дату
    if timeout_expire_diff < TIMOUT_SEC:
        return False  # файл уже обновлен

    datetime_stamp = io_utils.read_pref_date()
    is_remote_changed = is_remote_file_changed(datetime_stamp)
    return is_remote_changed


def fetch_pomper_stat() -> Optional[dict]:
    should_refresh = should_update_data()
    if should_refresh is False:
        # попытка вернуть кешированные данные
        if os.path.exists(io_utils.get_timeseries_data_path()):
            with open(io_utils.get_timeseries_data_path()) as json_file:
                data = json.load(json_file)
                return data

    req = requests.get(timeseries_url)
    if req.status_code == requests.codes.ok:
        # сохранить дату и время
        date_timestamp = req.headers['last-modified']
        url_date = parsedate(date_timestamp)

        ts = time.mktime(url_date.timetuple())
        io_utils.write_pref_date(int(ts))

        json_data = req.json()
        # сохранить файл
        io_utils.write_timeseries_data(json_data)
        return json_data  # ответ в формате JSON
    return None


def fetch_timeseries_report_deaths() -> Optional[list]:
    return fetch_timeseries_report('time_series_covid19_deaths_global.csv')


def fetch_timeseries_report_recovered() -> Optional[list]:
    return fetch_timeseries_report('time_series_covid19_recovered_global.csv')


def fetch_timeseries_report_confirmed() -> Optional[list]:
    return fetch_timeseries_report('time_series_covid19_confirmed_global.csv')


def fetch_timeseries_report(file_name: str) -> Optional[list]:
    url = f'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data' \
          f'/csse_covid_19_time_series/{file_name}'
    req = requests.get(url)
    if req.status_code == requests.codes.ok:

        csv_content = req.text

        data_stats = []
        csv_file = StringIO(csv_content)
        csv_reader = csv.DictReader(csv_file)
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                line_count += 1
                print(f'Column names are {", ".join(row)}')

            total = 0
            dates_stat = defaultdict(int)
            for key, value in row.items():
                match = re.search(r'\d{1,2}/\d{1,2}/\d{2}', key)
                if match is not None:
                    group = match.group().split("/")
                    year = 2000 + num(group[2])
                    month = num(group[0])
                    day = num(group[1])
                    dt = datetime(year=year, month=month, day=day)
                    print(dt)
                    date_str = dt.isoformat()
                    dates_stat[date_str] = num(value)
                    total += num(value)

            country = row["Country/Region"]
            state = row["Province/State"]
            ts = TimeSeriesItem(state, country, dates_stat, total)
            data_stats.append(ts)

            line_count += 1
        print(f'Processed {line_count} lines.')
        return data_stats

    return None


def reformat_large_tick_values(tick_val, pos):
    if tick_val >= 1000000000:
        val = round(tick_val / 1000000000, 1)
        new_tick_format = '{:}B'.format(val)
    elif tick_val >= 1000000:
        val = round(tick_val / 1000000, 1)
        new_tick_format = '{:}M'.format(val)
    elif tick_val >= 1000:
        val = round(tick_val / 1000, 1)
        new_tick_format = '{:}K'.format(val)
    elif tick_val < 1000:
        new_tick_format = round(tick_val, 1)
    else:
        new_tick_format = tick_val

    # превратить new_tick_format в строковое значение
    new_tick_format = str(new_tick_format)

    # приведенный ниже код сохранит 4.5M как есть, но изменит такие значения, как 4.0M на 4M, так как ноль после десятичной дроби не нужен
    index_of_decimal = new_tick_format.find(".")

    if index_of_decimal != -1:
        value_after_decimal = new_tick_format[index_of_decimal + 1]
        if value_after_decimal == "0":
            # удаление 0 после десятичной запятой, так как он не нужен
            new_tick_format = new_tick_format[0:index_of_decimal] + new_tick_format[index_of_decimal + 2:]

    return new_tick_format
