import click
from flask.cli import AppGroup

from project import database
from project.core.roles import ROLE_SUPERUSER
from project.models.models import User, Role
from project.validators.email import EmailValidator

user_cli = AppGroup('superuser')


@user_cli.command('create')
@click.argument("email", type=str, required=True)
@click.password_option()
def create_superuser(email, password) -> bool:
    if not EmailValidator.validate(email=email):
        print("Email is non valid")
        return False

    role_superuser = database.session.query(Role).filter(Role.name == ROLE_SUPERUSER).first()
    new_user = User(email=email, password_plaintext=password, role_id=role_superuser.id)
    database.session.add(new_user)
    database.session.commit()

    print("New user created")
    return True
