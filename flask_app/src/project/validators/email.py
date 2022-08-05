import re

from project.validators.validator import Validator


class EmailValidator(Validator):
    @staticmethod
    def validate(**kwargs) -> bool:
        regex = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"

        email = kwargs['email']
        if re.search(regex, email):
            return True
        else:
            return False
