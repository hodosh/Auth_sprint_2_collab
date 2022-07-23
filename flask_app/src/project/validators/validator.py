from abc import ABC, abstractmethod


class Validator(ABC):
    @staticmethod
    @abstractmethod
    def validate(**kwargs) -> bool:
        pass
