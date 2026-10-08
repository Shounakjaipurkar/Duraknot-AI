# DuraKnot AI Dataset

This folder contains information about the dataset used to train the YOLO11n model for automatic DuraKnot fence defect detection.

## Dataset Classes

The model detects two types of fence defects:

1. Broken fence
2. Improper knotting

## Dataset Split

| Dataset | Images |
|---|---:|
| Total | 645 |
| Training | 516 |
| Validation | 129 |

## Dataset Processing

The images were collected and labelled for the required defect classes.

The labelled dataset was then divided into training and validation sets and used for YOLO11n model training.

## Purpose

The dataset is used to train the AI model to identify defects during DuraKnot fence production.

```text
Fence Images
     ↓
Image Labelling
     ↓
Dataset Preparation
     ↓
Training / Validation Split
     ↓
YOLO11n Training
     ↓
Trained Model (best.pt)
     ↓
Real-Time Defect Detection
