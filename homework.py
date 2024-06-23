import logging
import os
import requests
import time
from dotenv import load_dotenv
from telebot import TeleBot

from http import HTTPStatus


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
        bot.send_massage(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.debug(f'Сообщение {message} отправлено.')
    except Exception as error:
        logging.error(f'Ошибка при отправке сообщения: {error}')


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
        logging.error('Ответ API не является словарем.')
        raise TypeError('Ответ API не является словарем.')
    if not response:
        logging.error('Ответ содержит пустой словарь.')
        raise KeyError('Ответ содержит пустой словарь.')
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        logging.error('Структура данных не соответствует ожиданиям.')
        raise TypeError('Структура данных не соответствует ожиданиям.')
    if 'homeworks' not in response:
        logging.error('Отсутствие ожидаемого ключа в ответе.')
        raise KeyError('Отсутствие ожидаемого ключа в ответе.')
    return homeworks


def parse_status(homework):
    """Извлекает из информации о конкретной домашней работе ее статус."""
    if homework:
        homework_name = homework.get('homework_name')
        if not homework_name:
            logging.error(f'Отсутствует поле: {homework_name}')
            raise KeyError
        homework_status = homework.get('status')
        if homework_status not in HOMEWORK_VERDICTS:
            logging.error(f'Неизвестный статус: {homework_status}')
            raise KeyError
        verdict = HOMEWORK_VERDICTS[homework_status]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    else:
        logging.error('Пустой словарь')
        raise KeyError


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logging.critical('Отсутствует переменная окружения')
        exit()

    # Создаем объект класса бота
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
