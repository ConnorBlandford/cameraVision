from __future__ import annotations

from pathlib import Path

from flask import Flask

from camera_vision import PROJECT_ROOT, load_config
from camera_vision.web.routes import register_routes


def create_app(config: dict | None = None) -> Flask:
    cfg = config or load_config()

    app = Flask(
        __name__,
        template_folder=str(Path(__file__).parent / "templates"),
        static_folder=str(Path(__file__).parent / "static"),
    )
    app.config["CAMERA_VISION_CONFIG"] = cfg
    app.config["CAMERA_VISION_ROOT"] = PROJECT_ROOT

    register_routes(app)
    return app
