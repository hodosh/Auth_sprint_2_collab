from project import ma


class PermissionSchema(ma.Schema):
    id = ma.String()
    name = ma.String()


class NestedPermissionSchema(ma.Schema):
    id = ma.String()
    value = ma.String()


class ShortRoleSchema(ma.Schema):
    id = ma.String()
    name = ma.String()


class RoleSchema(ma.Schema):
    id = ma.String()
    name = ma.String()
    permissions = ma.List(ma.Nested(NestedPermissionSchema))
    created = ma.DateTime()


class NewRoleSchema(ma.Schema):
    name = ma.String()
    permissions = ma.List(ma.Nested(NestedPermissionSchema))
