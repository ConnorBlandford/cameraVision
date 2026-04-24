from camera_vision.sources.base import CameraSource, StereoFrame
from camera_vision.sources.webcam import WebcamSource
from camera_vision.sources.stereo_uvc import StereoUVCSource


def build_source(config: dict) -> CameraSource:
    cam = config["camera"]
    kind = cam["source"]
    if kind == "webcam":
        w = cam["webcam"]
        return WebcamSource(
            device_index=w["device_index"],
            width=w["width"],
            height=w["height"],
        )
    if kind == "stereo_uvc":
        s = cam["stereo_uvc"]
        return StereoUVCSource(
            left_index=s["left_index"],
            right_index=s["right_index"],
            width=s["width"],
            height=s["height"],
        )
    raise ValueError(f"Unknown camera source: {kind}")


__all__ = ["CameraSource", "StereoFrame", "WebcamSource", "StereoUVCSource", "build_source"]
