from camera_vision import load_config
from camera_vision.web import create_app


def main() -> None:
    cfg = load_config()
    app = create_app(cfg)
    server = cfg["server"]
    app.run(host=server["host"], port=server["port"], debug=server["debug"], threaded=True)


if __name__ == "__main__":
    main()
