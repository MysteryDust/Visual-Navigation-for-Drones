# Aerial Optical Navigation & Targeting System

## Overview
This repository contains a full-stack algorithm pipeline designed to solve GNSS-denied optical navigation challenges. Given a video feed and initial barometric/gimbal telemetry from a UAV (DJI Air 3), the system calculates the real-time geographic coordinates of the camera's center-point and maps semantic targets (vehicles/pedestrians) to absolute GNSS space.

## System Architecture

1. **Preprocessing Engine (`telemetry_extractor.py`)**
   - Parses raw `.SRT` flight logs, mitigating UTF-BOM encoding artifacts.
   - Normalizes temporal telemetry data into a structured pandas DataFrame.

2. **Geospatial Raycasting (`raycast_engine.py`)**
   - Calculates dynamic UAV yaw using vector displacement between sequential latitude/longitude points.
   - Implements hover-state stabilization to prevent yaw-spin anomalies.
   - Executes trigonometric raycasting (accounting for the Air 3's -45° gimbal pitch) to project the optical center-point onto a flat-earth approximation model.

3. **Target Acquisition & Sensor Fusion (`optical_targeting_hud.py`)**
   - **Architectural Note:** While theoretical frameworks demand dense semantic segmentation (e.g., SegFormer) for static infrastructure, executing transformer-based models is computationally unviable for real-time edge processing on integrated hardware. 
   - **Solution:** We optimized the vision pipeline by deploying a `YOLOv8-Nano` architecture fine-tuned on the VisDrone dataset. This ensures high-framerate, real-time tracking of dynamic targets while maintaining absolute GNSS coordinate mapping.

4. **Tactical Mapping (`tactical_map_generator.py`)**
   - Fuses the optical classification logs with the raycast coordinates to generate an interactive Folium map, verifying the spatial accuracy of the target path.

## Execution
Ensure `visdrone_yolov8n.pt` and the required video/SRT files are in the root directory, then execute the modules sequentially.
