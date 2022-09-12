from app.base.base_accessor import BaseAccessor


class DifficultyAccessor(BaseAccessor):
    async def connect(self, app: "Application"):
        title = app.config.difficulties.title
        right_answers_count = app.config.difficulties.right_answers_to_win
        wrong_answers_count = app.config.difficulties.wrong_answers_to_lose
        pass
