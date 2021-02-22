# -*- coding: utf-8 -*-
"""Main module"""
import logging
import os

import telegram
from bottle import Bottle, response, request as bottle_request
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

import io_utils
import plot_utils
import tg_utils
import virus_utils
from models import Countries, Country, GraphType, StatType

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


class TelegramBot:

    def error(update, context):
        """Журнал ошибок, вызванных обновлениями."""
        logger.warning('Обновление "%s" вызвало ошибку "%s"', update, context.error)

    def __init__(self, token: str):
        self.tgBOT = telegram.Bot(token=token)

    def run(self, bottle: Bottle):
        bottle.route('/api', callback=self.post_handler, method="POST")

    def send_message(self, text, chat_id: int, reply_to_message_id=None):
        """
        Подготовленные данные должны быть в формате json, которые содержат как минимум chat_id и text.
        """
        self.tgBOT.sendMessage(chat_id=chat_id, text=text, reply_to_message_id=reply_to_message_id)

    def prompt_select_new_country(self, chat_id: int):
        temp_list = []
        keyboard = []

        items = Countries.__members__.items()
        length = len(items)
        if length % 4 == 0:
            rows_per_item = 4
        else:
            rows_per_item = 3
        idx = 0
        for name, member in items:
            str_val = member.displayString
            int_val = member.displayValue

            if idx > 0 and idx % rows_per_item == 0:  # 4 4 3 3
                keyboard.append(temp_list)  # построение линий
                temp_list = []
            temp_list.append(InlineKeyboardButton(str_val, callback_data=int_val))
            idx = idx + 1
        keyboard.append(temp_list)

        reply_markup = InlineKeyboardMarkup(keyboard)
        self.tgBOT.sendMessage(chat_id=chat_id,
                               text="Выберите страну",
                               reply_markup=reply_markup)

    def react_stats_option(self, text: str, chat_id: int, user_id: int) -> bool:
        # только для отладки
        if io_utils.is_local_run():
            print("Текстовое сообщение :", text)
        # Приветственное сообщение
        if text == "/start" or text == "/help":
            bot_welcome = """
                     Covid-19_Stats. Бот для получения статистики по Covid-19.

                     Команда /stats для получения статистики выбранной страны.
                     Команда /country для выбора страны.
                     """
            self.tgBOT.sendMessage(chat_id=chat_id, text=bot_welcome)
            return True

        if text == '/country':
            self.prompt_select_new_country(chat_id)
            return True

        if text == '/stats':
            country = virus_utils.read_pref_country(user_id=user_id)
            self.buildMenuSendMessage(chat_id, country)
            return True

        if text == '/test':
            self.tgBOT.sendMessage(chat_id=chat_id,
                                   text="Проблема с именем, которое вы использовали, пожалуйста, введите другое имя")
            return True

        if text == '/cases_week' or text == '‎🌏 Случаи (сред)':
            self.send_photo_tg_general(stat_type=StatType.CONFIRMED, chat_id=chat_id,
                                       graph_type=GraphType.CONFIRMED_WEEK)
            return True

        if text == '/fatal_week' or text == '‎🌏 Смерти (сред)':
            self.send_photo_tg_general(stat_type=StatType.DEATHS, chat_id=chat_id,
                                       graph_type=GraphType.DEATHS_WEEK)
            return True

        if text == '/fatal_rate' or text == '‎🌏 Смерти (%)':
            self.send_photo_tg_general(stat_type=StatType.DEATHS, chat_id=chat_id,
                                       graph_type=GraphType.DEATHS_RATE)
            return True

        if text == '/cases_per_1m' or text == '‎🌏 Случаи на 1М':
            self.send_photo_tg_general(stat_type=StatType.CONFIRMED, chat_id=chat_id,
                                       graph_type=GraphType.CONFIRMED_1M_PEOPLE)
            return True

        if text == '/cases_bar' or text == '‎🌏 Случаи (С)':
            self.send_photo_tg_general(stat_type=StatType.CONFIRMED, chat_id=chat_id,
                                       graph_type=GraphType.CONFIRMED_BAR)
            return True

        if text == '/fatal_bar' or text == '‎🌏 Смерти (С)':
            self.send_photo_tg_general(stat_type=StatType.DEATHS, chat_id=chat_id,
                                       graph_type=GraphType.DEATHS_BAR)
            return True

        if text == '/cases' or text == '‎🌏 Случаи':
            self.send_photo_tg_general(stat_type=StatType.CONFIRMED, chat_id=chat_id,
                                       graph_type=GraphType.CONFIRMED_TOTAL)
            return True

        if text == '/fatal' or text == '‎🌏 Смерти':
            self.send_photo_tg_general(stat_type=StatType.DEATHS, chat_id=chat_id,
                                       graph_type=GraphType.DEATHS_TOTAL)
            return True

        for name, member in Countries.__members__.items():
            int_val = member.displayValue
            flag = member.displayFlag
            country_value = member.value

            if text == f'/{int_val}_fatal_total' or text == f"{flag} Всего смертей":
                self.send_photo_tg_country_total(stat_type=plot_utils.StatType.DEATHS, chat_id=chat_id,
                                                 graph_type=GraphType.DEATHS_TOTAL,
                                                 country_name=country_value)
                return True

            if text == f'/{int_val}_cases_total' or text == f"{flag} Всего случаев":
                self.send_photo_tg_country_total(stat_type=StatType.CONFIRMED, chat_id=chat_id,
                                                 graph_type=GraphType.CONFIRMED_TOTAL,
                                                 country_name=country_value)
                return True

            if text == f'/{int_val}_fatal_daily' or text == f"{flag} Смерти (день)":
                self.send_photo_tg_country_active(stat_type=StatType.DEATHS, chat_id=chat_id,
                                                  graph_type=GraphType.DEATHS_ACTIVE,
                                                  country_name=country_value)
                return True

            if text == f'/{int_val}_cases_daily' or text == f"{flag} Случаи (день)":
                self.send_photo_tg_country_active(stat_type=StatType.CONFIRMED, chat_id=chat_id,
                                                  graph_type=GraphType.CONFIRMED_ACTIVE,
                                                  country_name=country_value)
                return True

    def post_handler(self):
        data = bottle_request.json
        update = telegram.Update.de_json(data, self.tgBOT)
        query = update.callback_query

        is_bot = update.effective_user.is_bot
        if is_bot:
            print('Бот обнаружен')
            return

        user_id = update.effective_user.id
        if io_utils.is_local_run():
            print(f'USER ID: {user_id}, name: {update.effective_user.username}')

        if query is not None:
            option = query.data

            if option in Countries.__members__:
                country = Countries[option]
                virus_utils.write_pref_country(user_id, country)
                query.edit_message_text(text="Выбранная опция: {}".format(country.displayString))

                chat_id = query.message.chat_id
                self.buildMenuSendMessage(chat_id, country)
            else:
                print(f'Нет информации о стране {option}')
            return

        if update.message is None:
            print('Пустое сообщение')
            return

        chat_id = update.message.chat_id
        msg_id = update.message.message_id

        text_pure = update.message.text
        if text_pure is None:
            print('Пустой текст')
            return

        text = text_pure.encode('utf-8').decode()
        reacted = self.react_stats_option(text=text, chat_id=chat_id, user_id=user_id)
        if reacted:
            return

        self.send_message(text='Опция не выбрана', chat_id=chat_id)
        return response

    def buildMenuSendMessage(self, chat_id: int, country: Country):
        self.tgBOT.sendMessage(chat_id, 'Выберите опцию клавиатуры',
                               reply_markup=ReplyKeyboardMarkup(
                                   resize_keyboard=True,
                                   keyboard=[
                                       [
                                           KeyboardButton(text="‎🌏 Случаи (сред)"),
                                           KeyboardButton(text="‎🌏 Смерти (сред)"),
                                           KeyboardButton(text="‎🌏 Смерти (%)"),
                                           KeyboardButton(text="‎🌏 Случаи на 1М")
                                       ],
                                       [
                                           KeyboardButton(text="‎🌏 Случаи"),
                                           KeyboardButton(text="‎🌏 Смерти"),
                                           KeyboardButton(text="‎🌏 Случаи (С)"),
                                           KeyboardButton(text="‎🌏 Смерти (С)")
                                       ],
                                       [
                                           KeyboardButton(text=f"{country.displayFlag} Всего случаев"),
                                           KeyboardButton(text=f"{country.displayFlag} Всего смертей"),
                                           KeyboardButton(text=f"{country.displayFlag} Случаи (день)"),
                                           KeyboardButton(text=f"{country.displayFlag} Смерти (день)")
                                       ]
                                   ],
                                   one_time_keyboard=False
                               ))

    def send_photo_tg_country(self, active: bool, stat_type: StatType, country: Country, chat_id: int,
                              graph_type: GraphType):
        photo_url = io_utils.get_photo_path_country(graph_type, country_name=country.value)
        need_data = virus_utils.should_update_data()

        if need_data is False and os.path.exists(photo_url):
            photo_stream = open(photo_url, 'rb')
            tg_utils.send_photo_file(self.tgBOT, photo_stream, chat_id)
        else:
            if active:
                plot_tuple = plot_utils.generate_country_active_plot(country, stat_type)
            else:
                plot_tuple = plot_utils.generate_country_total_plot(country, stat_type)

            if plot_tuple is not None:
                fig, ax = plot_tuple
                tg_utils.send_photo_fig(self.tgBOT, chat_id=chat_id, fig=fig, graph_type=graph_type,
                                        country=country)

    def send_photo_tg_country_active(self, stat_type: StatType, country_name: Country, chat_id: int,
                                     graph_type: GraphType):
        self.send_photo_tg_country(True, stat_type, country_name, chat_id, graph_type)

    def send_photo_tg_country_total(self, stat_type: StatType, country_name: Country, chat_id: int,
                                    graph_type: GraphType):
        self.send_photo_tg_country(False, stat_type, country_name, chat_id, graph_type)

    def send_photo_tg_general(self, stat_type: StatType, chat_id: int, graph_type: GraphType):
        photo_url = io_utils.get_photo_path_world(graph_type)
        need_data = virus_utils.should_update_data()

        if need_data is False and os.path.exists(photo_url):  # нет необходимости в данных и фото -> возврат
            photo_stream = open(photo_url, 'rb')
            tg_utils.send_photo_file(self.tgBOT, photo_stream, chat_id)
        else:  # получить новые данные или переписать существующие

            if graph_type == GraphType.CONFIRMED_1M_PEOPLE:
                plot_tuple = plot_utils.generate_world_stat_10_per_million(stat_type)
            elif graph_type == GraphType.DEATHS_RATE:
                plot_tuple = plot_utils.generate_world_mortality_rate_10()
            elif graph_type == GraphType.CONFIRMED_BAR or \
                    graph_type == GraphType.DEATHS_BAR or \
                    graph_type == GraphType.RECOVERED_BAR:
                plot_tuple = plot_utils.generate_bar_world_stat_10(stat_type)
            elif graph_type == GraphType.CONFIRMED_WEEK or \
                    graph_type == GraphType.DEATHS_WEEK or \
                    graph_type == GraphType.RECOVERED_WEEK:
                plot_tuple = plot_utils.generate_toll_plot_avg(stat_type)
            else:
                plot_tuple = plot_utils.generate_world_stat_10(stat_type, False)

            if plot_tuple is not None:
                fig, ax = plot_tuple
                tg_utils.send_photo_fig(self.tgBOT, chat_id=chat_id, fig=fig, graph_type=graph_type)
            else:
                print('Граф не построен ' + graph_type.to_name())
