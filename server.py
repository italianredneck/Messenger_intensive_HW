"""
Серверное приложение для соединений
"""
import asyncio  # библиотека асинхронного выполнения функций
from asyncio import transports


class ClientProtocol(asyncio.Protocol):
    """Функция, которая будет возвращать объект на каждое новое подключение
    (описывает протокол взаимодействия с клиентом)"""
    login: str
    server: 'Server'  # ' ' - как обещание, что переменная сервер будет позже
    transport: transports.Transport  # транспортный уровень - передает бинарный код между компами

    def __init__(self, server: 'Server'):
        self.server = server
        self.login = None

    """ для создания след. 3х методов используется генератор (дабл Shift -> Generate -> Override Methods -> перечислены 
    все возможности классов, от которых наследуемся. Конкретно тут взяли только названия и вх.переменные"""

    def data_received(self, data: bytes):  # Что делать, когда пришли данные(data в байтах)
        decoded = data.decode()  # Расшифровка из байтов
        print(decoded)  # вывод расшифрованного

        if self.login is None:  # Проверка: если логин у клиента не существует
            # login:User
            if decoded.startswith("login:"):  # проверка сообщения на ниличие логина
                login = decoded.replace("login:", "").replace("\r\n", "")  # извлекаем логин
                for client in self.server.clients:  # проход по подключенным клиентам
                    if client != self:
                        if client.login == login:  # если логин уже есть на сервере
                            self.transport.write(f"Логин {login} занят, попробуйте другой".encode())
                            self.transport.close()  # Отключаем от сервера этого клиента
                self.login = login  # регаем новый логин
                self.transport.write(
                    f"Привет, {self.login}!".encode()  # привет новый пользователь. Кодируем т.к. отправляем
                )
                self.send_history()  # отправляем историю сообщений
        else:  # если логин есть - значит сообщение, и вызываем соотв. метод
            self.send_message(decoded)

    def send_message(self, message):
        format_string = f"<{self.login}> {message}"  # добавляем подпись сообщению
        self.server.log_messages.append(format_string)  # добавляем его в историю сервера
        encoded = format_string.encode()  # снова кодируем для отправки

        for client in self.server.clients:  # отправляем сообщение всем клиентам
            if client.login != self.login and client.login is not None:  # .. кроме того, кто отправил, и незареганых
                client.transport.write(encoded)  # отправляем

    def connection_made(self, transport: transports.Transport):  # Когда соединение установлено
        self.transport = transport  # сохраняем транспорт чтобы могли передавать сообщения
        self.server.clients.append(self)  # Добавим в список клиентов сервера успешно установленное соединение
        print("Соединение установлено")

    def connection_lost(self, exception):  # когда соединение потеряно
        self.server.clients.remove(self)
        print("Соединение разорвано")

    def send_history(self):
        self.transport.write(f"Последние 10 сообщений:\n".encode())
        for message in self.server.log_messages[-10:]:
            self.transport.write(f"{message}\n".encode())


class Server:  # Отвечает за передачу данных
    clients: list

    def __init__(self):
        self.clients = []  # при создании сервера пустой список клиентов
        self.log_messages = []  # история сообщений

    def create_protocol(self):
        return ClientProtocol(self)

    async def start(self):  # Запуск сервера
        loop = asyncio.get_running_loop()  # "специальный цикл событий" - некое хранилище, где лежат все задачи
        # на выполнение в асинхронном режиме // .get_running_loop() - получить запущенный цикл

        coroutine = await loop.create_server(  # await должен возвращать соединенние с сервером
            # // .create_server - создать сервер
            self.create_protocol,  # без скобок - передаем как переменную
            "127.0.0.1",
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()  # сервер, работай вечно


process = Server()
try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")  # обработка исключения, из сообщения понятно
