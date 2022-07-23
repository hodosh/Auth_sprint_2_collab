from http import HTTPStatus

from apifairy import response, body
from flask import abort
from flask_jwt_extended import jwt_required

from project import database
from project.core.permissions import ROLE_SELF, ROLE_ALL
from project.extensions import check_access
from project.models.models import Role, RolePermission
from project.schemas import role_schema, new_role_schema
from project.schemas.role import ShortRoleSchema
from . import role_api_blueprint


@role_api_blueprint.route('/create', methods=['POST'])
@jwt_required()
@body(new_role_schema)
@response(role_schema, 200)
@check_access([ROLE_SELF.CREATE, ROLE_ALL.CREATE])
def create_role(kwargs: dict):
    """Create new role"""
    if not kwargs:
        abort(HTTPStatus.EXPECTATION_FAILED, 'cannot find name and permissions in data!')
    name = kwargs['name']
    permissions = kwargs['permissions']
    role = Role.query.filter_by(name=name).first()
    if role:
        abort(HTTPStatus.EXPECTATION_FAILED, f'role with name={name} exists')
    role = Role(name=name)

    database.session.add(role)
    database.session.commit()

    RolePermission.set_permissions_to_role(role.id, permissions)

    database.session.commit()

    return role


@role_api_blueprint.route('/<role_id>', methods=['POST'])
@jwt_required()
@body(new_role_schema)
@response(role_schema, 200)
@check_access([ROLE_SELF.UPDATE, ROLE_ALL.UPDATE])
def update_role(kwargs: dict, role_id: str):
    """Update role & its permissions"""
    if not kwargs:
        abort(HTTPStatus.EXPECTATION_FAILED, 'cannot find name and permissions in data!')
    name = kwargs['name']
    role = Role.query.get(role_id)
    permission_list = kwargs['permissions']
    if not role:
        abort(HTTPStatus.NOT_FOUND, f'role with role_id={role_id} not found')
    if name:
        role.name = name

    if permission_list:
        RolePermission.set_permissions_to_role(role.id, permission_list)

    database.session.commit()

    return role


@role_api_blueprint.route('/', methods=['GET'])
@jwt_required()
@response(ShortRoleSchema(many=True), 200)
@check_access([ROLE_SELF.READ, ROLE_ALL.READ])
def get_all_roles():
    """List all roles"""
    roles = Role.query.order_by(Role.name).all()
    if not roles:
        abort(HTTPStatus.NOT_FOUND, 'roles not found')

    return roles


@role_api_blueprint.route('/<role_id>', methods=['GET'])
@jwt_required()
@response(role_schema, 200)
@check_access([ROLE_SELF.READ, ROLE_ALL.READ])
def get_role(role_id: str):
    """Get role info"""
    role = Role.query.get(role_id)
    if not role:
        abort(HTTPStatus.NOT_FOUND, f'role with role_id={role_id} not found')

    role_permissions = RolePermission.query.filter_by(role_id=role_id).all()

    return dict(id=role.id, name=role.name, created=role.created, permissions=role_permissions)


@role_api_blueprint.route('/<role_id>', methods=['DELETE'])
@jwt_required()
@response(role_schema, 200)
@check_access([ROLE_SELF.DELETE, ROLE_ALL.DELETE])
def delete_role(role_id: str):
    """Delete role"""
    role = Role.query.get(role_id)
    if not role:
        abort(HTTPStatus.NOT_FOUND, f'role with role_id={role_id} not found')

    role_permissions = RolePermission.query.filter_by(role_id=role_id).all()
    for role_permission in role_permissions:
        database.session.delete(role_permission)
    database.session.commit()

    database.session.delete(role)
    database.session.commit()

    return role
