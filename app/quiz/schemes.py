from marshmallow import Schema, fields

from app.web.schemes import OkResponseSchema


class ThemeSchema(Schema):
    id = fields.Int(required=False)
    title = fields.Str(required=True)


class AnswerSchema(Schema):
    title = fields.Str(required=True)
    is_correct = fields.Bool(required=True)


class QuestionSchema(Schema):
    id = fields.Int(dump_only=True)
    title = fields.Str(required=True)
    theme_id = fields.Int(required=True)
    answers = fields.Nested(AnswerSchema, many=True)


class QuestionResponseSchema(OkResponseSchema):
    data = fields.Nested(QuestionSchema)


class ThemeListSchema(Schema):
    themes = fields.Nested(ThemeSchema, many=True)


class ThemeListResponseSchema(OkResponseSchema):
    data = fields.Nested(ThemeListSchema)


class ThemeIdSchema(OkResponseSchema):
    data = fields.Nested(ThemeSchema)


class ListQuestionSchema(Schema):
    questions = fields.Nested(QuestionSchema, many=True)


class ListQuestionResponseSchema(OkResponseSchema):
    data = fields.Nested(ListQuestionSchema)


class QuestionGetRequestSchema(Schema):
    theme_id = fields.Int(required=False)
