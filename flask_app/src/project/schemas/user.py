from project import ma


class NewUserSchema(ma.Schema):
    """Schema defining the attributes when creating a new user."""
    email = ma.String()
    password = ma.String()
    password_confirm = ma.String()


class UpdateUserSchema(ma.Schema):
    """Schema defining the attributes when creating a new user."""
    email = ma.String()
    old_password = ma.String()
    new_password = ma.String()
    new_password_confirm = ma.String()


class UserSchema(ma.Schema):
    """Schema defining the attributes of a user."""
    id = ma.String()
    email = ma.String()
    disabled = ma.Boolean()


class UserRole(ma.Schema):
    """Schema defining the attributes of a user."""
    user_id = ma.String()
    role_id = ma.String()
