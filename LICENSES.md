# Third-party licenses

This project only uses permissively-licensed software. No GPL, LGPL, AGPL, or other copyleft licences are permitted, per the IP requirements in [system_description.md](system_description.md).

Generate a current, machine-derived inventory at any time with:

```bat
.venv\Scripts\activate
pip-licenses --format=markdown --with-urls --with-license-file=false
```

Fail the build if any copyleft appears:

```bat
pip-licenses --fail-on="GNU General Public License (GPL);GNU Lesser General Public License (LGPL);GNU Affero General Public License v3 (AGPL-3.0);GNU Affero General Public License v3 or later (AGPLv3+)"
```

## Direct dependencies

| Package | Licence | Notes |
|---|---|---|
| Flask | BSD-3-Clause | |
| opencv-contrib-python | Apache-2.0 | |
| numpy | BSD-3-Clause | |
| PyYAML | MIT | |
| supervision | MIT | |
| rfdetr | Apache-2.0 | **Only sizes N / S / M / L are used.** The XL / 2XL models are PML 1.0 (a restrictive custom licence) and are explicitly disallowed in [camera_vision/detection/detector.py](camera_vision/detection/detector.py) (`_ALLOWED_SIZES`). |
| Pillow | MIT-CMU (HPND) | |
| pytest | MIT | Dev only. |
| pip-licenses | MIT | Dev only, for the audit above. |

## Notably excluded

- **Ultralytics YOLOv8 / YOLOv11** — AGPL-3.0. Copyleft, disallowed.
- **RF-DETR XL / 2XL** — PML 1.0. Not Apache-2.0; disallowed.
