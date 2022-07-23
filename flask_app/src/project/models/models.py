import secrets
import uuid
from datetime import datetime, timedelta
from http import HTTPStatus

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from werkzeug.security import check_password_hash, generate_password_hash
from flask import abort

from project import database
from project.core.roles import USER_DEFAULT_ROLE


# ----------------
# Mixin  Classes
# ----------------


class IDMixin(object):
    id = database.Column(UUID(as_uuid=True),
                         primary_key=True,
                         default=uuid.uuid4,
                         unique=True, nullable=False)


class CreatedMixin(object):
    created = database.Column(database.DateTime,
                              default=func.now())


class CreatedModifiedMixin(CreatedMixin):
    modified = database.Column(database.DateTime,
                               server_default=func.now(),
                               onupdate=func.current_timestamp())


# ----------------
# Data  Classes
# ----------------
class User(IDMixin, CreatedModifiedMixin, database.Model):
    __tablename__ = 'users'

    email = database.Column(database.String,
                            unique=True,
                            nullable=False)

    password_hashed = database.Column(database.String(128),
                                      nullable=False)

    auth_token = database.Column(database.String(64),
                                 index=True)

    auth_token_expiration = database.Column(database.DateTime)

    disabled = database.Column(database.Boolean,
                               nullable=False,
                               default=False)

    role_id = database.Column(UUID(as_uuid=True),
                              database.ForeignKey('roles.id'))

    def __init__(self, email: str, password_plaintext: str, disabled: bool = False, role_id: str = USER_DEFAULT_ROLE):
        """Create a new User object."""
        self.email = email
        self.password_hashed = self._generate_password_hash(password_plaintext)
        self.disabled = disabled

        if role_id == USER_DEFAULT_ROLE:
            role_superuser = database.session.query(Role).filter(Role.name == USER_DEFAULT_ROLE).first()
            self.role_id = role_superuser.id
        else:
            self.role_id = role_id

    def is_password_correct(self, password_plaintext: str):
        return check_password_hash(self.password_hashed, password_plaintext)

    def set_password(self, password_plaintext: str):
        self.password_hashed = self._generate_password_hash(password_plaintext)

    def disable(self):
        self.disabled = True

    def is_enabled(self) -> bool:
        return not self.disabled

    @staticmethod
    def _generate_password_hash(password_plaintext):
        return generate_password_hash(password_plaintext)

    def generate_auth_token(self):
        self.auth_token = secrets.token_urlsafe()
        self.auth_token_expiration = datetime.utcnow() + timedelta(minutes=60)
        return self.auth_token

    @staticmethod
    def verify_auth_token(auth_token):
        user = User.query.filter_by(auth_token=auth_token).first()
        if user and user.auth_token_expiration > datetime.utcnow():
            return user

    def revoke_auth_token(self):
        self.auth_token_expiration = datetime.utcnow()

    def __repr__(self):
        return f'<User: {self.email}>'


class Role(IDMixin, CreatedModifiedMixin, database.Model):
    __tablename__ = 'roles'

    name = database.Column(database.String,
                           unique=True,
                           nullable=False)

    def __init__(self, name: str):
        """Create a new Role object."""
        self.name = name

    def __repr__(self):
        return f'<Role {self.name}>'


class Permission(IDMixin, database.Model):
    __tablename__ = 'permissions'

    name = database.Column(database.String,
                           unique=True,
                           nullable=False)

    def __init__(self, name: str):
        """Create a new Permission object."""
        self.name = name

    def __repr__(self):
        return f'<Permission {self.name}>'


class RolePermission(IDMixin, CreatedMixin, database.Model):
    __tablename__ = 'role_permission'

    role_id = database.Column(UUID(as_uuid=True),
                              database.ForeignKey('roles.id'),
                              nullable=False)

    permission_id = database.Column(UUID(as_uuid=True),
                                    database.ForeignKey('permissions.id'),
                                    nullable=False)

    value = database.Column(database.String,
                            nullable=False)

    def __init__(self, role_id: str, permission_id: str, value: str):
        """Create a new RolePermission object."""
        self.role_id = role_id
        self.permission_id = permission_id
        self.value = value

    @staticmethod
    def set_permissions_to_role(role_id: str, permission_list: list):
        for permission_dict in permission_list:
            permission_id = permission_dict['id']
            permission_value = permission_dict.get('value', 'true')
            permission = Permission.query.get(permission_id)
            if not permission:
                abort(HTTPStatus.NOT_FOUND, f'permission with id={permission_id} not found')
            role_permission = RolePermission(role_id=role_id, permission_id=permission_id, value=permission_value)
            database.session.add(role_permission)

    def __repr__(self):
        return f'<RolePermission {self.id}>'


class UserHistory(IDMixin, CreatedMixin, database.Model):
    __tablename__ = 'user_history'

    user_id = database.Column(UUID(as_uuid=True),
                              database.ForeignKey('users.id', ondelete='CASCADE'),
                              nullable=False,
                              index=True)

    activity = database.Column(database.String,
                               unique=False,
                               nullable=False)

    def __init__(self, user_id: str, activity: str):
        self.user_id = user_id
        self.activity = activity

    def __repr__(self):
        return f'<UserHistory {self.id}>'
