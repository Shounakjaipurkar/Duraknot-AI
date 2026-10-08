# A-1 DuraKnot AI-Based Fence Quality Inspection and Production Monitoring 

WORKING OF THE PROJECT

__1. WITH CURRENT LENGTH AND REQUIRED LENGTH__
<img width="400" height="225" alt="first one" src="https://github.com/user-attachments/assets/b8525a66-4da1-4b6b-abac-5ebfab0db1f2" />

__2. FENCE DEFECT DETECTION__
<img width="880" height="475" alt="image" src="https://github.com/user-attachments/assets/c3c5ff23-2e63-4452-b82f-a95834266a1b" />

__2. FOR MORE VIDEOS FOLLOW THE DRIVE LINK__









Project Overview
The A-1 DuraKnot AI-Based Fence Quality Inspection and Production Monitoring System combines production monitoring and AI-based visual inspection.
The system integrates:
- ESP32
- Rotary encoder
- Hall-effect sensor
- LCD
- Servo
- Camera
- OpenCV
- YOLO11n
- Flask
- MySQL
- Web dashboard
Objectives
1. Measure fence production length in real time.
2. Monitor roller movement using sensors.
3. Compare current length with required length.
4. Perform the programmed control action when the required length is reached.
5. Detect fence defects using AI.
6. Detect Broken Fence and Improper Knotting.
7. Store relevant production and inspection information.
8. Display information on a web dashboard.
9. Provide dashboard controls such as resetting the current length.
    
__System Architecture__

<img width="1199" height="1312" alt="image" src="https://github.com/user-attachments/assets/1216cb79-16d5-46b3-9326-34984536505a" />



   <img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/17b706ad-21a0-4ea6-bf5d-bc15d86823e9" />

__Length Measurement__
The rotary encoder generates pulses as the roller rotates.
The project uses:
600 pulses = 34 cm
Therefore:
CM_PER_PULSE = 34 / 600
             ≈ 0.05667 cm/pulse
Length is handled in centimeters.
The ESP32 compares current length with required length. When the programmed condition is reached, the control action is triggered.

__Hall-Effect Sensor__

Magnets are placed on the rotating roller. When a magnet passes the Hall sensor, a pulse is generated.
Magnet passes
     ↓
Hall sensor detects it
     ↓
Pulse generated
     ↓
ESP32 counts pulse
     ↓
Hall-based measurement

__AI Defect Detection__
The project uses the YOLO11n object detection model.
Classes
Class 0 → Broken Fence
Class 1 → Improper Knotting

AI Pipeline

Camera
   ↓
OpenCV
   ↓
YOLO11n
   ↓
Class + Bounding Box + Confidence
   ↓
Flask
   ↓
Dashboard / MySQL

__OpenCV__
OpenCV is used for the camera and video-processing side of the system.
It is used to:
- Access the camera
- Capture frames
- Process camera frames
- Work with YOLO detection results
- Display detection information
- Provide the processed camera feed to the dashboard
- Save qualifying detection images
OpenCV is the computer-vision library; YOLO11n is the AI object-detection model.
YOLO Confidence
YOLO provides a confidence score for each detection.
For example:
Broken Fence → 87%
The implemented AI pipeline uses a 70% confidence threshold for saving qualifying defect detections. A save cooldown is also used so that a continuously visible defect is not saved on every frame.

__Dataset and Training__
Images were labelled using Label Studio with bounding boxes for the defect classes.
The latest recorded dataset contained:
Total Images      = 645
Training Images   = 516
Validation Images = 129
Dataset classes:
names:
  0: Broken fence
  1: Improper knotting
Model
Model: YOLO11n
Framework: Ultralytics
The trained model weights are normally stored as:
best.pt
Large model and dataset files may be kept outside normal GitHub storage.
Flask Backend
Flask is the Python web framework used as the backend.
It acts as a bridge between the ESP32, AI system, MySQL database and dashboard.
Flask responsibilities
- Receive ESP32 data
- Process HTTP/JSON requests
- Communicate with MySQL
- Handle camera streaming
- Run YOLO inference
- Process AI detections
- Provide dashboard routes
- Handle dashboard controls
- Handle the current-length reset workflow
The main backend file is:
app.py
ESP32 ↔ Flask Communication
The ESP32 communicates with Flask using:
Wi-Fi + HTTP + JSON
ESP32 → Flask
Data can include:
- Pulse count
- Current length
- Hall pulse count
- Hall length
- Production values used by the application
Flask → ESP32
The backend can provide:
- Required length
- Reset command/flag
This provides two-way communication.

__MySQL Database__
MySQL stores relevant production and AI inspection information.
ESP32 Data ──> Flask ──> MySQL
AI Detection ─> Flask ──┘
Web Dashboard
The dashboard is the main user interface.
It can display:
- Required Length
- Current Length
- Rotary encoder information
- Hall sensor information
- Production status
- AI detection results
- Defect information/images
- Live camera feed

__Complete Project Flow__

<img width="1145" height="1374" alt="image" src="https://github.com/user-attachments/assets/34b2ee50-de8e-4661-9950-930d0cae6f22" />


__Technology Stack__

Hardware
- ESP32
- Rotary Encoder
- Hall-Effect Sensor
- Magnets
- LCD
- Servo
- Camera
- Motor
- Chain and pulley
- Rollers
Software
- Arduino IDE / ESP32 development environment
- Python
- Flask
- OpenCV
- Ultralytics YOLO11n
- MySQL
- HTML
- CSS
- JavaScript
- Label Studio
Communication
- Wi-Fi
- HTTP
- JSON
