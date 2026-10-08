# Flask Backend – DuraKnot Fence System

## Overview

The Flask backend is the central software layer of the DuraKnot Fence production monitoring and AI inspection system.

It connects the ESP32, AI inspection system, MySQL database, and web dashboard.


ESP32
  ↓
HTTP / JSON
  ↓
Flask Backend
  ├── MySQL Database
  ├── YOLO11n
  ├── OpenCV Camera
  └── Web Dashboard


  Main Responsibilities
The Flask backend performs the following functions:
- Receives production data from the ESP32.
- Processes HTTP and JSON requests.
- Communicates with the MySQL database.
- Handles the live camera feed.
- Uses OpenCV for camera and image processing.
- Runs the YOLO11n model for defect detection.
- Processes AI detection results.
- Provides data to the web dashboard.
- Handles dashboard commands.
- Sends required length information to the ESP32.
- Handles the dashboard reset request.
  
ESP32 Communication
The ESP32 communicates with Flask using Wi-Fi, HTTP, and JSON.
ESP32 → Flask
The ESP32 sends information such as:
- Pulse count
- Current length in cm
- Hall pulse count
- Hall length
- Production information
  
Flask → ESP32
Flask can send:
- Required length
- Reset command/flag
This provides two-way communication between the ESP32 and the backend.

AI Inspection
The Flask backend connects the camera-processing system with the YOLO11n model.
Camera
   ↓
OpenCV
   ↓
YOLO11n
   ↓
Defect Detection
   ↓
Flask
   ↓
Dashboard / MySQL

The model detects two classes:
- Broken Fence
- Improper Knotting
Confidence Filtering
YOLO provides a confidence score for each detection.
The implemented system uses a 70% confidence threshold for saving qualifying defect detections.
A save cooldown is also used to avoid repeatedly saving the same continuously visible defect.

MySQL Database
Flask communicates with MySQL to store and retrieve relevant system information.
The database can contain:
- Production data
- Sensor readings
- AI detection results
- Defect information
- Defect images
- Historical records
  
Dashboard
Flask provides the backend services required by the web dashboard.
The dashboard can display:
- Required length
- Current length
- Rotary encoder information
- Hall sensor information
- Production status
- Live camera feed
- AI detection results
- Defect images
- Reset control
  
Reset Function
The dashboard reset function communicates through Flask to reset the ESP32 counters.
Dashboard
    ↓
Flask
    ↓
ESP32
    ↓
Reset Counters
    ↓
Length = 0 cm
    ↓
Updated Data
    ↓
Flask
    ↓
Dashboard

Main File
The main Flask application file is:
app.py

It contains the backend routes and logic used to connect the different parts of the project.
Technologies Used
- Python
- Flask
- OpenCV
- Ultralytics YOLO11n
- MySQL
- NumPy
- Pillow
- HTTP
- JSON
- Wi-Fi
  
Requirements
The Python dependencies required by the backend are listed in:
requirements.txt

Install them using:
__pip install -r requirements.txt__

Backend Role in the Complete System

<img width="195" height="242" alt="image" src="https://github.com/user-attachments/assets/eb09b172-3d85-428c-8d9a-8f3872e01d04" />
