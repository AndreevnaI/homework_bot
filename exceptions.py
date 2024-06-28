class BaseErorr(Exception):
    """Базовый класс ошибки."""

    def __init__(self, msg, code):
        """Конструктор класса."""
        self.msg = msg
        self.code = code


class MessageError(BaseErorr):
    """Ошибка при отправке сообщения."""

    pass


class ResponseError(BaseErorr):
    """Ошибка в ответе."""

    pass


class NameKeyError(BaseErorr):
    """Отсутствие ожидаемого ключа в ответе."""

    pass
