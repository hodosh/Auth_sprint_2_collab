from project.validators.validator import Validator


class PasswordValidator(Validator):
    @staticmethod
    def validate(**kwargs) -> bool:
        if kwargs['password1'] == kwargs['password2']:
            return True
        else:
            return False
