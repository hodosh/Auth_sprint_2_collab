from project import ma


class MessageSchema(ma.Schema):
    message = ma.String()
