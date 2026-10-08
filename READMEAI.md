# AI Model – DuraKnot Fence Defect Detection

This folder contains the trained YOLO11n model used for automatic fence defect detection in the A-1 DuraKnot production monitoring system.

## Model

- Model: YOLO11n
- Framework: Ultralytics YOLO
- Task: Object Detection
- Classes:
  - Broken fence
  - Improper knotting

## Dataset

The dataset contains images of DuraKnot fence conditions.

- Total Images: 645
- Training Images: 516
- Validation Images: 129

## Detection Process

The camera captures the fence during production.

The image is processed using OpenCV and passed to the YOLO11n model.

The model detects:

1. Broken fence
2. Improper knotting

Detected defects are sent to the Flask backend and stored in the MySQL database.

## Model Files

| File | Description |
|---|---|
| `best.pt` | Trained YOLO11n model |
| `data.yaml` | Dataset configuration |
| `README.md` | Model documentation |

## Confidence

The YOLO model performs inference with a base confidence setting, and detections are accepted for recording when the confidence is at least **70%**.

## Integration

The trained model is loaded by the Flask backend and used for real-time camera-based defect detection.

```text
Camera
   ↓
OpenCV
   ↓
YOLO11n
   ↓
Defect Detection
   ↓
Flask Backend
   ↓
MySQL Database
   ↓
Dashboard
