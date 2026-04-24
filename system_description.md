# System Description
Camera Vision uses two Inno-maker U20CAM-10800P cameras in a stereo depth setup.

The U20CAM-10800P is a native driver camera based on the UVC standard.

For this project python and opencv are used as a backbone for image collection and processing.

NOTE: For local testing, without stereo cameras, assume the laptop has a webcame and use this for the image source.

## System Components
The system contains the following components to faciliate calibration and operation.

0. User Interface
    - Serivce is delivered through a clean and simple local browser based application
        - Uses Flask for the interface to the browser application
    - Presents User the option to use available services
    - Presents status information such as calibration state (included last calibration time)
    - Include an easy to use toogle for theme (system is default, toogle for light or dark mode)
    - Make the app accessible considering text sizes and colour blindness


1. Calibration Service
    - Exposed through the User Interface
    - Operator Calibration Workflow
        - A 'current state' view which exposes raw images and calibrated images
        - Presents operator options to initate Intrinsics or Extrinsics calibration
    - Intrinsics Calibration Workflow
        - Guides the user through intrinsics calibration
        - Outputs a intrinsics calibration to a yaml file for subsequent useage
            - Include all relevant calibration properties
            - Include metadata such as:
                - Date and time of calibration
                - User name that performed the calibration
    - Extrinsics Calibraiton Workflow
        - Guides the user through extrinsics calibration
        - Outputs a extrinsics calibration to a yaml file for subsequent useage
            - Include all relevant calibration properties
            - Include metadata such as:
                - Date and time of calibration
                - User name that performed the calibration

2. Target Detection Service
    - Exposed through the User Interface
    - Uses intrinsics and extrinsics calibrations
    - Presents User with options for running a target detection round
        - Presents target type selection: Apples, Corks, Other - string input
        - Detection Confidence Thershold
    - Creates or updates a manifest of images taken with image metadata:
            - Each target detection round is assigned:
                - A unique identifier uuid
                - A status: 'started', 'scanned', 'detections_made', 'targets_selected', 'cancelled', 'failed'
                - File path reference for: 'raw', 'detection', and 'target' images
                - Time
    - Detection Workflow moves through these steps:
        1. Inital Scan of scene using User Options for target detection round
            - Saves 'raw-{target_type}-{detection_round.uuid}' images to dedicated 'data/scan_images/' path
            - Produces an datetime stamp is ISO 8601 format to be added to the manifest
        - Intakes scan_image scene, returning annotated detection image path and datetime stamp:
            - Annotation includes: a bound box with {target_type} and confidence (2 significant figures)
            - Saves 'detection-{target_type}-{detection_round.uuid}' images to dedicated 'data/detection_annotation/' path
            - Produces an datetime stamp is ISO 8601 format to be added to the manifest
        - Intakes and detection image scene, returning annotated target image:
            - Annotation includes: a bound box with {target_type} and a target selection status label (selected - not selected)
            - Saves 'target-{target_type}-{detection_round.uuid}' images to dedicated 'data/target_annotation/' path
            - Produces an datetime stamp is ISO 8601 format to be added to the manifest

3. Depth Scanning Service
    - Exposed through the User Interface
    - Stub for now

## IP Requirements
The System shall only use commerical use licensed software.
The system shall not use CopyLeft licensed software.