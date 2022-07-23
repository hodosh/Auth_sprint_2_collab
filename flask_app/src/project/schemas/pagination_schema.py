from project import ma


class PaginationSchema(ma.Schema):
    page = ma.Integer(default=1)
    per_page = ma.Integer(default=10)
