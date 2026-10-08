# DuraKnot Dashboard

The DuraKnot Dashboard is the web-based monitoring interface of the A-1 Fence production monitoring system.

## Features

- User login
- Live production monitoring
- Required length display
- Current fence length
- Production status
- Rotary encoder readings
- Hall sensor readings
- AI defect detection results
- Broken fence detection
- Improper knotting detection
- Defect image display
- Production history
- Roll details
- Production analytics
- Current-length reset
- PDF report generation

## System Flow

```text
ESP32 ──────────────┐
                    │
Camera → OpenCV → YOLO11n
                    │
                    ↓
                 Flask
                    │
                    ↓
                  MySQL
                    │
                    ↓
                Dashboard
