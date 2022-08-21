from marshmallow import Schema, fields

from app.web.schemes import OkResponseSchema


class AdminSchema(Schema):
    email = fields.String(required=True)


class AdminRequestSchema(AdminSchema):
    password = fields.String(required=True)


class AdminResponseDataSchema(AdminSchema):
    id = fields.Integer(required=True)


class AdminResponseSchema(OkResponseSchema):
    data = fields.Nested(AdminResponseDataSchema)
