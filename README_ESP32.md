# ESP32 – DuraKnot Production Monitoring

## Overview

The ESP32 is the main microcontroller used in the DuraKnot production monitoring system. It collects sensor data, calculates the fence length, controls the servo, displays information on the LCD, and communicates with the Flask backend through Wi-Fi.

## Functions of ESP32

The ESP32 performs the following functions:

- Reads pulses from the rotary encoder.
- Calculates the produced fence length in centimeters.
- Reads pulses from the Hall-effect sensor.
- Calculates additional Hall-based length information.
- Displays the required and current length on the LCD.
- Compares the current length with the required length.
- Triggers the programmed servo action when the required length is reached.
- Connects to Wi-Fi.
- Sends sensor and production data to the Flask server using HTTP and JSON.
- Receives required length and reset information from the Flask server.
- Resets the length counters when the reset command is received.

## Components Connected to ESP32

| Component | Purpose |
|---|---|
| Rotary Encoder | Measures fence movement and length |
| Hall-Effect Sensor | Provides additional roller rotation/length monitoring |
| LCD | Displays production information |
| Servo Motor | Performs the programmed control action |
| ESP32 | Processes sensor data and communicates with the backend |

## Rotary Encoder

The rotary encoder is used as the primary method for measuring the produced fence length.

The project uses:

**600 pulses = 34 cm**

Therefore:

**1 pulse ≈ 0.05667 cm**

The ESP32 counts the encoder pulses and calculates the current fence length.

## Hall-Effect Sensor

The Hall-effect sensor provides additional roller rotation and length monitoring.

Magnets are placed on the rotating roller. When a magnet passes the Hall sensor, a pulse is generated and counted by the ESP32.

## LCD Display

The LCD is used to display information locally at the machine, such as:

- Required Length
- Current Length
- Production Status

## Servo Control

The ESP32 compares the current fence length with the required length.

When the required length is reached, the programmed servo action is triggered.

## Communication

The ESP32 communicates with the Flask backend using:

**Wi-Fi → HTTP → JSON**

### ESP32 to Flask

The ESP32 sends information such as:

- Pulse count
- Current length
- Hall pulse count
- Hall length
- Production information

### Flask to ESP32

Flask can send:

- Required length
- Reset command/flag

This provides two-way communication between the ESP32 and the Flask backend.

## Dashboard Reset

The dashboard reset function works through Flask.

The flow is:

Dashboard → Flask → ESP32 → Reset Counters → Length becomes 0 cm

After resetting, the ESP32 sends the updated values back to the Flask server.

## ESP32 in the Complete System

<img width="190" height="237" alt="image" src="https://github.com/user-attachments/assets/186623c4-b670-410c-926b-636704c8800d" />
