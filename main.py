import json
import os
import sqlite3
import base64
import time
import requests
from requests.exceptions import ConnectionError, ConnectTimeout

"""
5. Получить статус что вацап подключен и записать имя и телефон
6. Отправить сообщение 
7. Загрузить код в гит и прислать вместе со скрином  отправленного сообщения в переписку. 
"""

base_url = os.environ["BASE_URL"]


def get_chat():
    """
    Запрашивает свободный чат
    :return: id: int, token: str
    """
    session = requests.session()

    query_params = {
        "crm": "TEST",
        "domain": "test"
    }

    headers = {
        "X-Tasktest-Token": os.environ["AUTH_TOKEN"]
    }

    try:
        response = session.post(url=f"{base_url}/chat/spare",
                                headers=headers,
                                params=query_params,
                                timeout=3)

        json_data = json.loads(response.text)

        id = json_data['id']
        token = json_data['token']

        return id, token

    except ConnectTimeout as e:
        print(e)
    except ConnectionError as e:
        print(e)

    session.close()

    print(json.dumps(json_data, indent=2))

    return json_data["id"], json_data["token"]


def save_to_db(id: int, token: str):
    """
    Записывает полученные id и token в БД
    :param id: int
    :param token: str
    :return:
    """
    db = sqlite3.connect("db.sqlite")
    cursor = db.cursor()
    try:
        db_create_query = """CREATE TABLE chat (id integer PRIMARY  KEY, token TEXT NOT NULL)"""
        cursor.execute(db_create_query)
    except sqlite3.OperationalError:
        pass

    try:
        insert_query = f"""INSERT INTO chat (id, token) VALUES ({id}, '{token}')"""
        cursor.execute(insert_query)
    except sqlite3.IntegrityError:
        pass

    db.commit()
    cursor.close()


def get_chat_state(chat_id: int, chat_token: str):
    """
    Получает текущий статус чата
    :param chat_id: int
    :param chat_token: str
    :return: {}
    """
    session = requests.session()

    query_params = {
        "full": 1,
        "token": chat_token
    }

    headers = {
        "X-Tasktest-Token": os.environ["AUTH_TOKEN"]
    }

    try:
        response = session.get(url=f"{base_url}/instance{chat_id}/status",
                               headers=headers,
                               params=query_params)

        return json.loads(response.text)
    except ConnectTimeout as e:
        print(e)
    except ConnectionError as e:
        print(e)

    session.close()


def save_qrcode_to_file(filename: str, data: str):
    qr_code_data = data.split(",")
    with open("qrcode.png", "wb") as f:
        print(f.write(base64.b64decode(qr_code_data[1])))


if __name__ == '__main__':
    # chat_id, chat_token = get_chat()
    chat_id = 10
    chat_token = "7XImPoynNl0CvWH1"
    save_to_db(chat_id, chat_token)
    chat_data = get_chat_state(chat_id=chat_id, chat_token=chat_token)

    # wait for "got qr code" state
    try_count = 0
    while chat_data['state'] != 'got qr code':
        chat_data = get_chat_state(chat_id=chat_id, chat_token=chat_token)
        try_count += 1
        time.sleep(1)
        if try_count == 10:
            raise Exception

    save_qrcode_to_file("db.sqlite", chat_data["qrCode"])

    print("QR ready. Waiting for scan")
    input("Press Enter to continue...")

    chat_data = get_chat_state(chat_id=chat_id, chat_token=chat_token)

    print(json.dumps(chat_data, indent=2))

