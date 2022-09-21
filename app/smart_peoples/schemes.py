from marshmallow import Schema, fields

from app.web.schemes import OkResponseSchema


class DifficultySchema(Schema):
    id = fields.Int(required=True)
    title = fields.Str(required=True)
    right_answers_to_win = fields.Int(required=True)
    wrong_answers_to_lose = fields.Int(required=True)


class PlayerSchema(Schema):
    id = fields.Int(required=True)
    vk_id = fields.Int(required=True)
    first_name = fields.Str(required=True)
    last_name = fields.Str(required=True)
    games_count = fields.Int(required=True)
    wins_count = fields.Int(required=True)
    loses_count = fields.Int(required=True)


class PlayerStatusSchema(Schema):
    id = fields.Int(required=True)
    session_id = fields.Int(required=True)
    player_id = fields.Int(required=True)
    difficulty_id = fields.Int(required=True)
    right_answers = fields.Int(required=True)
    wrong_answers = fields.Int(required=True)
    is_won = fields.Bool(required=True)
    is_lost = fields.Bool(required=True)
    difficulty = fields.Nested(DifficultySchema)
    player = fields.Nested(PlayerSchema)


class PlayerStatusResponseSchema(OkResponseSchema):
    data = fields.Nested(PlayerStatusSchema)


class SessionSchema(Schema):
    id = fields.Int(required=True)
    chat_id = fields.Int(required=True)
    started_by = fields.Int(required=True)
    status = fields.Str(required=True)
    response_time = fields.Int(required=True)
    session_duration = fields.Int(required=True)
    started_at = fields.DateTime(required=True)
    finished_at = fields.DateTime(required=False)
    winner_id = fields.Int(required=False)


class SessionResponseSchema(OkResponseSchema):
    data = fields.Nested(SessionSchema)


class PlayersStatusesGetRequestSchema(Schema):
    session_id = fields.Int(required=True)


class SessionGetRequestSchema(Schema):
    page = fields.Int(required=False)
