"""Generate a printable ChArUco calibration board from config/default.yaml.

Writes a PNG (with DPI metadata) and a PDF sized to the exact physical
dimensions of the board, so printers that respect page size will produce
squares of the configured millimetre length.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import yaml
from cv2 import aruco
from PIL import Image

MM_PER_INCH = 25.4
REPO_ROOT = Path(__file__).resolve().parents[1]


def load_board_config(config_path: Path) -> dict:
    with config_path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return cfg["calibration"]["board"]


def resolve_dictionary(name: str) -> int:
    attr = getattr(aruco, name, None)
    if attr is None:
        raise ValueError(f"Unknown ArUco dictionary: {name}")
    return attr


def generate(board_cfg: dict, dpi: int, out_dir: Path) -> tuple[Path, Path]:
    squares_x = int(board_cfg["squares_x"])
    squares_y = int(board_cfg["squares_y"])
    square_m = float(board_cfg["square_length_m"])
    marker_m = float(board_cfg["marker_length_m"])
    dict_name = str(board_cfg["dictionary"])

    if marker_m >= square_m:
        raise ValueError("marker_length_m must be smaller than square_length_m")

    dictionary = aruco.getPredefinedDictionary(resolve_dictionary(dict_name))
    board = aruco.CharucoBoard(
        (squares_x, squares_y), square_m, marker_m, dictionary
    )

    board_w_mm = squares_x * square_m * 1000.0
    board_h_mm = squares_y * square_m * 1000.0
    px_w = int(round(board_w_mm / MM_PER_INCH * dpi))
    px_h = int(round(board_h_mm / MM_PER_INCH * dpi))

    margin_px = int(round(5.0 / MM_PER_INCH * dpi))  # 5 mm quiet zone
    img = board.generateImage((px_w, px_h), marginSize=margin_px)

    stem = (
        f"charuco_{squares_x}x{squares_y}"
        f"_sq{int(square_m * 1000)}mm"
        f"_mk{int(marker_m * 1000)}mm"
        f"_{dict_name}"
    )
    png_path = out_dir / f"{stem}.png"
    pdf_path = out_dir / f"{stem}.pdf"

    pil = Image.fromarray(img)
    pil.save(png_path, dpi=(dpi, dpi))
    pil.save(pdf_path, "PDF", resolution=float(dpi))

    return png_path, pdf_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=REPO_ROOT / "config" / "default.yaml",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=REPO_ROOT / "config",
    )
    parser.add_argument("--dpi", type=int, default=300)
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    board_cfg = load_board_config(args.config)
    png_path, pdf_path = generate(board_cfg, args.dpi, args.out_dir)

    board_w_mm = board_cfg["squares_x"] * board_cfg["square_length_m"] * 1000.0
    board_h_mm = board_cfg["squares_y"] * board_cfg["square_length_m"] * 1000.0
    print(f"[OK] {png_path.relative_to(REPO_ROOT)}")
    print(f"[OK] {pdf_path.relative_to(REPO_ROOT)}")
    print(
        f"     {board_cfg['squares_x']}x{board_cfg['squares_y']} squares, "
        f"{board_w_mm:.1f} x {board_h_mm:.1f} mm @ {args.dpi} DPI"
    )
    print("     Print at 100% scale — measure a square to confirm 15.0 mm.")


if __name__ == "__main__":
    main()
