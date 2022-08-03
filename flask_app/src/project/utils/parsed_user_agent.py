from ua_parser import user_agent_parser
from werkzeug.user_agent import UserAgent
from werkzeug.utils import cached_property

from project import settings


class ParsedUserAgent(UserAgent):
    @cached_property
    def _details(self):
        return user_agent_parser.Parse(self.string)

    @property
    def platform(self) -> str:
        return self._details['os']['family']

    @property
    def browser(self) -> str:
        return self._details['user_agent']['family']

    @property
    def version(self) -> str:
        return '.'.join(
            part
            for key in ('major', 'minor', 'patch')
            if (part := self._details['user_agent'][key]) is not None
        )


def get_platform(user_agent: str) -> str:
    """
    Метод вычитки платформы, с которой поступил запрос
    @param user_agent: строка user_agent из запроса
    @return: тип платформы в соответствии с описанными ограничениями
    """
    platform = ParsedUserAgent(user_agent).platform.lower()
    if platform not in settings.PLATFORMS_TUPLE:
        return 'other'

    return platform
