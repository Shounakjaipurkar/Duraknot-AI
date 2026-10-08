# Database – DuraKnot Fence System

## Overview

MySQL is used as the database management system for the DuraKnot Fence production monitoring and AI inspection system.

The database stores relevant production and inspection information received and processed by the Flask backend.

## Database Role

The database provides a permanent place to store system information instead of keeping it only on the live dashboard.

The basic flow is:

```text
ESP32 ──────┐
            ↓
          Flask
            ↓
          MySQL
            ↑
     AI Detection
