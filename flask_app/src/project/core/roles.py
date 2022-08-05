from project.core.permissions import (
    USER_SELF,
    USER_ALL,
    ROLE_SELF,
    ROLE_ALL,
    PERMISSION,
)

SUPERUSER_ROLE = {
    USER_SELF.READ: True,
    USER_SELF.CREATE: True,
    USER_SELF.UPDATE: True,
    USER_SELF.DELETE: False,
    USER_SELF.SET_ROLE: False,

    USER_ALL.READ: True,
    USER_ALL.CREATE: True,
    USER_ALL.UPDATE: True,
    USER_ALL.DELETE: True,
    USER_ALL.SET_ROLE: True,

    ROLE_SELF.READ: True,
    ROLE_SELF.CREATE: True,
    ROLE_SELF.UPDATE: True,
    ROLE_SELF.DELETE: True,
    ROLE_SELF.SET_PERMIT: True,

    ROLE_ALL.READ: True,
    ROLE_ALL.CREATE: True,
    ROLE_ALL.UPDATE: True,
    ROLE_ALL.DELETE: True,
    ROLE_ALL.SET_PERMIT: True,

    PERMISSION.READ: True,
    PERMISSION.CREATE: True,
    PERMISSION.UPDATE: True,
    PERMISSION.DELETE: True
}

USER_ROLE = {
    USER_SELF.READ: True,
    USER_SELF.CREATE: True,
    USER_SELF.UPDATE: True,
    USER_SELF.DELETE: True,
    USER_SELF.SET_ROLE: False,

    USER_ALL.READ: False,
    USER_ALL.CREATE: False,
    USER_ALL.UPDATE: False,
    USER_ALL.DELETE: False,
    USER_ALL.SET_ROLE: False,

    ROLE_SELF.READ: True,
    ROLE_SELF.CREATE: False,
    ROLE_SELF.UPDATE: False,
    ROLE_SELF.DELETE: False,
    ROLE_SELF.SET_PERMIT: False,

    ROLE_ALL.READ: False,
    ROLE_ALL.CREATE: False,
    ROLE_ALL.UPDATE: False,
    ROLE_ALL.DELETE: False,
    ROLE_ALL.SET_PERMIT: False,

    PERMISSION.READ: True,
    PERMISSION.CREATE: False,
    PERMISSION.UPDATE: False,
    PERMISSION.DELETE: False
}

NON_REGISTERED = {
    USER_SELF.READ: True,
    USER_SELF.CREATE: True,
    USER_SELF.UPDATE: False,
    USER_SELF.DELETE: False,
    USER_SELF.SET_ROLE: False,

    USER_ALL.READ: False,
    USER_ALL.CREATE: False,
    USER_ALL.UPDATE: False,
    USER_ALL.DELETE: False,
    USER_ALL.SET_ROLE: False,

    ROLE_SELF.READ: False,
    ROLE_SELF.CREATE: False,
    ROLE_SELF.UPDATE: False,
    ROLE_SELF.DELETE: False,
    ROLE_SELF.SET_PERMIT: False,

    ROLE_ALL.READ: False,
    ROLE_ALL.CREATE: False,
    ROLE_ALL.UPDATE: False,
    ROLE_ALL.DELETE: False,
    ROLE_ALL.SET_PERMIT: False,

    PERMISSION.READ: False,  # аноним не сможет сделать запрос на свои права!
    PERMISSION.CREATE: False,
    PERMISSION.UPDATE: False,
    PERMISSION.DELETE: False
}

# Название ролей в базе данных
ROLE_SUPERUSER = "superuser"
ROLE_USER = "user"
ROLE_NON_REGISTERED = "non_registered"

#  При новой регистрации будет использована роль
USER_DEFAULT_ROLE = ROLE_USER

#
DEFAULT_ROLES = {
    ROLE_SUPERUSER: SUPERUSER_ROLE,
    ROLE_USER: USER_ROLE,
    ROLE_NON_REGISTERED: NON_REGISTERED
}

