import enum


@enum.unique
class USER_SELF(enum.Enum):
    READ = "user_self_read"
    CREATE = "user_self_create"
    UPDATE = "user_self_update"
    DELETE = "user_self_delete"
    SET_ROLE = "user_self_set_role"


@enum.unique
class USER_ALL(enum.Enum):
    READ = "user_all_read"
    CREATE = "user_all_create"
    UPDATE = "user_all_update"
    DELETE = "user_all_delete"
    SET_ROLE = "user_all_set_role"


@enum.unique
class ROLE_SELF(enum.Enum):
    READ = "role_self_read"
    CREATE = "role_self_create"
    UPDATE = "role_self_update"
    DELETE = "role_self_delete"
    SET_PERMIT = "role_self_set_permit"


@enum.unique
class ROLE_ALL(enum.Enum):
    READ = "role_all_read"
    CREATE = "role_all_create"
    UPDATE = "role_all_update"
    DELETE = "role_all_delete"
    SET_PERMIT = "role_all_set_permit"


@enum.unique
class PERMISSION(enum.Enum):
    READ = "permission_read"
    CREATE = "permission_create"
    UPDATE = "permission_update"
    DELETE = "permission_delete"


DEFAULT_PERMISSIONS = {
    "user_self": USER_SELF,
    "user_all": USER_ALL,
    "role_self": ROLE_SELF,
    "role_all": ROLE_ALL,
    "permission": PERMISSION
}
