from aiohttp.web_app import Application
from aiohttp_cors import CorsConfig


def setup_routes(app: Application, cors: CorsConfig):
    from kts_backend.admin.routes import setup_routes as admin_setup_routes

    admin_setup_routes(app, cors)
