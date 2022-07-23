from project import ma


class TokenSchema(ma.Schema):
    """Schema defining the attributes of a token."""
    token = ma.String()
