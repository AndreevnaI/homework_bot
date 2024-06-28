import logging
import os
import requests
import time
from dotenv import load_dotenv
from telebot import TeleBot

from http import HTTPStatus
import exceptions


load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM')
TELEGRAM_TOKEN = os.getenv('TELEGRAM')
TELEGRAM_CHAT_ID = os.getenv('CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)


def check_tokens():
    """Проверка доступности переменных окружения, которые необходимы.
    для работы программы.
    """
    return all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID))


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    try:
        logging.info(f'Бот отправил сообщение {message}')
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.debug(f'Сообщение {message} отправлено.')
    except Exception as error:
        logging.error(f'Ошибка при отправке сообщения: {error}')
        raise exceptions.MessageError(f'Ошибка в отправке сообщения {error}')


def get_api_answer(timestamp):
    """Запрос к эндпоинту API-сервиса."""
    try:
        timestamp = int(time.time())
        params = {'from_date': timestamp}
        homework_statuses = requests.get(ENDPOINT, headers=HEADERS,
                                         params=params)
        if homework_statuses.status_code != HTTPStatus.OK:
            raise AssertionError
        return homework_statuses.json()
    except requests.exceptions.RequestException as error:
        logging.error(f'Ошибка при запросе к эндпоинту: {error}')
        return None


def check_response(response):
    """Проверка полученного ответа."""
    if not isinstance(response, dict):
        message = 'Ответ API не является словарем.'
        logging.error(message)
        raise TypeError(message)
    if not response:
        message = 'Ответ содержит пустой словарь.'
        logging.error(message)
        raise KeyError(message)
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        message = 'Структура данных не соответствует ожиданиям.'
        logging.error(message)
        raise TypeError(message)
    if 'homeworks' not in response:
        message = 'Отсутствие ожидаемого ключа в ответе.'
        logging.error(message)
        raise exceptions.NameKeyError(message)
    return homeworks


def parse_status(homework):
    """Извлекает из информации о конкретной домашней работе ее статус."""
    if homework:
        homework_name = homework.get('homework_name')
        if not homework_name:
            logging.error(f'Отсутствует поле: {homework_name}')
            raise KeyError()
        homework_status = homework.get('status')
        if homework_status not in HOMEWORK_VERDICTS:
            logging.error(f'Неизвестный статус: {homework_status}')
            raise KeyError()
        verdict = HOMEWORK_VERDICTS[homework_status]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    else:
        message = 'Пустой словарь'
        logging.error(message)
        raise KeyError(message)


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logging.critical('Отсутствует переменная окружения')
        exit()

    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())

    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response)
            if homeworks:
                message = parse_status(homeworks[0])
                send_message(bot, message)
            else:
                logging.debug('Статус отсутсвует')
            timestamp = response.get('current_date')

        except Exception as error:
            logging.error(f'Сбой в работе программы: {error}')
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
