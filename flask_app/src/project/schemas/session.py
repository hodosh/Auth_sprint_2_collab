from project import ma


class HistorySchema(ma.Schema):
    activity = ma.String()
    created = ma.DateTime()


class PaginatedHistorySchema(ma.Schema):
    history = ma.List(ma.Nested(HistorySchema))
    page = ma.Integer(default=1)
    per_page = ma.Integer(default=10)


class LoginSchema(ma.Schema):
    email = ma.String()
    password = ma.String()
