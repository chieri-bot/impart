
class YinpaError(Exception):
    def __init__(self, message, *args):
        self.message = message
        super().__init__(*args)

class YinpaValueError(YinpaError):
    pass

class YinpaUserError(YinpaError):
    def __str__(self):
        return self.message

    def __repr__(self):
        return self.__str__()

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

class UserNotFoundError(YinpaError):
    def __init__(self, value):
        super().__init__(f"User: {value} not found.")
