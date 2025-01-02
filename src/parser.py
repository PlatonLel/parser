from pyrogram import Client
import re
import csv
from datetime import datetime
import os

# Имя файла CSV для хранения api_id и api_hash
API_CREDENTIALS_FILE = "api_credentials.csv"
SESSION_NAME = "my_program_session"

def get_api_credentials():
    #Получает api_id и api_hash из файла или запрашивает у пользователя
    if os.path.exists(API_CREDENTIALS_FILE):
        with open(API_CREDENTIALS_FILE, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            credentials = list(reader)
            if len(credentials) > 0 and len(credentials[0]) == 2:
                print("Найдены существующие API-ключи.")
                return int(credentials[0][0]), credentials[0][1]
    # Если файл не найден или он пустой
    api_input = input("Введите api_id и api_hash через пробел: ")
    api_id, api_hash = api_input.split()
    # Сохраняем данные в файл
    with open(API_CREDENTIALS_FILE, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([api_id, api_hash])
    return int(api_id), api_hash

# Получение API-ключей
api_id, api_hash = get_api_credentials()

# Создание клиента
app = Client(SESSION_NAME, api_id, api_hash)

def extract_contacts(text):
    #Извлекает все контакты из текста (форматы @username и https://t.me/username)
    contacts = []
    username_pattern = r'@[\w\d_]+'
    usernames = re.findall(username_pattern, text)
    contacts.extend(usernames)
    telegram_url_pattern = r'https://t\.me/[\w\d_]+'
    telegram_urls = re.findall(telegram_url_pattern, text)
    contacts.extend(telegram_urls)
    return contacts

def extract_discount(text):
    #Извлекает процент скидки из текста
    discount_pattern = r'\d+\s*%'
    discounts = re.findall(discount_pattern, text)
    if discounts:
        return discounts[0].strip().replace(' ', '')
    return None

def process_message(message):
    #Обрабатывает сообщение и возвращает контакты, скидку и ссылку на пост
    if not (message.text or message.caption):
        return None, None, None
    text = message.text if message.text else message.caption
    contacts = extract_contacts(text)
    discount = extract_discount(text)
    link = message.link  # Получаем ссылку на сообщение, если доступна
    return contacts, discount, link

async def main():
    # Запрашиваем у пользователя дату и время
    date_str = input("Введите дату в формате гггг-мм-дд чч:мм:сс: ")
    try:
        date_from = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")  # Преобразуем в datetime
    except ValueError:
        print("Неправильный формат даты. Убедитесь, что ввод соответствует формату гггг-мм-дд чч:мм:сс.")
        return

    # Создаём CSV файл с текущей датой в имени
    filename = f'contacts_discounts_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Contact', 'Discount', 'Post Link', 'Message Date'])  # Записываем заголовки

        async with app:
            async for dialog in app.get_dialogs():
                chat_id = dialog.chat.id
                if chat_id < 0:  # Только группы и каналы
                    try:
                        async for message in app.get_chat_history(chat_id):
                            # Преобразование даты сообщения в datetime
                            message_date = message.date  # message.date уже объект datetime
                            if not isinstance(message_date, datetime):
                                print(f"Ошибка преобразования даты для сообщения {message.id}")
                                continue

                            # Проверяем дату сообщения
                            if message_date < date_from:  # Сравнение дат
                                print(f"Сообщение {message.link} ({message_date}) до указанной даты {date_from}, пропуск.")
                                break

                            # Обрабатываем только сообщения после указанной даты
                            print(f"Сообщение {message.link} ({message_date}) после указанной даты {date_from}, обработка.")
                            contacts, discount, link = process_message(message)
                            if contacts:
                                for contact in contacts:
                                    writer.writerow([contact, discount if discount else "", link if link else "", message_date])
                    except Exception as e:
                        print(f"Ошибка при получении сообщений из чата {chat_id}: {e}")

# Запуск
app.run(main())
