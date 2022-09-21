import typing

from app.smart_peoples.views import SessionsListView, PlayersStatusesListView

if typing.TYPE_CHECKING:
    from app.web.app import Application


def setup_routes(app: "Application"):
    app.router.add_view("/game.list_sessions", SessionsListView)
    app.router.add_view("/game.list_statuses_by_session", PlayersStatusesListView)
