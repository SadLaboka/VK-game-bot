import pytest
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select

from app.quiz.models import Answer, AnswerModel, Question, QuestionModel, Theme
from app.store import Store
from tests.quiz import question2dict
from tests.utils import check_empty_table_exists
from tests.utils import ok_response


class TestQuestionsStore:
    async def test_table_exists(self, cli):
        await check_empty_table_exists(cli, "questions")
        await check_empty_table_exists(cli, "answers")

    async def test_create_question(
        self, cli, store: Store, theme_1: Theme, answers: list[Answer]
    ):
        question_title = "title"
        question = await store.quizzes.create_question(
            question_title, theme_1.id, answers
        )
        assert type(question) is Question

        async with cli.app.database.session() as session:
            res = await session.execute(select(QuestionModel))
            questions = res.scalars().all()

            res = await session.execute(select(AnswerModel))
            db_answers = res.scalars().all()

        assert len(questions) == 1
        db_question = questions[0]

        assert db_question.title == question_title

        assert len(db_answers) == len(answers)
        for have, expected in zip(db_answers, answers):
            assert have.title == expected.title
            assert have.is_correct == expected.is_correct

    async def test_create_question_no_theme(
        self, cli, store: Store, answers: list[Answer]
    ):
        question_title = "title"
        with pytest.raises(IntegrityError) as exc_info:
            await store.quizzes.create_question(question_title, 1, answers)
        assert exc_info.value.orig.pgcode == "23503"

    async def test_create_question_none_theme_id(
        self, cli, store: Store, answers: list[Answer]
    ):
        question_title = "title"
        with pytest.raises(IntegrityError) as exc_info:
            await store.quizzes.create_question(question_title, None, answers)
        assert exc_info.value.orig.pgcode == "23502"

    async def test_create_question_unique_title_constraint(
        self, cli, store: Store, question_1: Question, answers: list[Answer]
    ):
        with pytest.raises(IntegrityError) as exc_info:
            await store.quizzes.create_question(
                question_1.title, question_1.theme_id, answers
            )
        assert exc_info.value.orig.pgcode == "23505"

    async def test_get_question_by_title(self, cli, store: Store, question_1: Question):
        assert question_1 == await store.quizzes.get_question_by_title(question_1.title)

    async def test_list_questions(
        self, cli, store: Store, question_1: Question, question_2: Question
    ):
        questions = await store.quizzes.list_questions()
        assert questions == [question_1, question_2]

    async def test_check_cascade_delete(self, cli, question_1: Question):
        async with cli.app.database.session() as session:
            await session.execute(
                delete(QuestionModel).where(QuestionModel.id == question_1.id)
            )
            await session.commit()

            res = await session.execute(
                select(AnswerModel).where(AnswerModel.question_id == question_1.id)
            )
            db_answers = res.scalars().all()

        assert len(db_answers) == 0


class TestQuestionAddView:
    async def test_success(self, authed_cli, theme_1: Theme):
        resp = await authed_cli.post(
            "/quiz.add_question",
            json={
                "title": "How many legs does an octopus have?",
                "theme_id": theme_1.id,
                "answers": [
                    {
                        "title": "2",
                        "is_correct": False,
                    },
                    {
                        "title": "8",
                        "is_correct": True,
                    },
                ],
            },
        )
        assert resp.status == 200
        data = await resp.json()
        assert data == ok_response(
            data=question2dict(
                Question(
                    id=data["data"]["id"],
                    title="How many legs does an octopus have?",
                    theme_id=1,
                    answers=[
                        Answer(title="2", is_correct=False),
                        Answer(title="8", is_correct=True),
                    ],
                )
            )
        )

    async def test_unauthorized(self, cli):
        resp = await cli.post(
            "/quiz.add_question",
            json={
                "title": "How many legs does an octopus have?",
                "theme_id": 1,
                "answers": [
                    {
                        "title": "2",
                        "is_correct": False,
                    },
                    {
                        "title": "8",
                        "is_correct": True,
                    },
                ],
            },
        )
        assert resp.status == 401
        data = await resp.json()
        assert data["status"] == "unauthorized"

    async def test_theme_not_found(self, authed_cli):
        resp = await authed_cli.post(
            "/quiz.add_question",
            json={
                "title": "How many legs does an octopus have?",
                "theme_id": 1,
                "answers": [
                    {
                        "title": "2",
                        "is_correct": False,
                    },
                    {
                        "title": "8",
                        "is_correct": True,
                    },
                ],
            },
        )
        assert resp.status == 404

    async def test_all_answers_are_correct(self, authed_cli, theme_1):
        resp = await authed_cli.post(
            "/quiz.add_question",
            json={
                "title": "How many legs does an octopus have?",
                "theme_id": theme_1.id,
                "answers": [
                    {
                        "title": "2",
                        "is_correct": True,
                    },
                    {
                        "title": "8",
                        "is_correct": True,
                    },
                ],
            },
        )
        assert resp.status == 400

    async def test_all_answers_are_incorrect(self, authed_cli, theme_1):
        resp = await authed_cli.post(
            "/quiz.add_question",
            json={
                "title": "How many legs does an octopus have?",
                "theme_id": theme_1.id,
                "answers": [
                    {
                        "title": "2",
                        "is_correct": False,
                    },
                    {
                        "title": "8",
                        "is_correct": False,
                    },
                ],
            },
        )
        assert resp.status == 400

    async def test_only_one_answer(self, authed_cli, theme_1):
        resp = await authed_cli.post(
            "/quiz.add_question",
            json={
                "title": "How many legs does an octopus have?",
                "theme_id": theme_1.id,
                "answers": [
                    {
                        "title": "2",
                        "is_correct": True,
                    },
                ],
            },
        )
        assert resp.status == 400
        data = await resp.json()
        assert data["status"] == "bad_request"


class TestQuestionListView:
    async def test_unauthorized(self, cli):
        resp = await cli.get("/quiz.list_questions")
        assert resp.status == 401
        data = await resp.json()
        assert data["status"] == "unauthorized"

    async def test_empty(self, authed_cli):
        resp = await authed_cli.get("/quiz.list_questions")
        assert resp.status == 200
        data = await resp.json()
        assert data == ok_response(data={"questions": []})

    async def test_one_question(self, authed_cli, question_1):
        resp = await authed_cli.get("/quiz.list_questions")
        assert resp.status == 200
        data = await resp.json()
        assert data == ok_response(data={"questions": [question2dict(question_1)]})

    async def test_several_questions(
        self, authed_cli, question_1: Question, question_2
    ):
        resp = await authed_cli.get("/quiz.list_questions")
        assert resp.status == 200
        data = await resp.json()
        assert data == ok_response(
            data={"questions": [question2dict(question_1), question2dict(question_2)]}
        )
