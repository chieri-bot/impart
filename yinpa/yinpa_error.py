
class YinpaError(Exception):
    def __init__(self, message, *args):
        self.message = message
        super().__init__(*args)

    def __str__(self):
        return self.message

    def __repr__(self):
        return self.__str__()

class YinpaValueError(YinpaError):
    def __init__(self, message, *args):
        super().__init__(message, *args)
        self.message = f"{self.__class__.__name__}: {message}"

class YinpaUserExistsError(YinpaError):
    pass

class YinpaUserError(YinpaError):
    pass

class SexNotFoundError(YinpaError):
    def __init__(self, value):
        super().__init__(f"Sex type: {value} not found.")

class BodyNotFoundError(YinpaError):
    def __init__(self, value):
        super().__init__(f"Body type: {value} not found.")

class RaceNotFoundError(YinpaError):
    def __init__(self, value):
        super().__init__(f"Race type: {value} not found.")

class ActionNotFoundError(YinpaError):
    def __init__(self, value):
        super().__init__(f"Action type: {value} not found.")

class UserNotFoundError(YinpaUserError):
    def __init__(self, value):
        super().__init__(f"用户: {value} 还未加入 yinpa." if isinstance(value, int) else value)

class ItemNotFoundError(YinpaError):
    def __init__(self, value):
        super().__init__(f"Item: {value} not found.")
