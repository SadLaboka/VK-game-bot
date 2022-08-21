from marshmallow import Schema, fields

from app.web.schemes import OkResponseSchema


class ThemeSchema(Schema):
    id = fields.Int(required=False)
    title = fields.Str(required=True)


class QuestionSchema(Schema):
    pass


class AnswerSchema(Schema):
    pass


class ThemeListSchema(Schema):
    pass


class ThemeIdSchema(OkResponseSchema):
    data = fields.Nested(ThemeSchema)


class ListQuestionSchema(Schema):
    pass
