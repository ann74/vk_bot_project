import typing
from aiohttp_cors import CorsConfig

if typing.TYPE_CHECKING:
    from kts_backend.web.app import Application


def setup_routes(app: "Application", cors: CorsConfig):
    from kts_backend.admin.views import AdminLoginView, QuestionAddView, QuestionListView, Hello

    app.router.add_view("/admin.login", AdminLoginView)
    app.router.add_view("/admin.add_question", QuestionAddView)
    app.router.add_view("/admin.list_questions", QuestionListView)
    cors.add(app.router.add_route("GET", "/", Hello))
