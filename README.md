# Camera Vision

Stereo depth / target-detection system for two Inno-Maker U20CAM-10800P cameras, delivered as a local browser app (Flask + OpenCV). On a dev laptop without the stereo rig, the app falls back to the built-in webcam — a single frame is duplicated as both left and right, so the stereo code paths still run.

## Requirements

- Windows with the `py` launcher (Python 3.11–3.13 recommended; `rfdetr` / `torch` wheels may lag on 3.14)
- A working webcam at index 0 for dev, or two UVC cameras for the full rig

## Setup

```bat
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bat
.venv\Scripts\activate
python app.py
```

Then open `http://localhost:5050`. Port is configurable in [config/default.yaml](config/default.yaml) — the default is 5050 (not 5000) to avoid clashing with other local services.

## Tests

```bat
.venv\Scripts\activate
pytest
```

The non-detector tests (camera contract, manifest, calibration IO, class resolution) don't require `rfdetr` / `torch` to import.

## Configuration

Single YAML file: [config/default.yaml](config/default.yaml). Swap between webcam and stereo UVC by changing `camera.source` to `webcam` or `stereo_uvc`. The `camera.webcam.device_index` selects which OS camera to use; `camera.stereo_uvc.{left_index,right_index}` pick the two UVC devices for the real rig.

## Workflows

### Calibration
- ChArUco board (dimensions in config). Capture ≥ 15 varied poses per camera for intrinsics, then ≥ ~10 simultaneous pairs for extrinsics.
- Output: `data/calibrations/intrinsics-{left,right}.yaml` and `data/calibrations/extrinsics.yaml`, each carrying a metadata header (timestamp, user, RMS reprojection error, image size).

### Target detection
- UI starts a round, scans the scene (`data/scan_images/raw-*.jpg`), runs RF-DETR (`data/detection_annotation/detection-*.jpg`), then presents an interactive target-selection step. Auto-preselection is applied at `confidence_threshold + selection_delta`; the user can override per detection.
- Round lifecycle: `started → scanned → detections_made → targets_selected` (or `cancelled`/`failed`). The whole history lives in `data/manifest.json`.
- Target types not in the COCO vocab (e.g. `cork`) run the detector over everything and flag the round with `class_filter_applied: false` — a custom-trained model is the planned follow-up.

### Depth scanning
- Stub. Page reports whether extrinsics are available.

## Licensing

See [LICENSES.md](LICENSES.md). All direct and known transitive dependencies are permissive (Apache-2.0 / BSD / MIT / PSF). No GPL / LGPL / AGPL. RF-DETR's XL / 2XL variants (PML 1.0) are explicitly excluded; only the Apache-2.0 sizes N / S / M / L are used, gated in [camera_vision/detection/detector.py](camera_vision/detection/detector.py).
